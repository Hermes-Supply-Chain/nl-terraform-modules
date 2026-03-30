from google.cloud.errorreporting_v1beta1 import ErrorStatsServiceClient
from google.cloud.errorreporting_v1beta1.types import (
    ListEventsRequest,
    ListGroupStatsRequest,
    QueryTimeRange,
)
from google.api_core.datetime_helpers import to_milliseconds
import json
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ErrorGroupData:
    count: int
    message: str
    affected_service: str
    timestamps: list[int]
    ai_reasoning: str = ""


class ErrorReport:
    error_groups: dict[str, ErrorGroupData]

    def __init__(self, error_groups: dict[str, ErrorGroupData]) -> None:
        self.error_groups = error_groups

    def get_new_errors(self, former_report: "ErrorReport") -> "ErrorReport":
        return ErrorReport(
            {
                key: value
                for key, value in self.error_groups.items()
                if key not in former_report.error_groups
            }
        )

    def get_spiked_errors(
        self,
        former_report: "ErrorReport",
        increase_threshold: float,
    ) -> "ErrorReport":
        spiked_errors: dict[str, ErrorGroupData] = {}
        for group_id, current_error_group in self.error_groups.items():
            if group_id not in former_report.error_groups:
                continue

            cached_error_group = former_report.error_groups[group_id]
            cached_errors_count = cached_error_group.count
            current_errors_count = current_error_group.count

            if cached_errors_count == 0:
                continue

            diff = current_errors_count - cached_errors_count

            if diff / cached_errors_count >= increase_threshold:
                spiked_errors[group_id] = current_error_group

        return ErrorReport(spiked_errors)

    def get_errors_as_string(self) -> str:
        serializable = {key: asdict(value) for key, value in self.error_groups.items()}
        return json.dumps(serializable)

    def serialize_error_report(self) -> bytes:
        return self.get_errors_as_string().encode("utf-8")

    @staticmethod
    def deserialize_error_report(data: bytes) -> "ErrorReport":
        decoded: dict[str, dict[str, Any]] = json.loads(data)
        return ErrorReport(
            {key: ErrorGroupData(**value) for key, value in decoded.items()}
        )


class ErrorReportClient:
    def __init__(self, project_id: str, client: ErrorStatsServiceClient):
        self.project_id = project_id
        self.client = client

    def request_error_report(self, period: int) -> ErrorReport:
        time_range = QueryTimeRange(period=period)
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
                count=error_report.count,
                affected_service=error_report.representative.service_context.service,
                timestamps=error_time_stamps,
            )
        return ErrorReport(error_report_groups)
