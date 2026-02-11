from __future__ import annotations

from enum import Enum
from typing import Mapping, Literal

from langchain_core.language_models import BaseChatModel

# LLM Models & their IDs
class LLMModelSelection(str, Enum):
    STANDARD = "llm_standard"

LLMProviderModelId = Literal["gpt-5.2-2025-12-11"]

LLMModelIdMap = Mapping[LLMModelSelection, LLMProviderModelId]

LLM_MODEL_TO_PROVIDER: LLMModelIdMap = {
    LLMModelSelection.STANDARD: "gpt-5.2-2025-12-11",
}
