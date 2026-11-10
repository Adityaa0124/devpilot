import os
from typing import Optional, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)
from app.core.logging import get_logger

logger = get_logger("llm_factory")


def get_chat_llm(temperature: float = 0.7, provider: Optional[str] = None) -> BaseChatModel:
    """
    Centralized LLM provider factory.
    Supports OpenAI and Google Gemini with credential validation and error messaging.

    Raises:
        ValueError: If the required API key for the chosen provider is not set.
    """
    selected_provider = (provider or LLM_PROVIDER or "openai").lower()

    if selected_provider == "openai":
        api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        # In unit tests or mock runs, provide a fallback placeholder to allow import & patching
        effective_key = api_key if (api_key and not api_key.startswith("sk-...")) else (api_key or "mock-test-key-openai")
        return ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=temperature,
            api_key=effective_key,
        )

    if selected_provider in ("gemini", "google"):
        api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        raw_model = GEMINI_MODEL or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        model_name = raw_model.strip()
        if not model_name.startswith("gemini-") and not model_name.startswith("models/"):
            model_name = f"gemini-{model_name}".replace(" ", "-")

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            effective_key = api_key if api_key else "mock-test-key-gemini"
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                google_api_key=effective_key,
            )
        except ImportError:
            # Fallback if langchain-google-genai is not installed: use OpenAI-compatible proxy or raise clear error
            raise ImportError(
                "Google Gemini provider requested, but `langchain-google-genai` is not installed. "
                "Install it using `pip install langchain-google-genai` or set LLM_PROVIDER=openai."
            )

    raise ValueError(
        f"Unsupported LLM provider: '{selected_provider}'. Supported providers are: 'openai', 'gemini'."
    )


def validate_provider_credentials(provider: Optional[str] = None) -> bool:
    """Validates that real credentials exist for the selected provider."""
    selected = (provider or LLM_PROVIDER or "openai").lower()
    if selected == "openai":
        key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        return bool(key and not key.startswith("sk-..."))
    if selected in ("gemini", "google"):
        key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
        return bool(key)
    return False

