"""
Data Collector - 从 LingClaude 收集会话历史数据
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class SessionRecord:
    """单条会话记录"""
    session_id: str
    timestamp: float
    query: str
    model: str
    agent: str | None
    input_tokens: int
    output_tokens: int
    latency_ms: float
    success: bool
    quality_score: float | None = None
    api_cost_usd: float | None = None
    error_message: str | None = None

    @property
    def total_tokens(self) -> int:
        """总 token 数"""
        return self.input_tokens + self.output_tokens

    @property
    def datetime(self) -> datetime:
        """时间戳转换为 datetime"""
        return datetime.fromtimestamp(self.timestamp)


class DataCollector:
    """从 LingClaude 会话历史收集数据"""

    def __init__(self, session_dir: str | Path):
        """
        初始化数据收集器

        Args:
            session_dir: LingClaude 会话目录路径
        """
        self.session_dir = Path(session_dir)
        if not self.session_dir.exists():
            raise ValueError(f"Session directory does not exist: {session_dir}")

    def collect_sessions(self) -> list[SessionRecord]:
        """
        收集所有会话数据

        Returns:
            SessionRecord 列表
        """
        records: list[SessionRecord] = []

        # 读取 session_history.json
        history_path = self.session_dir / "session_history.json"
        if history_path.exists():
            try:
                with open(history_path) as f:
                    history = json.load(f)

                for item in history:
                    try:
                        record = SessionRecord(
                            session_id=item.get("session_id", ""),
                            timestamp=item.get("created_at", 0),
                            query=item.get("query", ""),
                            model="",
                            agent=item.get("agent"),
                            input_tokens=0,
                            output_tokens=0,
                            latency_ms=0.0,
                            success=True
                        )
                        records.append(record)
                    except Exception as e:
                        logger.warning(f"Failed to parse history item: {e}")
            except Exception as e:
                logger.warning(f"Failed to read session_history.json: {e}")

        # 读取详细 session 文件
        for session_file in self.session_dir.glob("*.json"):
            if session_file.name == "session_history.json":
                continue

            try:
                with open(session_file) as f:
                    session_data = json.load(f)

                # 解析详细数据
                messages = session_data.get("messages", [])
                if not messages:
                    continue

                # 提取第一条用户查询
                query = ""
                for msg in messages:
                    if msg.get("role") == "user":
                        query = msg.get("content", "")
                        break

                # 提取统计信息
                input_tokens = session_data.get("input_tokens", 0)
                output_tokens = session_data.get("output_tokens", 0)
                model = session_data.get("model", "")
                agent = session_data.get("agent", "")
                success = session_data.get("success", True)

                # 如果 session_history.json 中已记录，更新其详细信息
                session_id = session_file.stem
                updated = False
                for record in records:
                    if record.session_id == session_id:
                        record.model = model
                        record.agent = agent
                        record.input_tokens = input_tokens
                        record.output_tokens = output_tokens
                        record.success = success
                        updated = True
                        break

                # 如果 session_history.json 中未记录，创建新记录
                if not updated and query:
                    record = SessionRecord(
                        session_id=session_id,
                        timestamp=session_file.stat().st_mtime,
                        query=query,
                        model=model,
                        agent=agent,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        latency_ms=0.0,
                        success=success
                    )
                    records.append(record)

            except Exception as e:
                logger.warning(f"Failed to read session file {session_file}: {e}")
                continue

        # 按时间戳排序
        records.sort(key=lambda x: x.timestamp)

        logger.info(f"Collected {len(records)} session records from {self.session_dir}")

        return records

    def sample_tasks(self, n: int = 100, random_seed: int | None = None) -> list[dict]:
        """
        采样 n 个任务用于评估

        Args:
            n: 采样数量
            random_seed: 随机种子

        Returns:
            采样后的任务字典列表
        """
        import random

        records = self.collect_sessions()

        if random_seed is not None:
            random.seed(random_seed)

        if len(records) <= n:
            sampled_records = records
        else:
            # 按意图类型分层采样（如果有的话）
            sampled_records = random.sample(records, n)

        # 转换为字典格式
        sampled = [
            {
                "session_id": r.session_id,
                "query": r.query,
                "model": r.model,
                "agent": r.agent,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "total_tokens": r.total_tokens,
                "latency_ms": r.latency_ms,
                "success": r.success,
                "quality_score": r.quality_score,
            }
            for r in sampled_records
        ]

        return sampled

    def get_statistics(self) -> dict[str, Any]:
        """
        获取会话统计信息

        Returns:
            统计信息字典
        """
        records = self.collect_sessions()

        if not records:
            return {
                "total_sessions": 0,
                "total_tokens": 0,
                "avg_tokens_per_session": 0,
                "success_rate": 0.0,
            }

        total_tokens = sum(r.total_tokens for r in records)
        success_count = sum(1 for r in records if r.success)

        return {
            "total_sessions": len(records),
            "total_tokens": total_tokens,
            "avg_tokens_per_session": total_tokens / len(records),
            "success_rate": success_count / len(records),
            "model_distribution": self._get_model_distribution(records),
            "agent_distribution": self._get_agent_distribution(records),
        }

    def _get_model_distribution(self, records: list[SessionRecord]) -> dict[str, int]:
        """获取模型分布"""
        distribution: dict[str, int] = {}
        for record in records:
            model = record.model or "unknown"
            distribution[model] = distribution.get(model, 0) + 1
        return distribution

    def _get_agent_distribution(self, records: list[SessionRecord]) -> dict[str, int]:
        """获取 Agent 分布"""
        distribution: dict[str, int] = {}
        for record in records:
            agent = record.agent or "unknown"
            distribution[agent] = distribution.get(agent, 0) + 1
        return distribution
