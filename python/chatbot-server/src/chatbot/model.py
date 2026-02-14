from langchain.chat_models import init_chat_model
from src.chatbot.types.llm_models import LLMProviderModelId
from langchain_core.language_models import BaseChatModel


def get_model(
    model_id: LLMProviderModelId,
    temperature: int | float = 0,
    *,
    api_key: str | None = None,
) -> BaseChatModel:
    kwargs: dict = {"model": model_id, "temperature": temperature}
    if api_key is not None:
        kwargs["api_key"] = api_key
    return init_chat_model(**kwargs)
