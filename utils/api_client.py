"""
CorrespondenceApiClient — authenticated HTTP client for test data operations.

Loads cookies from a Playwright storage-state file so API calls are
authenticated without a separate browser login.  Intended for test fixtures
that need to seed, read, or clean up application data via the backend API
rather than driving the UI for every setup step.

Usage in conftest.py:
    @pytest.fixture(scope="session")
    def api_client(auth_state):
        return CorrespondenceApiClient(Config.BASE_URL, storage_state_path=auth_state)

Usage in a test:
    def test_something(api_client):
        summary = api_client.get_status_summary()
        assert summary["draft"] >= 0
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

from config.config import Config
from utils.logger import get_logger


log = get_logger(__name__)


class ApiError(Exception):
    """Raised when an API call returns a non-2xx status."""
    def __init__(self, method: str, url: str, status: int, body: str):
        super().__init__(f"{method} {url} → HTTP {status}: {body[:200]}")
        self.status = status


class CorrespondenceApiClient:
    """Thin HTTP wrapper around the Correspondence backend API.

    All requests share a single requests.Session loaded with the auth cookies
    captured by Playwright during the login fixture.
    """

    def __init__(
        self,
        base_url: str,
        storage_state_path: Optional[Path] = None,
        timeout: int = 30,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        if storage_state_path:
            self._load_storage_state(storage_state_path)

    # ------------------------------------------------------------------ Setup
    def _load_storage_state(self, path: Path) -> None:
        """Populate the requests session with cookies from a Playwright storage state."""
        if not path.exists():
            log.warning(f"Storage state not found at {path} — API client will be unauthenticated.")
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for cookie in data.get("cookies", []):
                self._session.cookies.set(
                    name=cookie["name"],
                    value=cookie["value"],
                    domain=cookie.get("domain"),
                    path=cookie.get("path", "/"),
                )
            log.info(f"Loaded {len(data.get('cookies', []))} cookies from {path.name}")
        except Exception as exc:  # noqa: BLE001
            log.warning(f"Failed to load storage state: {exc}")

    # ---------------------------------------------------------------- HTTP
    def _url(self, path: str) -> str:
        return f"{self._base}/{path.lstrip('/')}"

    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        url = self._url(path)
        log.debug(f"GET {url} params={params}")
        resp = self._session.get(url, params=params, timeout=self._timeout)
        if not resp.ok:
            raise ApiError("GET", url, resp.status_code, resp.text)
        return resp.json()

    def _post(self, path: str, json_body: Any = None) -> Any:
        url = self._url(path)
        log.debug(f"POST {url}")
        resp = self._session.post(url, json=json_body, timeout=self._timeout)
        if not resp.ok:
            raise ApiError("POST", url, resp.status_code, resp.text)
        return resp.json()

    # --------------------------------------------------- Letter Type Versions
    def get_letter_type_versions(
        self, status: str = "", page: int = 0, size: int = 50
    ) -> Dict:
        """GET /cac/letter-type-version — returns totalRecords + statusSummary."""
        params: Dict = {"page": page, "size": size}
        if status:
            params["status"] = status
        return self._get("/cac/letter-type-version", params=params)

    def get_status_summary(self) -> Dict[str, int]:
        """Return the statusSummary dict from the letter-type-version API."""
        data = self.get_letter_type_versions()
        return data.get("statusSummary", {})

    def get_total_records(self, status: str = "") -> int:
        """Return the totalRecords count, optionally filtered by status."""
        data = self.get_letter_type_versions(status=status)
        return int(data.get("totalRecords", 0))

    def get_letter_types(self, page: int = 0, size: int = 50) -> List[Dict]:
        """Return the list of letter type records."""
        data = self._get("/cac/letter-type", params={"page": page, "size": size})
        return data.get("content", data) if isinstance(data, dict) else data

    # --------------------------------------------------------- Health / Auth
    def is_authenticated(self) -> bool:
        """Quick check — returns True if the session cookies grant API access."""
        try:
            self.get_letter_type_versions(size=1)
            return True
        except ApiError as exc:
            if exc.status in (401, 403):
                return False
            raise
        except Exception:  # noqa: BLE001
            return False
