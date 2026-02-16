"""HTTP/API prompt source - fetches from a remote URL, supports periodic refresh."""

from __future__ import annotations

import threading
from typing import Any

import httpx

from src.chatbot.prompts.sources.refreshable import RefreshablePromptSource
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HttpPromptSource(RefreshablePromptSource):
    """
    Fetch prompts from an HTTP API. Caches in memory and refreshes periodically.

    Expects GET {base_url} to return JSON: {"prompt_id": "template", ...}
    e.g. {"nodes.llm_node.system": "You are a helpful assistant..."}
    """

    def __init__(
        self,
        base_url: str,
        refresh_interval_seconds: float = 300,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._refresh_interval_seconds = refresh_interval_seconds
        self._headers = headers or {}
        self._timeout = timeout
        self._cache: dict[str, str] = {}
        self._lock = threading.Lock()
        self.refresh()  # Prime cache on init

    @property
    def refresh_interval_seconds(self) -> float:
        return self._refresh_interval_seconds

    def refresh(self) -> None:
        """
        Re-fetch all prompts from the API.

        On success: updates the in-memory cache.
        On failure: leaves the cache unchanged (keeps last successful fetch).
        Only when the cache is empty does get() return None and allow
        FilePromptSource to serve as fallback.
        """
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(self._base_url, headers=self._headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            logger.exception(
                "Failed to fetch prompts from %s; keeping existing cache",
                self._base_url,
            )
            return  # Keep existing cache on failure; never clear it
        if isinstance(data, dict):
            new_cache = {k: str(v) for k, v in data.items() if isinstance(v, str)}
            with self._lock:
                old_keys = set(self._cache.keys())
                new_keys = set(new_cache.keys())
                if old_keys and old_keys != new_keys:
                    added = new_keys - old_keys
                    removed = old_keys - new_keys
                    logger.warning(
                        "Prompt key mismatch after refresh from %s: "
                        "added=%s, removed=%s",
                        self._base_url,
                        sorted(added) if added else None,
                        sorted(removed) if removed else None,
                    )
                self._cache = new_cache

    def get(self, prompt_id: str, **variables: Any) -> str | None:
        template = self._cache.get(prompt_id)
        if template is None:
            return None
        if variables:
            try:
                return template.format(**variables)
            except KeyError as e:
                logger.warning(
                    "Missing variable %s for prompt %s; returning unformatted template",
                    e,
                    prompt_id,
                )
                return template
        return template
