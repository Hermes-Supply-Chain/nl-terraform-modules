from google.cloud.errorreporting_v1beta1 import ErrorStatsServiceClient
from google.cloud.errorreporting_v1beta1.types import (
    ListEventsRequest,
    ListGroupStatsRequest,
    QueryTimeRange,
)
from google.api_core.datetime_helpers import to_milliseconds
import json
from dataclasses import dataclass, asdict


@dataclass
class ErrorGroupData:
    message: str
    affected_services: list[str]
    timestamps: list[int]
    ai_response: str = ""


class ErrorReport:
    error_groups: dict[str, ErrorGroupData]

    def __init__(self, error_groups: dict[str, ErrorGroupData]) -> None:
        self.error_groups = error_groups

    def get_errors_as_string(self) -> str:
        serializable = {key: asdict(value) for key, value in self.error_groups.items()}
        return json.dumps(serializable)


class ErrorReportClient:
    def __init__(self, project_id: str, client: ErrorStatsServiceClient):
        self.project_id = project_id
        self.client = client

    def request_error_report(self, time_range: QueryTimeRange) -> ErrorReport:
        page_size = 1000
        error_report_request = ListGroupStatsRequest(
            project_name=f"projects/{self.project_id}",
            time_range=time_range,
            page_size=page_size,
        )
        error_report_pager = self.client.list_group_stats(request=error_report_request)
        error_report_groups: dict[str, ErrorGroupData] = {}
        for error_report in error_report_pager:
            error_group_events_request = ListEventsRequest(
                project_name=f"projects/{self.project_id}",
                group_id=error_report.group.group_id,
                time_range=time_range,
                page_size=page_size,
            )
            error_events_pager = self.client.list_events(
                request=error_group_events_request
            )
            error_time_stamps: list[int] = []
            for error_event in error_events_pager:
                error_time_stamps.append(to_milliseconds(error_event.event_time))

            error_report_groups[error_report.group.group_id] = ErrorGroupData(
                message=error_report.representative.message,
                affected_services=[service.service for service in error_report.affected_services],
                timestamps=error_time_stamps,
            )
        return ErrorReport(error_report_groups)
