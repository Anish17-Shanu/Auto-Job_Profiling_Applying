import requests

from app.config import settings


class ApiClient:
    def __init__(self) -> None:
        self.base_url = settings.api_base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "X-Internal-Api-Key": settings.internal_api_key,
        }

    def claim_run(self):
        response = requests.post(f"{self.base_url}/api/internal/pipeline-runs/claim", headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def complete_run(self, run_id: int, payload: dict):
        response = requests.post(
            f"{self.base_url}/api/internal/pipeline-runs/{run_id}/complete",
            json=payload,
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

