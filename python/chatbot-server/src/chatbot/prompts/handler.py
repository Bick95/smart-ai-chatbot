"""Prompt handler - fetches prompts from sources with variable substitution."""

from __future__ import annotations

import threading
import time

from src.chatbot.prompts.sources.base import PromptSource
from src.chatbot.prompts.sources.file import FilePromptSource
from src.chatbot.prompts.sources.refreshable import RefreshablePromptSource


class PromptHandler:
    """
    Resolves prompts from configurable sources (file, database, API).

    Sources are queried in order; the first non-None result is returned.

    Optional: start_background_refresh() periodically calls refresh() on
    RefreshablePromptSource instances (e.g. HttpPromptSource). File-based
    sources are never re-read; they use Python's module cache.
    """

    def __init__(self, sources: list[PromptSource] | None = None) -> None:
        self.sources: list[PromptSource] = sources or [FilePromptSource()]
        self._refresh_thread: threading.Thread | None = None
        self._refresh_stop = threading.Event()

    def get(self, prompt_id: str, **variables: str) -> str:
        """
        Retrieve a prompt by ID and optionally substitute variables.

        :param prompt_id: Dot-separated ID (e.g. "nodes.llm_node.system")
        :param variables: Key-value pairs for {variable} substitution
        :return: The resolved prompt string
        :raises: ValueError if prompt not found in any source
        """
        for source in self.sources:
            result = source.get(prompt_id, **variables)
            if result is not None:
                return result
        raise ValueError(f"Prompt not found: {prompt_id}")

    def get_optional(self, prompt_id: str, default: str = "", **variables: str) -> str:
        """Like get(), but returns default instead of raising if not found."""
        for source in self.sources:
            result = source.get(prompt_id, **variables)
            if result is not None:
                return result
        return default

    def _get_refreshable_sources(self) -> list[RefreshablePromptSource]:
        return [s for s in self.sources if isinstance(s, RefreshablePromptSource)]

    def start_background_refresh(
        self,
        interval_seconds: float | None = None,
    ) -> None:
        """
        Start a background thread that periodically refreshes remote prompt sources.

        Only sources implementing RefreshablePromptSource are refreshed.
        File-based sources are never touched.

        :param interval_seconds: Poll interval. If None, uses the minimum
            refresh_interval_seconds across all refreshable sources.
        """
        refreshable = self._get_refreshable_sources()
        if not refreshable:
            return
        if interval_seconds is None:
            interval_seconds = min(s.refresh_interval_seconds for s in refreshable)
        self._refresh_stop.clear()

        def _run() -> None:
            while not self._refresh_stop.wait(timeout=interval_seconds):
                for source in refreshable:
                    try:
                        source.refresh()
                    except Exception:
                        pass  # Log and continue? Handler has no logger

        self._refresh_thread = threading.Thread(target=_run, daemon=True)
        self._refresh_thread.start()

    def stop_background_refresh(self) -> None:
        """Stop the background refresh thread."""
        self._refresh_stop.set()
        if self._refresh_thread is not None:
            self._refresh_thread.join(timeout=5.0)
            self._refresh_thread = None


_default_handler: PromptHandler | None = None


def get_prompt_handler() -> PromptHandler:
    """Return the default prompt handler (singleton)."""
    global _default_handler
    if _default_handler is None:
        _default_handler = PromptHandler()
    return _default_handler


def set_prompt_handler(handler: PromptHandler) -> None:
    """Set the default prompt handler. Use for custom configuration at startup."""
    global _default_handler
    _default_handler = handler
