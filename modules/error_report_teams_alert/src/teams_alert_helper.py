import requests
from error_reporting import ErrorGroupData


class TeamsAlertHelper:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    @staticmethod
    def _create_teams_alert_body(
        errors: dict[str, ErrorGroupData],
        title: str,
        project: str,
    ) -> dict[str, object]:
        error_blocks = []
        for error in errors.values():
            facts = [
                {
                    "title": "Service",
                    "value": f"{error.affected_service} (reported {error.count} times)",
                },
                {"title": "Message", "value": f"{error.message[:100]}..."},
            ]
            if error.ai_reasoning:
                facts.append({"title": "AI response", "value": error.ai_reasoning})

            error_blocks.append({"type": "FactSet", "separator": True, "facts": facts})

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
                                "type": "TextBlock",
                                "text": f"Project: {project}",
                                "size": "Medium",
                                "weight": "Bolder",
                                "separator": True,
                            },
                            *error_blocks,
                        ],
                    },
                }
            ],
        }

    def notify_errors(
        self,
        errors: dict[str, ErrorGroupData],
        title: str,
        project: str,
    ) -> None:
        teams_request_headers = {"Content-Type": "application/json"}
        teams_request_body = self._create_teams_alert_body(errors, title, project)
        requests.post(
            self.webhook_url, headers=teams_request_headers, json=teams_request_body
        )
