from langchain_core.messages import HumanMessage

from app.services import llm


def test_invoke_with_fallback_openrouter_then_gemini(monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER_ORDER", "openrouter,gemini")
    monkeypatch.setattr(llm.settings, "LLM_FALLBACK_ENABLED", True)
    monkeypatch.setattr(llm.settings, "OPENROUTER_API_KEY", "x")
    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", "y")

    class _OpenRouterModel:
        def invoke(self, messages):
            raise RuntimeError("openrouter 500")

    class _Resp:
        def __init__(self, content):
            self.content = content

    monkeypatch.setattr(
        llm,
        "_build_openrouter_model",
        lambda **kwargs: _OpenRouterModel(),
    )
    monkeypatch.setattr(llm, "_invoke_gemini", lambda messages: _Resp("{}"))

    resp, provider = llm.invoke_with_fallback([HumanMessage(content="hello")], max_tokens=100)
    assert provider == "gemini"
    assert resp.content == "{}"


def test_invoke_with_fallback_raises_when_all_fail(monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER_ORDER", "openrouter,gemini")
    monkeypatch.setattr(llm.settings, "LLM_FALLBACK_ENABLED", True)
    monkeypatch.setattr(llm.settings, "OPENROUTER_API_KEY", "x")
    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", "y")
    monkeypatch.setattr(
        llm,
        "_build_openrouter_model",
        lambda **kwargs: type("M", (), {"invoke": lambda self, m: (_ for _ in ()).throw(RuntimeError("or fail"))})(),
    )
    monkeypatch.setattr(
        llm,
        "_invoke_gemini",
        lambda messages: (_ for _ in ()).throw(RuntimeError("gem fail")),
    )

    try:
        llm.invoke_with_fallback([HumanMessage(content="hello")], max_tokens=100)
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "All LLM providers failed" in str(e)
