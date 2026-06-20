"""Tests for the LLM client layer: DeepSeek client, fallback client, mock client.

These tests verify the unified LLMClient interface, the DeepSeek HTTP integration
(mocked, no real network), the fallback's structured-answer-from-evidence upgrade,
and the MockLLMClient used by downstream agent tests.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from marketlens.agent.llm import (
    DeepSeekLLMClient,
    FallbackLLMClient,
    LLMClient,
    LLMResult,
    MockLLMClient,
)


# --- DeepSeekLLMClient -----------------------------------------------------


def test_deepseek_client_calls_api_when_key_present(monkeypatch):
    """When API key and safe base URL are present, DeepSeekLLMClient posts
    to the chat/completions endpoint and returns the LLM content."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.example")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-test")

    captured: dict[str, Any] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps(
                {
                    "choices": [
                        {"message": {"content": "DeepSeek reply."}}
                    ]
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout=30):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = DeepSeekLLMClient(temperature=0.7, max_tokens=512)
    result = client.complete("system prompt", "user prompt")

    assert result.provider == "deepseek"
    assert result.content == "DeepSeek reply."

    request = captured["request"]
    assert request.full_url == "https://api.deepseek.example/chat/completions"
    assert request.method == "POST"
    assert request.headers.get("Authorization") == "Bearer test-key"

    body = json.loads(request.data.decode("utf-8"))
    assert body["model"] == "deepseek-test"
    assert body["temperature"] == 0.7
    assert body["max_tokens"] == 512
    assert body["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user prompt"},
    ]


def test_deepseek_client_passes_context_ignored_by_deepseek(monkeypatch):
    """Context is accepted by the interface but DeepSeek path does not need
    to inject it into the payload (agents serialize context into user_prompt
    themselves). The call still succeeds."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.example")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": "ok"}}]}
            ).encode("utf-8")

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *a, **k: FakeResponse()
    )

    result = DeepSeekLLMClient().complete(
        "system", "user", context={"query": "luckin", "evidence": []}
    )

    assert result.provider == "deepseek"
    assert result.content == "ok"


# --- FallbackLLMClient -----------------------------------------------------


def test_fallback_client_echoes_prompt_without_context():
    """Backward compatibility: no context means echo user_prompt, matching
    the pre-upgrade behavior that existing tests depend on."""
    client = FallbackLLMClient()

    result = client.complete("You are concise.", "瑞幸利润率?")

    assert result.provider == "fallback"
    assert result.content == "瑞幸利润率?"


def test_fallback_client_generates_structured_answer_from_evidence():
    """When context contains evidence, fallback builds a readable Chinese
    answer citing each evidence ID + claim, plus a limitations paragraph."""
    client = FallbackLLMClient()
    context = {
        "query": "瑞幸价格战对利润率影响",
        "evidence": [
            {
                "evidence_id": "EV-001",
                "claim": "瑞幸 2026 Q1 全球门店 33596 家。",
            },
            {
                "evidence_id": "EV-004",
                "claim": "瑞幸 GAAP 营业利润率从 8.3% 下滑至 6.0%。",
            },
        ],
    }

    result = client.complete("system", "user prompt", context=context)

    assert result.provider == "fallback"
    assert "瑞幸价格战对利润率影响" in result.content
    assert "EV-001" in result.content
    assert "33596" in result.content
    assert "EV-004" in result.content
    assert "6.0%" in result.content
    assert "局限性" in result.content


def test_fallback_client_handles_empty_evidence_in_context():
    """Context with empty evidence list still echoes the prompt (no evidence
    to cite, so no structured answer to build)."""
    client = FallbackLLMClient()

    result = client.complete("system", "query", context={"evidence": []})

    assert result.content == "query"


def test_fallback_client_skips_malformed_evidence_rows():
    """Malformed evidence rows (missing id or claim) are skipped, not crashed on."""
    client = FallbackLLMClient()
    context = {
        "query": "test",
        "evidence": [
            {"evidence_id": "EV-001", "claim": "valid claim"},
            {"evidence_id": "", "claim": "no id"},
            {"evidence_id": "EV-002", "claim": ""},
            "not a dict",
        ],
    }

    result = client.complete("system", "user", context=context)

    assert "EV-001" in result.content
    assert "valid claim" in result.content
    assert "EV-002" not in result.content
    assert "no id" not in result.content


# --- MockLLMClient ---------------------------------------------------------


def test_mock_client_returns_preset_content():
    """MockLLMClient returns exactly the response it was constructed with,
    regardless of prompts or context."""
    client = MockLLMClient(response="preset answer")

    result = client.complete("any system", "any user", context={"foo": "bar"})

    assert result.provider == "mock"
    assert result.content == "preset answer"


def test_mock_client_default_response():
    """Default response is 'mock response' when none is provided."""
    client = MockLLMClient()

    result = client.complete("s", "u")

    assert result.content == "mock response"


# --- Protocol conformance --------------------------------------------------


def test_all_clients_satisfy_protocol_interface():
    """All three clients expose the same complete(system, user, context=None)
    signature and return LLMResult. This is what lets agents accept any of
    them via dependency injection."""
    clients = [
        FallbackLLMClient(),
        MockLLMClient("x"),
        DeepSeekLLMClient(),  # no key in test env -> falls back, but type matches
    ]
    for client in clients:
        assert hasattr(client, "provider")
        assert hasattr(client, "complete")
        result = client.complete("s", "u")
        assert isinstance(result, LLMResult)
        assert isinstance(result.content, str)
        assert isinstance(result.provider, str)
