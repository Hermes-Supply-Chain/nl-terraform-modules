import requests
from error_reporting import ErrorGroupData


# see: https://adaptivecards.microsoft.com/designer
class TeamsAlertHelper:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    @staticmethod
    def _create_teams_alert_body(
        errors: dict[str, ErrorGroupData],
        project: str,
    ) -> dict[str, object]:
        error_blocks = []
        for group_id, error in errors.items():
            error_blocks.append(
                {
                    "type": "Container",
                    "separator": True,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": error.ai_response,
                            "wrap": True,
                            "style": "heading",
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Service(s): {", ".join(error.affected_services)}",
                            "size": "Medium",
                            "isSubtle": True,
                        },
                        {
                            "type": "Container",
                            "id": f"details_{group_id}",
                            "isVisible": False,
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": f"{error.message[:1000]}",
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
                                    "targetElements": [f"details_{group_id}"],
                                },
                                {
                                    "type": "Action.OpenUrl",
                                    "title": "Open in Google Cloud Console",
                                    "url": f"https://console.cloud.google.com/errors/{group_id};time=P1D?project={project}",
                                },
                            ],
                        },
                    ],
                },
            )

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
                                "text": f"Project: {project}",
                                "size": "Medium",
                                "isSubtle": True,
                            },
                            *error_blocks,
                        ],
                    },
                },
            ],
        }

    def notify_errors(
        self,
        errors: dict[str, ErrorGroupData],
        project: str,
    ) -> None:
        teams_request_headers = {"Content-Type": "application/json"}
        teams_request_body = self._create_teams_alert_body(errors, project)
        requests.post(
            url=self.webhook_url, headers=teams_request_headers, json=teams_request_body
        )
