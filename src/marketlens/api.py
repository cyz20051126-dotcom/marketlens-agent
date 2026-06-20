from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from marketlens.agent.orchestrator import MarketLensAgentOrchestrator

# Load .env from project root so DEEPSEEK_API_KEY is available to the
# orchestrator's _default_llm_client() without manual export.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)


def create_app(
    session_dir: Path | None = None,
    search_cache_dir: Path | None = None,
) -> FastAPI:
    app = FastAPI(title="MarketLens Agent API")
    root = Path(__file__).resolve().parents[2]
    orchestrator = MarketLensAgentOrchestrator(
        evidence_path=root / "data" / "evidence.csv",
        finance_metrics_path=root / "data" / "finance_metrics.csv",
        session_dir=session_dir or root / "work" / "agent_sessions",
        search_cache_dir=search_cache_dir or root / ".search_cache",
    )

    @app.post("/api/agent/chat")
    def chat(request: ChatRequest) -> dict[str, Any]:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=422, detail="query must not be empty")
        return orchestrator.answer(query).to_dict()

    @app.get("/api/agent/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        try:
            return orchestrator.load_run(run_id)
        except (FileNotFoundError, ValueError):
            raise HTTPException(status_code=404, detail="run not found") from None

    return app


app = create_app()
