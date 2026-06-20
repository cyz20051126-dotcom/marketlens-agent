from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from marketlens.agent.models import AgentRun


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(f"Invalid run_id: {run_id}")
    return run_id


class SessionStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_run(self, run: AgentRun) -> Path:
        run_id = _validate_run_id(run.run_id)
        path = self.root / f"{run_id}.json"
        path.write_text(
            json.dumps(run.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load_run(self, run_id: str) -> dict[str, Any]:
        safe_run_id = _validate_run_id(run_id)
        path = self.root / f"{safe_run_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))
