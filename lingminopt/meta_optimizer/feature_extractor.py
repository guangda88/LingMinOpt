"""
Feature Extractor - 从会话记录中提取特征用于优化
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """意图类型"""
    CODE_GENERATION = "code_generation"
    CODE_REFACTORING = "code_refactoring"
    BUG_FIXING = "bug_fixing"
    CODE_REVIEW = "code_review"
    ARCHITECTURE_DESIGN = "architecture_design"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    GENERAL_CHAT = "general_chat"


class TaskComplexity(str, Enum):
    """任务复杂度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class TaskFeatures:
    """任务特征"""
    # 基础信息
    session_id: str
    query: str
    query_length: int

    # 意图和复杂度
    intent: IntentType
    complexity: TaskComplexity

    # Token 相关
    input_tokens: int
    output_tokens: int
    total_tokens: int

    # 性能指标
    latency_ms: float
    success: bool

    # 资源使用
    model: str
    agent: str | None

    # 推断特征
    code_related: bool
    has_file_operations: bool
    has_test_operations: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskFeatures:
        """从字典创建 TaskFeatures"""
        query = data.get("query", "")

        # 简单推断意图
        intent = cls._infer_intent(query)

        # 简单推断复杂度
        complexity = cls._infer_complexity(query)

        # 推断特征
        code_related = cls._is_code_related(query)
        has_file_operations = cls._has_file_operations(query)
        has_test_operations = cls._has_test_operations(query)

        return cls(
            session_id=data.get("session_id", ""),
            query=query,
            query_length=len(query),
            intent=intent,
            complexity=complexity,
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            latency_ms=data.get("latency_ms", 0.0),
            success=data.get("success", True),
            model=data.get("model", ""),
            agent=data.get("agent"),
            code_related=code_related,
            has_file_operations=has_file_operations,
            has_test_operations=has_test_operations,
        )

    @staticmethod
    def _infer_intent(query: str) -> IntentType:
        """简单推断意图"""
        query_lower = query.lower()

        # 关键词映射
        intent_keywords = {
            IntentType.CODE_GENERATION: [
                "写", "实现", "创建", "生成", "添加", "build", "create", "generate", "implement", "write"
            ],
            IntentType.CODE_REFACTORING: [
                "重构", "优化", "改进", "refactor", "optimize", "improve", "restructure"
            ],
            IntentType.BUG_FIXING: [
                "修复", "解决", "bug", "错误", "异常", "fix", "debug", "error", "exception"
            ],
            IntentType.CODE_REVIEW: [
                "审查", "review", "检查", "检查代码", "代码审查"
            ],
            IntentType.ARCHITECTURE_DESIGN: [
                "设计", "架构", "design", "architecture", "structure"
            ],
            IntentType.TESTING: [
                "测试", "test", "单元测试", "集成测试"
            ],
            IntentType.DOCUMENTATION: [
                "文档", "document", "说明", "注释"
            ],
        }

        # 计算匹配分数
        scores: dict[IntentType, int] = {intent: 0 for intent in IntentType}
        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[intent] += 1

        # 返回得分最高的意图
        max_intent = max(scores, key=scores.get)
        if scores[max_intent] == 0:
            return IntentType.GENERAL_CHAT

        return max_intent

    @staticmethod
    def _infer_complexity(query: str) -> TaskComplexity:
        """简单推断任务复杂度"""
        # 基于查询长度和关键词推断
        length = len(query)

        if length < 100:
            return TaskComplexity.LOW
        elif length < 300:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.HIGH

    @staticmethod
    def _is_code_related(query: str) -> bool:
        """判断是否与代码相关"""
        code_keywords = [
            "代码", "函数", "类", "模块", "变量", "参数",
            "code", "function", "class", "module", "variable", "parameter",
            "import", "def ", "class ", "self.", "return",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in code_keywords)

    @staticmethod
    def _has_file_operations(query: str) -> bool:
        """判断是否涉及文件操作"""
        file_keywords = [
            "文件", "读取", "写入", "删除", "创建",
            "file", "read", "write", "delete", "create", "save",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in file_keywords)

    @staticmethod
    def _has_test_operations(query: str) -> bool:
        """判断是否涉及测试操作"""
        test_keywords = [
            "测试", "单元测试", "集成测试", "test", "unit test", "integration test", "pytest"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in test_keywords)


class FeatureExtractor:
    """特征提取器"""

    def __init__(self):
        self._cache: dict[str, TaskFeatures] = {}

    def extract_features(
        self,
        session_records: list[dict[str, Any]],
        use_cache: bool = True,
    ) -> list[TaskFeatures]:
        """
        从会话记录中提取特征

        Args:
            session_records: 会话记录字典列表
            use_cache: 是否使用缓存

        Returns:
            TaskFeatures 列表
        """
        features_list: list[TaskFeatures] = []

        for record in session_records:
            session_id = record.get("session_id", "")

            if use_cache and session_id in self._cache:
                features_list.append(self._cache[session_id])
            else:
                features = TaskFeatures.from_dict(record)

                if use_cache:
                    self._cache[session_id] = features

                features_list.append(features)

        logger.info(f"Extracted features for {len(features_list)} records")

        return features_list

    def extract_features_by_intent(
        self,
        session_records: list[dict[str, Any]],
        intent: IntentType,
    ) -> list[TaskFeatures]:
        """
        提取特定意图的特征

        Args:
            session_records: 会话记录字典列表
            intent: 目标意图

        Returns:
            特定意图的 TaskFeatures 列表
        """
        all_features = self.extract_features(session_records)

        return [f for f in all_features if f.intent == intent]

    def get_intent_distribution(
        self,
        session_records: list[dict[str, Any]],
    ) -> dict[IntentType, int]:
        """
        获取意图分布

        Args:
            session_records: 会话记录字典列表

        Returns:
            意图分布字典
        """
        features_list = self.extract_features(session_records)

        distribution: dict[IntentType, int] = {intent: 0 for intent in IntentType}
        for features in features_list:
            distribution[features.intent] += 1

        return distribution

    def get_complexity_distribution(
        self,
        session_records: list[dict[str, Any]],
    ) -> dict[TaskComplexity, int]:
        """
        获取复杂度分布

        Args:
            session_records: 会话记录字典列表

        Returns:
            复杂度分布字典
        """
        features_list = self.extract_features(session_records)

        distribution: dict[TaskComplexity, int] = {comp: 0 for comp in TaskComplexity}
        for features in features_list:
            distribution[features.complexity] += 1

        return distribution

    def get_token_statistics(
        self,
        session_records: list[dict[str, Any]],
    ) -> dict[str, float]:
        """
        获取 Token 统计信息

        Args:
            session_records: 会话记录字典列表

        Returns:
            Token 统计字典
        """
        features_list = self.extract_features(session_records)

        if not features_list:
            return {
                "avg_input_tokens": 0.0,
                "avg_output_tokens": 0.0,
                "avg_total_tokens": 0.0,
                "max_total_tokens": 0,
                "min_total_tokens": 0,
            }

        total_tokens = [f.total_tokens for f in features_list]
        input_tokens = [f.input_tokens for f in features_list]
        output_tokens = [f.output_tokens for f in features_list]

        return {
            "avg_input_tokens": sum(input_tokens) / len(input_tokens),
            "avg_output_tokens": sum(output_tokens) / len(output_tokens),
            "avg_total_tokens": sum(total_tokens) / len(total_tokens),
            "max_total_tokens": max(total_tokens),
            "min_total_tokens": min(total_tokens),
        }
