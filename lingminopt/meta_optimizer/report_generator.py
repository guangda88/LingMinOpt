"""
Report Generator - 生成元知识优化报告
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any
import logging
import json

logger = logging.getLogger(__name__)


class ReportGenerator:
    """优化报告生成器"""

    def __init__(self, output_dir: str | Path):
        """
        初始化报告生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_markdown_report(
        self,
        optimization_results: dict[str, Any],
        filename: str = "meta_optimization_report.md",
    ) -> Path:
        """
        生成 Markdown 格式的优化报告

        Args:
            optimization_results: 优化结果字典
            filename: 报告文件名

        Returns:
            报告文件路径
        """
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self._format_markdown(optimization_results))

        logger.info(f"Generated markdown report: {output_path}")

        return output_path

    def generate_json_report(
        self,
        optimization_results: dict[str, Any],
        filename: str = "meta_optimization_report.json",
    ) -> Path:
        """
        生成 JSON 格式的优化报告

        Args:
            optimization_results: 优化结果字典
            filename: 报告文件名

        Returns:
            报告文件路径
        """
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(optimization_results, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated JSON report: {output_path}")

        return output_path

    def generate_config_file(
        self,
        optimization_results: dict[str, Any],
        filename: str = "optimized_config.json",
    ) -> Path:
        """
        生成优化后的配置文件

        Args:
            optimization_results: 优化结果字典
            filename: 配置文件名

        Returns:
            配置文件路径
        """
        output_path = self.output_dir / filename

        # 提取最优参数
        config = {
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "prompt_optimization": {},
            "routing_optimization": {},
            "retry_optimization": {},
        }

        if "prompt_optimization" in optimization_results:
            config["prompt_optimization"] = optimization_results["prompt_optimization"]

        if "routing_optimization" in optimization_results:
            config["routing_optimization"] = optimization_results["routing_optimization"]

        if "retry_optimization" in optimization_results:
            config["retry_optimization"] = optimization_results["retry_optimization"]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated config file: {output_path}")

        return output_path

    def _format_markdown(self, results: dict[str, Any]) -> str:
        """格式化为 Markdown"""
        md = []
        md.append("# 元知识优化报告")
        md.append("")
        md.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")

        # 综合结果
        if "combined_score" in results:
            md.append("## 综合结果")
            md.append("")
            md.append(f"- **综合得分**: {results['combined_score']:.4f}")
            md.append(f"- **总实验次数**: {results.get('total_experiments', 0)}")
            md.append(f"- **总耗时**: {results.get('total_time', 0):.2f} 秒")
            md.append("")

        # 提示词优化
        if "prompt_optimization" in results:
            md.append("## 提示词优化")
            md.append("")
            self._format_params(results["prompt_optimization"], md)
            md.append("")

            if "detailed_results" in results and "prompt" in results["detailed_results"]:
                prompt_detail = results["detailed_results"]["prompt"]
                md.append(f"- **最优得分**: {prompt_detail.get('best_score', 0):.4f}")
                md.append(f"- **实验次数**: {prompt_detail.get('total_experiments', 0)}")
                md.append(f"- **耗时**: {prompt_detail.get('total_time', 0):.2f} 秒")
                md.append("")

        # 路由优化
        if "routing_optimization" in results:
            md.append("## 路由优化")
            md.append("")
            self._format_params(results["routing_optimization"], md)
            md.append("")

            if "detailed_results" in results and "routing" in results["detailed_results"]:
                routing_detail = results["detailed_results"]["routing"]
                md.append(f"- **最优得分**: {routing_detail.get('best_score', 0):.4f}")
                md.append(f"- **实验次数**: {routing_detail.get('total_experiments', 0)}")
                md.append(f"- **耗时**: {routing_detail.get('total_time', 0):.2f} 秒")
                md.append("")

        # 重试优化
        if "retry_optimization" in results:
            md.append("## 重试优化")
            md.append("")
            self._format_params(results["retry_optimization"], md)
            md.append("")

            if "detailed_results" in results and "retry" in results["detailed_results"]:
                retry_detail = results["detailed_results"]["retry"]
                md.append(f"- **最优得分**: {retry_detail.get('best_score', 0):.4f}")
                md.append(f"- **实验次数**: {retry_detail.get('total_experiments', 0)}")
                md.append(f"- **耗时**: {retry_detail.get('total_time', 0):.2f} 秒")
                md.append("")

        # 建议
        md.append("## 优化建议")
        md.append("")
        md.append("1. **应用配置**: 将上述最优参数应用到 LingClaude 配置文件")
        md.append("2. **监控效果**: 观察 Token 使用量、响应时间、成功率的变化")
        md.append("3. **定期优化**: 每周或每月重新运行优化以适应业务变化")
        md.append("4. **A/B 测试**: 在生产环境中进行 A/B 测试验证效果")
        md.append("")

        md.append("---")
        md.append("")
        md.append("*由 LingMinOpt (灵极优) 自动生成*")

        return "\n".join(md)

    def _format_params(self, params: dict[str, Any], md: list[str]) -> None:
        """格式化参数列表"""
        for key, value in params.items():
            if isinstance(value, float):
                md.append(f"- **{key}**: {value:.4f}")
            else:
                md.append(f"- **{key}**: {value}")

    def generate_comparison_report(
        self,
        baseline_results: dict[str, Any],
        optimized_results: dict[str, Any],
        filename: str = "comparison_report.md",
    ) -> Path:
        """
        生成对比报告（优化前 vs 优化后）

        Args:
            baseline_results: 基准结果
            optimized_results: 优化后结果
            filename: 报告文件名

        Returns:
            报告文件路径
        """
        output_path = self.output_dir / filename

        md = []
        md.append("# 优化效果对比报告")
        md.append("")
        md.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")

        md.append("## 综合得分对比")
        md.append("")

        baseline_score = baseline_results.get("combined_score", 0)
        optimized_score = optimized_results.get("combined_score", 0)
        improvement = optimized_score - baseline_score
        improvement_percent = (improvement / baseline_score * 100) if baseline_score > 0 else 0

        md.append("| 指标 | 优化前 | 优化后 | 提升 |")
        md.append("|------|--------|--------|------|")
        md.append(f"| 综合得分 | {baseline_score:.4f} | {optimized_score:.4f} | {improvement:+.4f} ({improvement_percent:+.1f}%) |")
        md.append("")

        # 实验次数和耗时
        baseline_experiments = baseline_results.get("total_experiments", 0)
        optimized_experiments = optimized_results.get("total_experiments", 0)
        baseline_time = baseline_results.get("total_time", 0)
        optimized_time = optimized_results.get("total_time", 0)

        md.append("## 资源消耗对比")
        md.append("")
        md.append("| 指标 | 优化前 | 优化后 |")
        md.append("|------|--------|--------|")
        md.append(f"| 总实验次数 | {baseline_experiments} | {optimized_experiments} |")
        md.append(f"| 总耗时 (秒) | {baseline_time:.2f} | {optimized_time:.2f} |")
        md.append("")

        # 详细对比
        md.append("## 各项优化对比")
        md.append("")

        for task in ["prompt", "routing", "retry"]:
            if task in baseline_results.get("detailed_results", {}) and task in optimized_results.get("detailed_results", {}):
                baseline_task = baseline_results["detailed_results"][task]
                optimized_task = optimized_results["detailed_results"][task]

                baseline_task_score = baseline_task.get("best_score", 0)
                optimized_task_score = optimized_task.get("best_score", 0)
                task_improvement = optimized_task_score - baseline_task_score

                md.append(f"### {task.capitalize()} 优化")
                md.append("")
                md.append("| 指标 | 优化前 | 优化后 | 提升 |")
                md.append("|------|--------|--------|------|")
                md.append(f"| 得分 | {baseline_task_score:.4f} | {optimized_task_score:.4f} | {task_improvement:+.4f} |")
                md.append(f"| 实验次数 | {baseline_task.get('total_experiments', 0)} | {optimized_task.get('total_experiments', 0)} |")
                md.append(f"| 耗时 (秒) | {baseline_task.get('total_time', 0):.2f} | {optimized_task.get('total_time', 0):.2f} |")
                md.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))

        logger.info(f"Generated comparison report: {output_path}")

        return output_path
