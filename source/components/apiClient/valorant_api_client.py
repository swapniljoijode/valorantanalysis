import requests
from typing import Any, Dict, List, Optional

class ValorantAPIClient:
    BASE_URL = "https://valorant-api.com/v1"

    def __init__(self, rate_limit_delay: float = 1.0):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "ValorantAnalytics/1.0"})
        self.rate_limit_delay = rate_limit_delay

    def _get(self, path: str) -> List[Dict[str, Any]]:
        """
        Core GET method. Takes `/agents`, `/weapons`, etc.
        Returns the JSON['data'] list or raises on error.
        """
        url = f"{self.BASE_URL}{path}"
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        payload = resp.json()

        # basic validation
        if "data" not in payload or not isinstance(payload["data"], list):
            raise ValueError(f"Unexpected response format for {url}")

        return payload["data"]

    # Convenience methods per endpoint
    def get_agents(self) -> List[Dict[str, Any]]:
        return self._get("/agents")

    def get_weapons(self) -> List[Dict[str, Any]]:
        return self._get("/weapons")

    def get_maps(self) -> List[Dict[str, Any]]:
        return self._get("/maps")

    def get_gamemodes(self) -> List[Dict[str, Any]]:
        return self._get("/gamemodes")

    def get_competitive_tiers(self) -> List[Dict[str, Any]]:
        return self._get("/competitivetiers")
    
    def get_gears(self) -> List[Dict[str, Any]]:
        return self._get("/gear")
