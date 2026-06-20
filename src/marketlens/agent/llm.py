from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Protocol
import urllib.parse
import urllib.request


@dataclass(frozen=True)
class LLMResult:
    content: str
    provider: str
    # True when the result came from the intended provider (e.g. DeepSeek).
    # False when the client degraded to the fallback (no key, request
    # failed, unsafe base URL). The orchestrator surfaces this on the
    # AgentRun so the frontend can show whether the answer was
    # LLM-generated or rule-generated.
    llm_used: bool = True
    fallback_reason: str = ""


class LLMClient(Protocol):
    """Unified interface for all LLM clients (DeepSeek, fallback, mock)."""

    provider: str

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any] | None = None,
    ) -> LLMResult: ...


class FallbackLLMClient:
    """Offline fallback. Echoes prompt when no context; builds a structured
    Chinese answer from evidence when context is supplied. Used when no
    DeepSeek API key is present so demos still produce readable output.

    Every result from this client carries llm_used=False so the
    orchestrator and frontend can distinguish rule-generated answers
    from real LLM output."""

    provider = "fallback"

    def __init__(self, reason: str = "no_api_key") -> None:
        self._reason = reason
        # Orchestrator reads these after a run to populate AgentRun.
        self.last_llm_used = False
        self.last_fallback_reason = reason

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any] | None = None,
    ) -> LLMResult:
        if context and context.get("evidence"):
            content = _fallback_answer_from_context(user_prompt, context)
        else:
            content = user_prompt
        result = LLMResult(
            content=content,
            provider=self.provider,
            llm_used=False,
            fallback_reason=self._reason,
        )
        # Track the most recent call so the orchestrator can surface
        # whether the answer was LLM-generated or rule-generated.
        self.last_llm_used = result.llm_used
        self.last_fallback_reason = result.fallback_reason
        return result


class DeepSeekLLMClient:
    """DeepSeek OpenAI-compatible client. Falls back to FallbackLLMClient
    when API key is missing, base URL is unsafe, or the request fails."""

    provider = "deepseek"

    def __init__(
        self,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> None:
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        self.base_url = os.environ.get(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        ).rstrip("/")
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.fallback = FallbackLLMClient(reason="no_api_key")
        # Orchestrator reads these after a run to populate AgentRun.
        self.last_llm_used = False
        self.last_fallback_reason = "no_call_made_yet"

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any] | None = None,
    ) -> LLMResult:
        if not self.api_key:
            self.last_llm_used = False
            self.last_fallback_reason = "no_api_key"
            return self.fallback.complete(system_prompt, user_prompt, context)
        if not _is_safe_base_url(self.base_url):
            self.last_llm_used = False
            self.last_fallback_reason = "unsafe_base_url"
            return FallbackLLMClient(reason="unsafe_base_url").complete(
                system_prompt, user_prompt, context
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
            result = LLMResult(
                content=str(content),
                provider=self.provider,
                llm_used=True,
                fallback_reason="",
            )
            self.last_llm_used = result.llm_used
            self.last_fallback_reason = result.fallback_reason
            return result
        except Exception as exc:
            reason = f"request_failed: {type(exc).__name__}"
            result = FallbackLLMClient(reason=reason).complete(
                system_prompt, user_prompt, context
            )
            # FallbackLLMClient.complete already set its own last_* attrs,
            # but those belong to the throwaway fallback instance. Update
            # self so the orchestrator reads the DeepSeek client's state.
            self.last_llm_used = False
            self.last_fallback_reason = reason
            return result


class MockLLMClient:
    """Test double. Returns a preset response regardless of input. Use in
    unit tests to avoid network calls and keep assertions deterministic."""

    provider = "mock"

    def __init__(self, response: str = "mock response") -> None:
        self.response = response

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any] | None = None,
    ) -> LLMResult:
        return LLMResult(content=self.response, provider=self.provider)


def _fallback_answer_from_context(user_prompt: str, context: dict[str, Any]) -> str:
    """Build a readable Chinese answer from evidence in context. Used by
    FallbackLLMClient when DeepSeek is unavailable but evidence exists."""
    query = str(context.get("query", user_prompt)).strip()
    evidence = context.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []

    lines = [f'针对\u201c{query}\u201d，基于本地证据：', ""]
    for row in evidence:
        if not isinstance(row, dict):
            continue
        evidence_id = str(row.get("evidence_id", "")).strip()
        claim = str(row.get("claim", row.get("excerpt", ""))).strip()
        if not evidence_id or not claim:
            continue
        lines.append(f"- {evidence_id}: {claim}")

    lines.extend([
        "",
        "局限性：以上结论基于本地证据库，可能未包含最新动态。"
        "如需补充最新信息，可触发联网搜索。",
    ])
    return "\n".join(lines)


def _is_safe_base_url(base_url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(base_url)
    except Exception:
        return False

    if parsed.scheme == "https" and parsed.netloc:
        return True

    if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}:
        return True

    return False
