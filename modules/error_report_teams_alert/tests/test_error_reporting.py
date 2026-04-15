import pytest
from src.error_reporting import ErrorReport, ErrorReportClient
from google.cloud.errorreporting_v1beta1 import (
    ErrorStatsServiceClient,
    QueryTimeRange,
    ErrorGroupStats,
    ErrorEvent,
    ServiceContext,
    ErrorGroup,
    ListGroupStatsRequest,
    ListEventsRequest,
    ErrorContext,
    HttpRequestContext,
)
from google.cloud.errorreporting_v1beta1.types import ErrorEvent
from datetime import datetime, timezone
from typing import Any


def test_request_error(monkeypatch):
    # given: setup mocks
    captured: dict[str, list[Any]] = {"list_group_stats": [], "list_events": []}

    def mock_list_group_stats(self, request):
        captured["list_group_stats"].append(request)
        mock_group_1 = ErrorGroupStats(
            group=ErrorGroup(group_id="group-1"),
            representative=ErrorEvent(
                message="The request was aborted because there was no available instance."
            ),
            affected_services=[
                ServiceContext(service="eta-bot-container-milestone-generator"),
                ServiceContext(service="eta-bot-shipment-milestone-generator"),
            ],
        )
        mock_group_2 = ErrorGroupStats(
            group=ErrorGroup(group_id="group-2"),
            representative=ErrorEvent(message="DatabaseError"),
            affected_services=[ServiceContext(service="portbase-cargo-events-api")],
        )
        return [mock_group_1, mock_group_2]

    def mock_list_events(self, request):
        captured["list_events"].append(request)
        mock_event_1 = ErrorEvent(
            event_time=datetime(2026, 4, 2, 11, 0, 0, tzinfo=timezone.utc)
        )
        mock_event_2 = ErrorEvent(
            event_time=datetime(2026, 4, 2, 12, 0, 0, tzinfo=timezone.utc)
        )
        return [mock_event_1, mock_event_2]

    monkeypatch.setattr(
        ErrorStatsServiceClient, "list_group_stats", mock_list_group_stats
    )
    monkeypatch.setattr(ErrorStatsServiceClient, "list_events", mock_list_events)

    # given: create client
    error_stats_service_client = ErrorStatsServiceClient()
    error_report_client = ErrorReportClient(
        project_id="event-service",
        client=error_stats_service_client,
    )

    # when
    result = error_report_client.request_error_report(QueryTimeRange(period=3))

    # then: assert result
    assert isinstance(result, ErrorReport)
    assert len(result.error_groups) == 2

    group_data = result.error_groups["group-1"]
    assert (
        group_data.message
        == "The request was aborted because there was no available instance."
    )
    assert group_data.affected_services == [
        "eta-bot-container-milestone-generator",
        "eta-bot-shipment-milestone-generator",
    ]
    assert group_data.timestamps == [1775127600000, 1775131200000]

    # then: verify requests
    list_group_stats_requests = captured["list_group_stats"]
    assert len(list_group_stats_requests) == 1
    list_group_stats_request = list_group_stats_requests[0]
    assert isinstance(list_group_stats_request, ListGroupStatsRequest)
    assert list_group_stats_request.project_name == "projects/event-service"
    assert list_group_stats_request.time_range.period == 3
    assert list_group_stats_request.page_size == 1000

    list_events_requests = captured["list_events"]
    assert len(list_events_requests) == 2
    list_events_request_1 = list_events_requests[0]
    assert isinstance(list_events_request_1, ListEventsRequest)
    assert list_events_request_1.project_name == "projects/event-service"
    assert list_events_request_1.group_id == "group-1"
    assert list_events_request_1.time_range.period == 3
    assert list_events_request_1.page_size == 1000

    list_events_request_2 = list_events_requests[1]
    assert isinstance(list_events_request_2, ListEventsRequest)
    assert list_events_request_2.group_id == "group-2"


def test_response_code_filter(monkeypatch):
    # given
    def mock_list_group_stats(self, request):
        mock_group_1 = ErrorGroupStats(
            group=ErrorGroup(group_id="group-1"),
            representative=ErrorEvent(
                message="The request was aborted because there was no available instance.",
                context=ErrorContext(
                    http_request=HttpRequestContext(
                        response_status_code=429,  # this is the response code that should be filtered
                    )
                ),
            ),
            affected_services=[
                ServiceContext(service="eta-bot-container-milestone-generator"),
            ],
        )
        return [mock_group_1]

    monkeypatch.setattr(
        ErrorStatsServiceClient, "list_group_stats", mock_list_group_stats
    )

    # given: create client
    error_stats_service_client = ErrorStatsServiceClient()
    error_report_client = ErrorReportClient(
        project_id="event-service",
        client=error_stats_service_client,
    )

    # when
    result = error_report_client.request_error_report(
        time_range=QueryTimeRange(period=3),
        response_codes_to_filter=[429],
    )

    # then
    assert isinstance(result, ErrorReport)
    assert len(result.error_groups) == 0
