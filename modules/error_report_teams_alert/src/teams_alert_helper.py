import requests
from error_reporting import ErrorGroupData


class TeamsAlertHelper:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    @staticmethod
    def create_teams_alert_body(
        errors: dict[str, ErrorGroupData],
        title: str,
    ) -> dict[str, object]:
        errors_teams_body = []
        for error in errors.values():
            errors_teams_body.append({"title": "Message", "value": error.message[:100]})
            errors_teams_body.append(
                {"title": "Service", "value": error.affected_service}
            )
            errors_teams_body.append({"title": "Amount", "value": str(error.count)})
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.5",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Large",
                                "weight": "Bolder",
                                "text": title,
                                "wrap": True,
                            },
                            {
                                "type": "FactSet",
                                "facts": errors_teams_body,
                            },
                        ],
                    },
                }
            ],
        }

    def notify_errors(self, errors: dict[str, ErrorGroupData], title: str) -> None:
        teams_request_headers = {"Content-Type": "application/json"}
        teams_request_body = self.create_teams_alert_body(errors, title)
        requests.post(
            self.webhook_url, headers=teams_request_headers, json=teams_request_body
        )
