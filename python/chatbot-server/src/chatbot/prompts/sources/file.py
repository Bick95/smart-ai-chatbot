"""File-based prompt source (default collection)."""

from __future__ import annotations

import importlib
from typing import Any

from src.chatbot.prompts.sources.base import PromptSource


class FilePromptSource(PromptSource):
    """
    Load prompts from the collection package.

    Prompt IDs use dot notation: "category.module.key"
    Maps to: prompts/collection/category/module.py, attribute "key"
    """

    _COLLECTION_BASE = "src.chatbot.prompts.collection"

    def get(self, prompt_id: str, **variables: Any) -> str | None:
        parts = prompt_id.split(".")
        if len(parts) < 3:
            return None
        category, module_name, attr = parts[0], parts[1], parts[2]
        module_path = f"{self._COLLECTION_BASE}.{category}.{module_name}"
        try:
            mod = importlib.import_module(module_path)
        except ModuleNotFoundError:
            return None
        template = getattr(mod, attr, None)
        if template is None or not isinstance(template, str):
            return None
        if variables:
            try:
                return template.format(**variables)
            except KeyError:
                return template
        return template
