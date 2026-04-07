from unittest.mock import patch

import pytest

from app.config import settings
from app.services import llm as llm_mod


def test_llm_backend_label_openrouter_when_key(monkeypatch):
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    assert llm_mod.llm_backend_label() == "openrouter"
    assert llm_mod.active_model_name() == settings.OPENROUTER_MODEL


def test_llm_backend_label_openai_when_no_openrouter(monkeypatch):
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-openai-test")
    assert llm_mod.llm_backend_label() == "openai"
    assert llm_mod.active_model_name() == settings.OPENAI_MODEL


def test_get_chat_model_openrouter_uses_base_url(monkeypatch):
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-or-x")
    monkeypatch.setattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "test/model")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "unused")

    with patch.object(llm_mod, "ChatOpenAI") as mock_cls:
        llm_mod.get_chat_model()
    kwargs = mock_cls.call_args.kwargs
    assert kwargs["api_key"] == "sk-or-x"
    assert kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert kwargs["model"] == "test/model"
    assert "HTTP-Referer" in kwargs["default_headers"]


def test_get_chat_model_openai_no_base_url(monkeypatch):
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-openai")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    with patch.object(llm_mod, "ChatOpenAI") as mock_cls:
        llm_mod.get_chat_model()
    kwargs = mock_cls.call_args.kwargs
    assert kwargs["api_key"] == "sk-openai"
    assert kwargs["model"] == "gpt-4o-mini"
    assert "base_url" not in kwargs


def test_get_chat_model_raises_when_no_keys(monkeypatch):
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    with pytest.raises(RuntimeError, match="No LLM configured"):
        llm_mod.get_chat_model()
