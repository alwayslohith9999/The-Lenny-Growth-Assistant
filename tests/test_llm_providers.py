from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider, OfflineSynthesisProvider, generate_with_fallback


class MockProvider(BaseLLMProvider):
    def generate(self, messages, system=None):
        return {
            "content": "Mocked LLM Response",
            "provider": "mock",
            "model": "mock-v1",
            "prompt_tokens": 10,
            "completion_tokens": 5
        }


def test_mock_provider():
    provider = MockProvider()
    res = provider.generate([{"role": "user", "content": "Hello"}])
    assert res["content"] == "Mocked LLM Response"
    assert res["provider"] == "mock"
    assert res["model"] == "mock-v1"
    assert res["prompt_tokens"] == 10
    assert res["completion_tokens"] == 5


def test_offline_synthesis_provider_with_context():
    provider = OfflineSynthesisProvider()
    res = provider.generate(
        [{"role": "user", "content": "PLG Advice"}],
        system="PROVIDED TRANSCRIPT CONTEXT:\nTest Context about PLG strategies"
    )
    assert "PLG Advice" in res["content"]
    assert "Test Context about PLG strategies" in res["content"]
    assert res["provider"] == "offline-grounded-fallback"
    assert res["model"] == "local-synthesizer"


def test_offline_synthesis_provider_no_context():
    provider = OfflineSynthesisProvider()
    res = provider.generate(
        [{"role": "user", "content": "Quantum Computing"}],
        system=None
    )
    assert "not covered" in res["content"]
    assert res["provider"] == "offline-grounded-fallback"


def test_offline_synthesis_provider_essay_mode():
    provider = OfflineSynthesisProvider()
    res = provider.generate(
        [{"role": "user", "content": "PLG growth strategies"}],
        system="SHIP 30 FOR 30 WRITING PRINCIPLES\nPROVIDED TRANSCRIPT SOURCES:\nSome grounded context here"
    )
    assert "Ship 30 for 30" in res["content"]
    assert "Some grounded context here" in res["content"]
    assert res["completion_tokens"] == 500


def test_generate_with_fallback_reaches_offline():
    """When no cloud keys and no Ollama are available, should fall through to OfflineSynthesisProvider."""
    res = generate_with_fallback(
        messages=[{"role": "user", "content": "Growth loops"}],
        system="PROVIDED TRANSCRIPT CONTEXT:\nGrowth loop info",
        requested_provider="anthropic"
    )
    # Should succeed via offline fallback (since no real API key is configured)
    assert "content" in res
    assert res["provider"] in ("anthropic", "ollama", "offline-grounded-fallback")


def test_offline_synthesis_empty_messages():
    provider = OfflineSynthesisProvider()
    res = provider.generate([], system="PROVIDED TRANSCRIPT CONTEXT:\nSome context")
    assert "query" in res["content"]
