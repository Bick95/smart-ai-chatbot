"""Base abstraction for prompt sources."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PromptSource(ABC):
    """Abstract base for prompt sources (file, database, API)."""

    @abstractmethod
    def get(self, prompt_id: str, **variables: str) -> str | None:
        """
        Retrieve a prompt by ID, optionally substituting variables.

        :param prompt_id: Dot-separated ID (e.g. "nodes.llm_node.system")
        :param variables: Key-value pairs for template substitution
        :return: The prompt string, or None if not found in this source
        """
        ...
