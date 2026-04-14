import os


# class Config:
#     project_id: str
#     region: str
#     teams_webhook_url: str
#     request_period: int
#     response_codes_to_filter: list[int]
#     ai_model_id: str

#     def __init__(self) -> None:
#         try:
#             self.project_id = os.environ["PROJECT_ID"]
#             self.region = os.environ["REGION"]
#             self.teams_webhook_url = os.environ["TEAMS_WEBHOOK_URL"]
#             self.request_period = int(os.environ["REQUEST_PERIOD"])
#             self.response_codes_to_filter = [
#                 int(code) for code in os.environ["RESPONSE_CODES_TO_FILTER"].split(",")
#             ]
#             self.ai_model_id = os.environ["AI_MODEL_ID"]
#         except KeyError as e:
#             raise RuntimeError(f"Missing environment variable: {e.args[0]}") from e


class Config:
    project_id: str
    region: str
    teams_webhook_url: str
    request_period: int
    response_codes_to_filter: list[int]
    ai_model_id: str

    def __init__(
        self,
        project_id: str,
        region: str,
        teams_webhook_url: str,
        request_period: int,
        response_codes_to_filter: list[int],
        ai_model_id: str,
    ) -> None:
        self.project_id = project_id
        self.region = region
        self.teams_webhook_url = teams_webhook_url
        self.request_period = request_period
        self.response_codes_to_filter = response_codes_to_filter
        self.ai_model_id = ai_model_id

    @classmethod
    def load_from_env(cls) -> "Config":
        try:
            return cls(
                project_id=os.environ["PROJECT_ID"],
                region=os.environ["REGION"],
                teams_webhook_url=os.environ["TEAMS_WEBHOOK_URL"],
                request_period=int(os.environ["REQUEST_PERIOD"]),
                response_codes_to_filter=[
                    int(code)
                    for code in os.environ["RESPONSE_CODES_TO_FILTER"].split(",")
                ],
                ai_model_id=os.environ["AI_MODEL_ID"],
            )
        except KeyError as e:
            raise RuntimeError(f"Missing environment variable: {e.args[0]}") from e
