"""Refreshable prompt source - for remote sources that support periodic updates."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.chatbot.prompts.sources.base import PromptSource


class RefreshablePromptSource(PromptSource, ABC):
    """
    Prompt source that can be periodically refreshed (e.g. API, database).

    File-based sources do NOT implement this; they are loaded on access
    and not re-read periodically.
    """

    @property
    @abstractmethod
    def refresh_interval_seconds(self) -> float:
        """How often this source should be refreshed."""
        ...

    @abstractmethod
    def refresh(self) -> None:
        """Re-fetch prompts from the remote store. Called by the scheduler."""
        ...
