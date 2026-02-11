from langchain.chat_models import init_chat_model
from src.chatbot.types.llm_models import LLMProviderModelId
from langchain_core.language_models import BaseChatModel


def get_model(model_id: LLMProviderModelId, temperature: int | float = 0) -> BaseChatModel:
    return init_chat_model(
        model=model_id,
        temperature=temperature
    )
