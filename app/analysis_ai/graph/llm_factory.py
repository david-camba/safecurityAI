from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from app.config import settings


def get_gemini_llm(
    temperature: float = 0.0,
    max_retries: int = 3,
    tools: list = None,
    model_name: str = "models/gemini-3.1-flash-lite-preview",
) -> BaseChatModel:
    """
    Factory for ChatGoogleGenerativeAI instances to standardize configuration
    and simplify dependency injection during testing.
    """
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        max_retries=max_retries,
        google_api_key=settings.GOOGLE_API_KEY,
    )

    if tools:
        return llm.bind_tools(tools)

    return llm
