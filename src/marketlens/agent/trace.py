from __future__ import annotations

from datetime import datetime
from typing import Any

from marketlens.agent.models import TraceEvent


PREVIEW_LIMIT = 240


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _preview(value: Any) -> str:
    text = str(value)
    return text[:PREVIEW_LIMIT]


class TraceLogger:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self._events: list[TraceEvent] = []

    def record(
        self,
        agent_name: str,
        event_type: str,
        summary: str,
        input_payload: Any = "",
        output_payload: Any = "",
        tool_name: str = "",
        tool_status: str = "",
        latency_ms: int = 0,
    ) -> TraceEvent:
        event = TraceEvent(
            event_id=f"trace_{len(self._events) + 1:03d}",
            run_id=self.run_id,
            timestamp=now_iso(),
            agent_name=agent_name,
            event_type=event_type,
            summary=summary,
            input_preview=_preview(input_payload),
            output_preview=_preview(output_payload),
            tool_name=tool_name,
            tool_status=tool_status,
            latency_ms=latency_ms,
        )
        self._events.append(event)
        return event

    def events(self) -> list[TraceEvent]:
        return list(self._events)
