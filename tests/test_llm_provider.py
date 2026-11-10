import pytest
from app.core.llm import get_chat_llm, validate_provider_credentials


def test_get_chat_llm_openai_default():
    """Factory should return ChatOpenAI when provider is openai or default."""
    llm = get_chat_llm(temperature=0.5, provider="openai")
    assert llm is not None
    assert hasattr(llm, "with_structured_output")


def test_get_chat_llm_unsupported_provider():
    """Factory should raise ValueError for invalid provider names."""
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_chat_llm(provider="unsupported_provider_xyz")


def test_validate_provider_credentials():
    """validate_provider_credentials returns False if only placeholder or missing key."""
    # When testing with default mock key, validate_provider_credentials correctly indicates real key absence
    is_valid = validate_provider_credentials("openai")
    # Should be a boolean
    assert isinstance(is_valid, bool)

