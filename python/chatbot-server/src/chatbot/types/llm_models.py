from __future__ import annotations

from enum import Enum
from typing import Literal, Mapping

from langchain_core.language_models import BaseChatModel


class LLMModelSelection(str, Enum):
    STANDARD = "llm_standard"
    SMALL = "llm_small"


LLMProviderModelId = Literal["gpt-5.2-2025-12-11", "gpt-4o-mini"]

LLMModelIdMap = Mapping[LLMModelSelection, LLMProviderModelId]

LLM_SELECTION_TO_MODEL_ID: LLMModelIdMap = {
    LLMModelSelection.STANDARD: "gpt-5.2-2025-12-11",
    LLMModelSelection.SMALL: "gpt-4o-mini",
}
