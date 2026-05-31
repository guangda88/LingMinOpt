"""
LingBus Data Collector - 从灵族crush.db和LingBus提取真实会话数据
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .data_collector import SessionRecord

logger = logging.getLogger(__name__)

LINGCLAN_MEMBERS = [
    "lingflow",
    "lingclaude",
    "lingresearch",
    "lingzhi",
    "lingtongask",
    "lingflowplus",
    "lingxi",
    "lingmessage",
    "lingweb",
    "lingminopt",
    "lingyang",
    "lingcreate",
    "zhibridge",
]

CRUSH_DB_PATHS = {member: Path(f"/home/ai/{member}/.crush/crush.db") for member in LINGCLAN_MEMBERS}

LINGBUS_DB = Path.home() / ".lingmessage" / "lingbus.db"


@dataclass
class MemberSessionStats:
    member: str
    total_sessions: int
    total_messages: int
    avg_messages_per_session: float
    total_assistant_messages: int
    total_tool_calls: int
    time_range: tuple[datetime | None, datetime | None]
    estimated_input_tokens: int
    estimated_output_tokens: int


def _extract_text(parts_json: str | None) -> str:
    if not parts_json:
        return ""
    try:
        parts = json.loads(parts_json)
    except (json.JSONDecodeError, TypeError):
        return parts_json or ""
    if not isinstance(parts, list):
        return str(parts)
    texts = []
    for p in parts:
        if not isinstance(p, dict):
            continue
        ptype = p.get("type", "")
        if ptype == "text":
            data = p.get("data", {})
            if isinstance(data, dict):
                texts.append(data.get("text", ""))
            elif isinstance(data, str):
                texts.append(data)
        elif ptype == "tool_call":
            texts.append(p.get("data", {}).get("name", ""))
        elif ptype == "tool_result":
            content = p.get("data", {}).get("content", "")
            if isinstance(content, str):
                texts.append(content[:500])
    return " ".join(texts)


class LingBusCollector:
    def __init__(
        self,
        lingbus_db: str | Path | None = None,
        crush_db_paths: dict[str, Path] | None = None,
    ):
        self.lingbus_db = Path(lingbus_db) if lingbus_db else LINGBUS_DB
        self.crush_db_paths = crush_db_paths or CRUSH_DB_PATHS

    def collect_member_stats(self, member: str) -> MemberSessionStats | None:
        crush_db = self.crush_db_paths.get(member)
        if not crush_db or not crush_db.exists():
            logger.debug(f"No crush.db for {member}")
            return None
        try:
            conn = sqlite3.connect(f"file:{crush_db}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT role, parts, created_at, model, provider FROM messages "
                "ORDER BY created_at"
            ).fetchall()
            session_count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to read {member} crush.db: {e}")
            return None

        total = len(rows)
        if total == 0:
            return MemberSessionStats(
                member=member,
                total_sessions=0,
                total_messages=0,
                avg_messages_per_session=0.0,
                total_assistant_messages=0,
                total_tool_calls=0,
                time_range=(None, None),
                estimated_input_tokens=0,
                estimated_output_tokens=0,
            )

        assistant_msgs = [r for r in rows if r["role"] == "assistant"]
        tool_calls = 0
        for r in assistant_msgs:
            raw = r["parts"] or "[]"
            if '"tool_call"' in raw:
                tool_calls += 1

        timestamps = [r["created_at"] for r in rows if r["created_at"]]
        time_range = (
            datetime.fromtimestamp(min(timestamps) / 1000) if timestamps else None,
            datetime.fromtimestamp(max(timestamps) / 1000) if timestamps else None,
        )

        est_input = sum(len(_extract_text(r["parts"])) for r in rows if r["role"] == "user") // 4
        est_output = sum(len(_extract_text(r["parts"])) for r in assistant_msgs) // 4

        return MemberSessionStats(
            member=member,
            total_sessions=session_count,
            total_messages=total,
            avg_messages_per_session=total / max(session_count, 1),
            total_assistant_messages=len(assistant_msgs),
            total_tool_calls=tool_calls,
            time_range=time_range,
            estimated_input_tokens=est_input,
            estimated_output_tokens=est_output,
        )

    def collect_all_stats(self) -> dict[str, MemberSessionStats]:
        results: dict[str, MemberSessionStats] = {}
        for member in LINGCLAN_MEMBERS:
            stats = self.collect_member_stats(member)
            if stats:
                results[member] = stats
        return results

    def collect_lingbus_messages(
        self,
        since: str | None = None,
        limit: int = 1000,
    ) -> list[SessionRecord]:
        if not self.lingbus_db.exists():
            logger.warning(f"LingBus DB not found: {self.lingbus_db}")
            return []
        try:
            conn = sqlite3.connect(f"file:{self.lingbus_db}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            query = (
                "SELECT rowid, sender, recipient, subject, body, timestamp, channel "
                "FROM messages"
            )
            params: list[Any] = []
            if since:
                query += " WHERE timestamp > ?"
                params.append(since)
            query += " ORDER BY rowid DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to read LingBus DB: {e}")
            return []

        records: list[SessionRecord] = []
        for row in rows:
            body = row["body"] or ""
            body_chars = len(body)
            records.append(
                SessionRecord(
                    session_id=f"lingbus_{row['rowid']}",
                    timestamp=0.0,
                    query=row["subject"] or body[:100],
                    model="lingbus",
                    agent=row["sender"],
                    input_tokens=body_chars // 4,
                    output_tokens=0,
                    latency_ms=0.0,
                    success=True,
                )
            )
        return records

    def to_session_records(self, stats: dict[str, MemberSessionStats]) -> list[SessionRecord]:
        records: list[SessionRecord] = []
        for member, s in stats.items():
            records.append(
                SessionRecord(
                    session_id=f"{member}_aggregate",
                    timestamp=0.0,
                    query=f"{member} aggregate session data",
                    model="unknown",
                    agent=member,
                    input_tokens=s.estimated_input_tokens,
                    output_tokens=s.estimated_output_tokens,
                    latency_ms=0.0,
                    success=True,
                )
            )
        return records
