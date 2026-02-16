from __future__ import annotations

from src.chatbot.model import get_model
from src.chatbot.types.llm_models import LLM_SELECTION_TO_MODEL_ID, LLMModelSelection
from src.settings import settings
from src.utils.types.clients import Clients


def create_clients() -> Clients:
    llm_models = {
        selection: get_model(
            LLM_SELECTION_TO_MODEL_ID[selection],
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
        )
        for selection in LLMModelSelection
    }
    return Clients(
        http={},
        llm_models=llm_models,
        llm_model_id_map=LLM_SELECTION_TO_MODEL_ID,
    )
