"""
Ashiee Transcript Logger
Records session history in dual JSONL format: compact transcript.jsonl and full transcript_full.jsonl.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TranscriptEntry(BaseModel):
    step_index: int
    role: str
    content: Optional[str] = None
    thought: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    timestamp: str = ""


class TranscriptLogger:
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.compact_path = self.session_dir / "transcript.jsonl"
        self.full_path = self.session_dir / "transcript_full.jsonl"
        self._step_counter = 0

    def record_step(
        self,
        role: str,
        content: Optional[str] = None,
        thought: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._step_counter += 1
        now = datetime.now(timezone.utc).isoformat()

        # Full entry
        full_entry = {
            "step_index": self._step_counter,
            "timestamp": now,
            "role": role,
            "content": content,
            "thought": thought,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
        }

        # Compact entry (truncates large outputs to save token inspection size)
        compact_results = None
        if tool_results:
            compact_results = []
            for r in tool_results:
                out = r.get("output", "")
                compact_results.append({
                    "name": r.get("name"),
                    "success": r.get("success"),
                    "output_preview": out[:200] + ("..." if len(out) > 200 else "")
                })

        compact_entry = {
            "step_index": self._step_counter,
            "timestamp": now,
            "role": role,
            "content": content[:500] if content else None,
            "tool_calls": [{"name": c.get("name")} for c in tool_calls] if tool_calls else None,
            "tool_results": compact_results,
        }

        with open(self.full_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(full_entry) + "\n")

        with open(self.compact_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(compact_entry) + "\n")
