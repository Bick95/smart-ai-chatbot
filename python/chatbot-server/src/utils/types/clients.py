from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import httpx

from langchain_core.language_models import BaseChatModel

from src.chatbot.types.llm_models import LLMModelSelection, LLMModelIdMap


@dataclass(frozen=True, slots=True)
class Clients:
    http: Mapping[str, httpx.Client]
    llm_models: Mapping[LLMModelSelection, BaseChatModel]
    llm_model_id_map: LLMModelIdMap

    def __post_init__(self) -> None:
        models_keys = set(self.llm_models.keys())
        ids_keys = set(self.llm_model_id_map.keys())
        if models_keys != ids_keys:
            missing_in_ids = models_keys - ids_keys
            missing_in_models = ids_keys - models_keys
            raise ValueError(
                "Inconsistent LLM registry. "
                f"Missing in llm_model_id_map: {missing_in_ids}. "
                f"Missing in llm_models: {missing_in_models}."
            )
