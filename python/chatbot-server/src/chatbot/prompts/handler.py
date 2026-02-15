"""Prompt handler - fetches prompts from sources with variable substitution."""

from __future__ import annotations

from src.chatbot.prompts.sources.base import PromptSource
from src.chatbot.prompts.sources.file import FilePromptSource


class PromptHandler:
    """
    Resolves prompts from configurable sources (file, database, API).

    Sources are queried in order; the first non-None result is returned.
    """

    def __init__(self, sources: list[PromptSource] | None = None) -> None:
        self.sources: list[PromptSource] = sources or [FilePromptSource()]

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


_default_handler: PromptHandler | None = None


def get_prompt_handler() -> PromptHandler:
    """Return the default prompt handler (singleton)."""
    global _default_handler
    if _default_handler is None:
        _default_handler = PromptHandler()
    return _default_handler
