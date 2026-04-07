import pytest
import requests
from src.error_reporting import ErrorReport, ErrorGroupData
from src.teams_alert_helper import TeamsAlertHelper
from typing import Any


@pytest.fixture
def error_report() -> ErrorReport:
    return ErrorReport(
        {
            "group-1": ErrorGroupData(
                message="DatabaseError was found!",
                affected_services=[
                    "eta-bot-container-milestone-generator",
                    "eta-bot-shipment-milestone-generator",
                ],
                timestamps=[12345, 45678],
                ai_response="AI Response",
            ),
        }
    )


def test_teams_alert(monkeypatch, error_report):
    # given: setup mock
    captured: dict[str, Any] = {}

    def mock_post(url, headers, json):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json

    monkeypatch.setattr(requests, "post", mock_post)

    # given: create client
    teams_alert_helper = TeamsAlertHelper(webhook_url="https://some-teams.url/")

    # when
    teams_alert_helper.notify_errors(
        errors=error_report.error_groups, project="event-service"
    )

    # then
    assert captured["url"] == "https://some-teams.url/"
    assert captured["headers"] == {"Content-Type": "application/json"}
    assert captured["json"] == {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.5",
                    "msteams": {"width": "Full"},
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Large",
                            "weight": "Bolder",
                            "text": "Error spikes found by AI!",
                            "wrap": True,
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Project: event-service",
                            "size": "Medium",
                            "isSubtle": True,
                        },
                        {
                            "type": "Container",
                            "separator": True,
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "AI Response",
                                    "wrap": True,
                                    "style": "heading",
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "Service(s): eta-bot-container-milestone-generator, eta-bot-shipment-milestone-generator",
                                    "size": "Medium",
                                    "isSubtle": True,
                                },
                                {
                                    "type": "Container",
                                    "id": f"details_group-1",
                                    "isVisible": False,
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": "DatabaseError was found!",
                                            "wrap": True,
                                        },
                                    ],
                                },
                                {
                                    "type": "ActionSet",
                                    "actions": [
                                        {
                                            "type": "Action.ToggleVisibility",
                                            "title": "Show Message",
                                            "targetElements": [f"details_group-1"],
                                        },
                                        {
                                            "type": "Action.OpenUrl",
                                            "title": "Open in Google Cloud Console",
                                            "url": f"https://console.cloud.google.com/errors/group-1;time=P1D?project=event-service",
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            },
        ],
    }
