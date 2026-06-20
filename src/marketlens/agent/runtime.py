from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Protocol

from marketlens.agent.models import TodoItem


@dataclass(frozen=True)
class ToolResponse:
    success: bool
    data: dict[str, Any]
    error: str = ""


class Tool(Protocol):
    name: str
    description: str

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def call(self, tool_name: str, payload: dict[str, Any]) -> ToolResponse:
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResponse(False, {}, f"Tool is not registered: {tool_name}")

        try:
            return tool.run(payload)
        except Exception as exc:
            return ToolResponse(False, {}, str(exc))

    def names(self) -> list[str]:
        return sorted(self._tools)


class BaseAgent:
    name = "BaseAgent"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class TodoBoard:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self._items: list[TodoItem] = []

    def add(
        self,
        title: str,
        intent: str,
        query: str,
        assigned_agent: str,
        supporting_source_urls: list[str] | None = None,
        result_summary: str = "",
        task_type: str = "",
    ) -> TodoItem:
        todo = TodoItem(
            todo_id=f"todo_{len(self._items) + 1:03d}",
            run_id=self.run_id,
            title=title,
            intent=intent,
            query=query,
            status="pending",
            assigned_agent=assigned_agent,
            supporting_source_urls=list(supporting_source_urls or []),
            result_summary=result_summary,
            task_type=task_type,
        )
        self._items.append(todo)
        return todo

    def complete(
        self,
        todo_id: str,
        result_summary: str = "",
        source_urls: list[str] | None = None,
    ) -> TodoItem:
        for index, item in enumerate(self._items):
            if item.todo_id == todo_id:
                next_source_urls = (
                    list(item.supporting_source_urls)
                    if source_urls is None
                    else list(source_urls)
                )
                completed = replace(
                    item,
                    status="completed",
                    supporting_source_urls=next_source_urls,
                    result_summary=result_summary,
                )
                self._items[index] = completed
                return completed
        raise ValueError(f"Todo is not registered: {todo_id}")

    def items(self) -> list[TodoItem]:
        return list(self._items)
