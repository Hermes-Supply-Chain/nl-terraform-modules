import os


class Config:
    project_id: str
    region: str
    error_increase_threshold: float
    cache_bucket: str
    teams_webhook_url: str
    request_period: int
    use_ai: bool

    def __init__(self) -> None:
        try:
            self.project_id = os.environ["PROJECT_ID"]
            self.region = os.environ["REGION"]
            self.error_increase_threshold = float(
                os.environ["ERROR_INCREASE_THRESHOLD"]
            )
            self.cache_bucket = os.environ["CACHE_BUCKET"]
            self.teams_webhook_url = os.environ["TEAMS_WEBHOOK_URL"]
            self.request_period = int(os.environ["REQUEST_PERIOD"])
            self.use_ai = os.getenv("USE_AI", default="false").lower() == "true"
        except KeyError as e:
            raise RuntimeError(f"Missing environment variable: {e.args[0]}") from e
