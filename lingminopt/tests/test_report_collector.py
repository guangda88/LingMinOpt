"""Tests for report_generator and lingbus_collector coverage gaps."""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from lingminopt.meta_optimizer.data_collector import SessionRecord


class TestReportGeneratorMarkdown:
    def test_markdown_with_member_stats(self, tmp_path):
        from lingminopt.meta_optimizer.lingbus_collector import MemberSessionStats
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        stats = {
            "lingflow": MemberSessionStats(
                member="lingflow",
                total_sessions=10,
                total_messages=100,
                avg_messages_per_session=10.0,
                total_assistant_messages=50,
                total_tool_calls=30,
                time_range=(datetime(2026, 1, 1), datetime(2026, 5, 1)),
                estimated_input_tokens=50000,
                estimated_output_tokens=150000,
            ),
            "lingminopt": MemberSessionStats(
                member="lingminopt",
                total_sessions=5,
                total_messages=20,
                avg_messages_per_session=4.0,
                total_assistant_messages=10,
                total_tool_calls=5,
                time_range=(None, None),
                estimated_input_tokens=1000,
                estimated_output_tokens=3000,
            ),
        }
        results = {"target_member": "灵族"}
        path = rg.generate_markdown_report(results, member_stats=stats)
        content = path.read_text()
        assert "lingflow" in content
        assert "lingminopt" in content
        assert "高优" in content
        assert "低优" in content

    def test_markdown_with_combined_score(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        results = {
            "target_member": "lingflow",
            "combined_score": 0.85,
            "total_experiments": 30,
            "total_time": 12.5,
        }
        path = rg.generate_markdown_report(results)
        content = path.read_text()
        assert "0.8500" in content
        assert "lingflow" in content

    def test_markdown_with_prompt_optimization(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        results = {
            "target_member": "lingflow",
            "prompt_optimization": {"model": "glm-5.1", "temperature": 0.7},
            "detailed_results": {
                "prompt": {"best_score": 0.9, "total_experiments": 10, "total_time": 3.0},
            },
        }
        path = rg.generate_markdown_report(results)
        content = path.read_text()
        assert "提示词优化" in content
        assert "glm-5.1" in content

    def test_markdown_with_routing_optimization(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        results = {
            "target_member": "lingflow",
            "routing_optimization": {"strategy": "hybrid"},
            "detailed_results": {
                "routing": {"best_score": 0.8, "total_experiments": 10, "total_time": 2.0},
            },
        }
        path = rg.generate_markdown_report(results)
        content = path.read_text()
        assert "路由优化" in content

    def test_markdown_with_retry_optimization(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        results = {
            "target_member": "lingflow",
            "retry_optimization": {"fallback_model": "qwen-max"},
            "detailed_results": {
                "retry": {"best_score": 0.75, "total_experiments": 10, "total_time": 1.5},
            },
        }
        path = rg.generate_markdown_report(results)
        content = path.read_text()
        assert "重试优化" in content

    def test_markdown_with_suggestions(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        results = {"target_member": "lingresearch"}
        path = rg.generate_markdown_report(results)
        content = path.read_text()
        assert "优化建议" in content
        assert "lingresearch" in content


class TestReportGeneratorJSON:
    def test_json_report(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        results = {"target_member": "test", "combined_score": 0.9}
        path = rg.generate_json_report(results)
        data = json.loads(path.read_text())
        assert data["combined_score"] == 0.9

    def test_config_file(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        results = {
            "prompt_optimization": {"model": "glm-5.1"},
            "routing_optimization": {"strategy": "hybrid"},
            "retry_optimization": {"fallback": "qwen-max"},
        }
        path = rg.generate_config_file(results)
        data = json.loads(path.read_text())
        assert data["prompt_optimization"]["model"] == "glm-5.1"
        assert "version" in data


class TestReportGeneratorComparison:
    def test_comparison_report(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        baseline = {
            "combined_score": 0.6,
            "total_experiments": 10,
            "total_time": 5.0,
            "detailed_results": {
                "prompt": {"best_score": 0.6, "total_experiments": 10, "total_time": 5.0},
            },
        }
        optimized = {
            "combined_score": 0.9,
            "total_experiments": 20,
            "total_time": 8.0,
            "detailed_results": {
                "prompt": {"best_score": 0.9, "total_experiments": 20, "total_time": 8.0},
            },
        }
        path = rg.generate_comparison_report(baseline, optimized)
        content = path.read_text()
        assert "0.6000" in content
        assert "0.9000" in content
        assert "Prompt" in content or "prompt" in content.lower()

    def test_comparison_zero_baseline(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        baseline = {"combined_score": 0, "total_experiments": 0, "total_time": 0}
        optimized = {"combined_score": 0.5, "total_experiments": 10, "total_time": 3.0}
        path = rg.generate_comparison_report(baseline, optimized)
        content = path.read_text()
        assert "0.5000" in content


class TestReportFormatParams:
    def test_format_params_float_and_other(self, tmp_path):
        from lingminopt.meta_optimizer.report_generator import ReportGenerator

        rg = ReportGenerator(str(tmp_path))
        md = []
        rg._format_params({"score": 0.85, "name": "test"}, md)
        assert any("0.8500" in line for line in md)
        assert any("test" in line for line in md)


class TestLingBusCollector:
    def test_collect_all_stats_missing_members(self, tmp_path):
        from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

        fake_paths = {m: tmp_path / f"{m}" / "crush.db" for m in ["member_a", "member_b"]}
        collector = LingBusCollector(crush_db_paths=fake_paths)
        result = collector.collect_all_stats()
        assert result == {}

    def test_collect_lingbus_messages_missing_db(self, tmp_path):
        from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

        collector = LingBusCollector(
            lingbus_db=tmp_path / "nonexistent.db",
            crush_db_paths={},
        )
        result = collector.collect_lingbus_messages()
        assert result == []

    def test_collect_lingbus_messages_with_data(self, tmp_path):
        from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

        db_path = tmp_path / "lingbus.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE messages (sender TEXT, recipient TEXT, subject TEXT, "
            "body TEXT, timestamp TEXT, channel TEXT)"
        )
        conn.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
            ("lingflow", "all", "test subject", "test body", "2026-05-31", "system"),
        )
        conn.commit()
        conn.close()

        collector = LingBusCollector(
            lingbus_db=db_path,
            crush_db_paths={},
        )
        records = collector.collect_lingbus_messages(limit=10)
        assert len(records) == 1
        assert records[0].agent == "lingflow"
        assert records[0].model == "lingbus"

    def test_collect_lingbus_messages_with_since_filter(self, tmp_path):
        from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

        db_path = tmp_path / "lingbus2.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE messages (sender TEXT, recipient TEXT, subject TEXT, "
            "body TEXT, timestamp TEXT, channel TEXT)"
        )
        conn.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
            ("lingflow", "all", "old", "body", "2026-01-01", "system"),
        )
        conn.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
            ("lingflow", "all", "new", "body", "2026-06-01", "system"),
        )
        conn.commit()
        conn.close()

        collector = LingBusCollector(
            lingbus_db=db_path,
            crush_db_paths={},
        )
        records = collector.collect_lingbus_messages(since="2026-05-01", limit=10)
        assert len(records) == 1
        assert records[0].query == "new"

    def test_to_session_records(self):
        from lingminopt.meta_optimizer.lingbus_collector import (
            LingBusCollector,
            MemberSessionStats,
        )

        stats = {
            "test": MemberSessionStats(
                member="test",
                total_sessions=1,
                total_messages=10,
                avg_messages_per_session=10.0,
                total_assistant_messages=5,
                total_tool_calls=2,
                time_range=(None, None),
                estimated_input_tokens=100,
                estimated_output_tokens=200,
            ),
        }
        collector = LingBusCollector(crush_db_paths={})
        records = collector.to_session_records(stats)
        assert len(records) == 1
        assert records[0].agent == "test"
        assert records[0].input_tokens == 100

    def test_extract_text_various_formats(self):
        from lingminopt.meta_optimizer.lingbus_collector import _extract_text

        assert _extract_text(None) == ""
        assert _extract_text("") == ""
        assert _extract_text("plain text") == "plain text"
        assert _extract_text("not json") == "not json"
        assert _extract_text("42") == "42"

        parts = [{"type": "text", "data": {"text": "hello"}}]
        assert _extract_text(json.dumps(parts)) == "hello"

        parts = [{"type": "text", "data": "direct string"}]
        assert _extract_text(json.dumps(parts)) == "direct string"

        parts = [{"type": "tool_call", "data": {"name": "bash"}}]
        assert _extract_text(json.dumps(parts)) == "bash"

        parts = [{"type": "tool_result", "data": {"content": "output text"}}]
        assert _extract_text(json.dumps(parts)) == "output text"

        parts = [{"type": "tool_result", "data": {"content": "x" * 1000}}]
        result = _extract_text(json.dumps(parts))
        assert len(result) == 500

        parts = [{"type": "unknown", "data": {}}]
        assert _extract_text(json.dumps(parts)) == ""

        parts = [{"type": "text", "data": {"text": "a"}}, {"type": "text", "data": {"text": "b"}}]
        assert _extract_text(json.dumps(parts)) == "a b"

    def test_collect_member_stats_with_corrupt_db(self, tmp_path):
        from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

        fake_db = tmp_path / "bad.db"
        fake_db.write_text("not a database")
        collector = LingBusCollector(crush_db_paths={"bad": fake_db})
        result = collector.collect_member_stats("bad")
        assert result is None

    def test_collect_member_stats_zero_messages(self, tmp_path):
        from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

        fake_db = tmp_path / "empty.db"
        conn = sqlite3.connect(str(fake_db))
        conn.execute("CREATE TABLE sessions (id TEXT)")
        conn.execute("CREATE TABLE messages (role TEXT, parts TEXT, created_at INTEGER, model TEXT, provider TEXT)")
        conn.commit()
        conn.close()

        collector = LingBusCollector(crush_db_paths={"empty": fake_db})
        result = collector.collect_member_stats("empty")
        assert result is not None
        assert result.total_messages == 0
        assert result.estimated_input_tokens == 0
