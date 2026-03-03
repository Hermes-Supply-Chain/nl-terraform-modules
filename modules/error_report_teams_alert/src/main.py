from google.cloud.errorreporting_v1beta1 import ErrorStatsServiceClient
import functions_framework
from error_reporting import ErrorReportClient
from storage_helper import StorageHelper
from teams_alert_helper import TeamsAlertHelper
from config import Config
from flask import Response, Request
from google import genai
import ast
import json
import logging
from nl_digital_platform_lib.gcp_json_logging import nxt_setup_logging
import traceback

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
            new_errors.error_groups, "New errors found in Error Reporting!"
        )

    spiked_errors = current_error_report.get_spiked_errors(
        last_error_report,
        config.error_increase_threshold,
    )
    if spiked_errors.error_groups:
        teams_alert_helper.notify_errors(
            spiked_errors.error_groups,
            f"Found errors with a {config.error_increase_threshold * 100}% increase!",
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
    Your function is to evaluate if a developer needs to IMMEDIATELY look at one or more of these error groups if they are very critical. 
    The structure of the input data is a dictionary with the Error Report group id as the key and the Error Report as the value. 
    Only return the keys that will trigger a notification as a string representation of a Python list or else an empty list. (Will be read with ast.literal_eval)
    This is the data:
    {json.dumps(current_error_report.error_groups)}
    """
    response = genai_client.models.generate_content(model=model, contents=message)
    logger.info("Sent message to Vertex AI: %s", message)

    genai_client.close()
    response_text = response.text or ""
    logger.info("AI response: " + response_text)
    critical_error_group_ids: list[str] = ast.literal_eval(response_text)
    if not critical_error_group_ids:
        return Response("AI has deemed no error as critical", status=200)
    critical_errors = {
        k: current_error_report[k]
        for k in critical_error_group_ids
        if k in current_error_report
    }
    teams_alert_helper.notify_errors(critical_errors, "Critical errors flagged by AI:")
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
