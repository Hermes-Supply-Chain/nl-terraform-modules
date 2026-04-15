from google.cloud.errorreporting_v1beta1 import ErrorStatsServiceClient, QueryTimeRange
import functions_framework
from error_reporting import ErrorReportClient
from teams_alert_helper import TeamsAlertHelper
from config import Config
from flask import Response, Request
from google import genai
import json
import logging
from nl_digital_platform_lib.gcp_json_logging import nxt_setup_logging
import traceback
from dataclasses import replace

nxt_setup_logging()
logging.getLogger(__package__).setLevel("INFO")
logger = logging.getLogger(__name__)


def find_and_report_errors(config: Config) -> Response:
    error_report_client = ErrorReportClient(
        config.project_id, ErrorStatsServiceClient()
    )
    teams_alert_helper = TeamsAlertHelper(config.teams_webhook_url)
    logger.info("Helpers initialized...")

    time_range = QueryTimeRange(period=config.request_period)
    current_error_report = error_report_client.request_error_report(
        time_range, config.response_codes_to_filter
    )
    logger.info(
        f"Fetched error report with {len(current_error_report.error_groups)} groups..."
    )

    genai_client = genai.Client(
        vertexai=True, project=config.project_id, location=config.region
    )
    logger.info("GenAI client initialized...")

    # see: https://raw.githubusercontent.com/googleapis/python-genai/refs/heads/main/codegen_instructions.md
    message = f"""
You are looking at a Google Cloud projects Error Reporting page grouped into error groups.
The structure of the input data is a dictionary with the Error Report group id as the key and the Error Report as the value.
Your function is to evaluate if any of the provided error groups have spiked or are currently spiking in error count.
You do that by looking at the provided timestamps to see if there are spikes in occurence.
For context, the time window of events sent below is '{time_range.period.name}'. If there is a constant flow of events (during the entire time window!), they may be ignored.
But if a constant stream of errors starts somewhere inside the window, it is a spike aswell!
Return a dict[str, str] with the Error Report group id as the key of the error you deem critical and set the value to a concise title stating the core error 
and the change of amount from baseline to spike, like in these examples:
'DatabaseError: 0/h -> 300/h'
'Invalid HTTP_HOST header: 10/min -> 100/min'
If no errors are critical, then return an empty dict. Your response will be read by json.loads().
Do NOT include any text before or after the JSON!
Do NOT use markdown code blocks! (like ``` or ```json)
The response MUST start with '{{' and end with '}}'!
This is the data:
{current_error_report.get_errors_as_string()}
    """
    response = genai_client.models.generate_content(
        model=config.ai_model_id, contents=message
    )
    logger.info("Sent message to Vertex AI: %s", message)

    genai_client.close()
    response_text = response.text or ""
    logger.info("AI response: " + response_text)

    try:
        # AI is instructed to return the error group id as the key, and its reasoning as the value
        ai_critical_errors: dict[str, str] = json.loads(response_text)
    except ValueError:
        return Response("AI output could not be read as JSON", status=500)

    if not ai_critical_errors:
        return Response("AI has deemed no error as critical", status=200)

    # filter current error groups dict, and append AI response to display in Teams
    critical_errors = {
        key: replace(current_error_report.error_groups[key], ai_response=value)
        for key, value in ai_critical_errors.items()
        if key in current_error_report.error_groups
    }
    teams_alert_helper.notify_errors(critical_errors, config.project_id)
    logger.info("Done!")
    return Response(status=200)


@functions_framework.http
def main(_request: Request) -> Response:
    try:
        config = Config.load_from_env()
        response = find_and_report_errors(config)
        return response
    except Exception as e:
        logger.error("Exception: %s", e)
        logger.exception(traceback.format_exc())
        return Response("Internal Server Error", status=500)
