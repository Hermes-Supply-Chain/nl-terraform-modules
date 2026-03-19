from google.cloud.errorreporting_v1beta1 import ErrorStatsServiceClient
import functions_framework
from error_reporting import ErrorReportClient
from storage_helper import StorageHelper
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


def main_classic(config: Config) -> Response:
    logger.info("main_classic() called...")
    error_report_client = ErrorReportClient(
        config.project_id, ErrorStatsServiceClient()
    )
    storage_helper = StorageHelper(config.cache_bucket)
    teams_alert_helper = TeamsAlertHelper(config.teams_webhook_url)
    logger.info("Helpers initialized...")

    current_error_report = error_report_client.request_error_report(
        config.request_period
    )
    logger.info(f"Fetched error report with {len(current_error_report)} groups...")

    last_error_report_bytes = storage_helper.get_last_cache_file_as_bytes()
    storage_helper.save_bytes_to_cache(current_error_report.serialize_error_report())

    if last_error_report_bytes is None:
        return Response("No cached report found, sending no alert", status=200)

    last_error_report = ErrorReportClient.deserialize_error_report(
        last_error_report_bytes
    )
    new_errors = current_error_report.get_new_errors(last_error_report)
    if new_errors.error_groups:
        teams_alert_helper.notify_errors(
            new_errors.error_groups, 
            "New errors found in Error Reporting!", 
            config.project_id,
        )

    spiked_errors = current_error_report.get_spiked_errors(
        last_error_report,
        config.error_increase_threshold,
    )
    if spiked_errors.error_groups:
        teams_alert_helper.notify_errors(
            spiked_errors.error_groups,
            f"Found errors with a {config.error_increase_threshold * 100}% increase!",
            config.project_id,
        )

    return Response(status=200)


def main_ai(config: Config) -> Response:
    logger.info("main_ai() called...")
    error_report_client = ErrorReportClient(
        config.project_id, ErrorStatsServiceClient()
    )
    teams_alert_helper = TeamsAlertHelper(config.teams_webhook_url)
    logger.info("Helpers initialized...")

    current_error_report = error_report_client.request_error_report(
        config.request_period
    )

    genai_client = genai.Client(
        vertexai=True, project=config.project_id, location=config.region
    )
    logger.info("GenAI client initialized...")

    # see: https://raw.githubusercontent.com/googleapis/python-genai/refs/heads/main/codegen_instructions.md
    model = "gemini-2.5-flash"
    message = f"""
    You are looking at a Google Cloud projects Error Reporting page grouped into error groups. 
    Your function is to evaluate if a developer needs to IMMEDIATELY look at one or more of these error groups if they are critical. 
    The structure of the input data is a dictionary with the Error Report group id as the key and the Error Report as the value.
    Return a dict[str, str] with the Error Report group id as the key of the error you deem critical and the value your reasoning why it is critical or possible fix, in less than 300 chars.
    If no errors are critical, then return an empty dict. Your response will be read by json.loads()!
    Do not include any text before or after the JSON. 
    Do not use markdown code blocks.
    Example: {{"key": "value"}}
    This is the data:
    {current_error_report.get_errors_as_string()}
    """
    response = genai_client.models.generate_content(model=model, contents=message)
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

    # filter current error groups dict, and append AI reasoning to display in Teams
    critical_errors = {
        key: replace(current_error_report.error_groups[key], ai_reasoning=value)
        for key, value in ai_critical_errors.items()
        if key in current_error_report.error_groups
    }
    teams_alert_helper.notify_errors(
        critical_errors,
        "Critical errors flagged by AI!",
        config.project_id,
    )
    return Response(status=200)


@functions_framework.http
def main(_request: Request) -> Response:
    try:
        config = Config()
        return main_ai(config) if config.use_ai else main_classic(config)
    except Exception as e:
        logger.error("Exception: %s", e)
        logger.exception(traceback.format_exc())
        return Response("Internal Server Error", status=500)
