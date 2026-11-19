"""
Nemr Voice Flow - SQLite Multi-Turn Conversation Memory, Escalation & FinOps Estimator (v3.0.0)
Persists caller history across turns, detects Arabic/English frustration triggers, and estimates Gemini Live session costs.
"""

from __future__ import annotations
import datetime
import sqlite3
from typing import Any, Dict, List


class ConversationMemory:
    """Tracks caller multi-turn history, detects human escalation triggers, and meters voice token cost."""

    ESCALATION_TRIGGERS = (
        "شكوى",
        "مشكلة كبيرة",
        "مدير",
        "نصب",
        "غلط",
        "حولني لموظف",
        "موظف بشري",
        "refund",
        "human agent",
        "complaint",
        "angry",
        "supervisor",
    )

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caller_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT NOT NULL DEFAULT 'GENERAL',
                audio_sec REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def add_turn(
        self,
        caller_id: str,
        role: str,
        content: str,
        intent: str = "GENERAL",
        audio_sec: float = 0.0,
    ) -> int:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cur = self._conn.execute(
            """
            INSERT INTO voice_turns (caller_id, role, content, intent, audio_sec, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (caller_id, role, content, intent, float(audio_sec), now_iso),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_context_window(self, caller_id: str, max_turns: int = 10) -> List[Dict[str, Any]]:
        cur = self._conn.execute(
            """
            SELECT role, content, intent, audio_sec, created_at
            FROM voice_turns
            WHERE caller_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (caller_id, max(1, max_turns)),
        )
        rows = list(reversed(cur.fetchall()))
        return [
            {
                "role": r[0],
                "content": r[1],
                "intent": r[2],
                "audio_sec": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]

    @classmethod
    def detect_escalation(cls, text: str) -> Dict[str, Any]:
        lowered = text.lower()
        matched = [t for t in cls.ESCALATION_TRIGGERS if t in lowered]
        if matched:
            return {
                "escalate": True,
                "reason": "Customer requested human supervisor / raised critical complaint.",
                "matched_triggers": matched,
            }
        return {
            "escalate": False,
            "reason": "",
            "matched_triggers": [],
        }

    @classmethod
    def estimate_session_cost(
        cls,
        audio_in_sec: float,
        audio_out_sec: float,
        text_tokens: int = 500,
    ) -> Dict[str, float]:
        # Gemini Live audio rate benchmark: ~25 tokens/second
        audio_in_tokens = round(max(0.0, audio_in_sec) * 25.0)
        audio_out_tokens = round(max(0.0, audio_out_sec) * 25.0)
        total_tokens = audio_in_tokens + audio_out_tokens + max(0, text_tokens)

        # Standard multimodal streaming rate estimate ($0.0005 per 1k input/text equiv, $0.0020 per 1k audio out equiv)
        cost_usd = (
            (audio_in_tokens / 1000.0) * 0.0007
            + (audio_out_tokens / 1000.0) * 0.0020
            + (max(0, text_tokens) / 1000.0) * 0.0002
        )
        return {
            "audio_in_tokens": float(audio_in_tokens),
            "audio_out_tokens": float(audio_out_tokens),
            "text_tokens": float(text_tokens),
            "total_tokens": float(total_tokens),
            "estimated_cost_usd": round(cost_usd, 6),
        }

    def close(self) -> None:
        self._conn.close()
