"""Meta-optimization CLI command."""

import json as _json
import logging
import sys
from pathlib import Path

import click


def _setup_logging(level: str = "INFO"):
    log = logging.getLogger("lingminopt")
    log.setLevel(getattr(logging, level.upper()))
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    log.addHandler(handler)


@click.command("meta-optimize")
@click.option(
    "--sessions-dir",
    type=click.Path(exists=True),
    required=True,
    help="Path to lingclaude sessions directory",
)
@click.option(
    "--strategy",
    type=click.Choice(["random", "grid", "bayesian", "annealing", "tpe"]),
    default="bayesian",
    help="Search strategy for optimization",
)
@click.option("--experiments", type=int, default=50, help="Max experiments per optimization task")
@click.option("--time-budget", type=int, default=300, help="Time budget per task (seconds)")
@click.option("--seed", type=int, default=None, help="Random seed for reproducibility")
@click.option(
    "--output", type=click.Path(), default="meta_opt_results", help="Output directory for reports"
)
def meta_optimize(sessions_dir, strategy, experiments, time_budget, seed, output):
    """运行元知识优化（提示词/路由/重试）"""
    _setup_logging("INFO")

    try:
        from lingminopt.meta_optimizer import MetaOptimizer, ReportGenerator

        optimizer = MetaOptimizer(sessions_dir)

        click.echo("正在运行元知识优化...")
        click.echo(f"  会话目录: {sessions_dir}")
        click.echo(f"  搜索策略: {strategy}")
        click.echo(f"  每任务实验数: {experiments}")

        results = optimizer.optimize_all(
            max_experiments_per_task=experiments,
            time_budget_per_task=time_budget,
            search_strategy=strategy,
            random_seed=seed,
        )

        generator = ReportGenerator(output)
        md_path = generator.generate_markdown_report(results)
        json_path = generator.generate_json_report(results)
        config_path = generator.generate_config_file(results)

        click.echo("\n" + "=" * 60)
        click.echo("元知识优化完成!")
        click.echo("=" * 60)
        click.echo(f"综合得分: {results['combined_score']:.4f}")

        for task_name in ["prompt", "routing", "retry"]:
            key = f"{task_name}_optimization"
            if key in results:
                click.echo(f"\n{task_name.capitalize()} 最优参数:")
                for k, v in results[key].items():
                    click.echo(f"  {k}: {v}")

        click.echo("\n报告已保存:")
        click.echo(f"  Markdown: {md_path}")
        click.echo(f"  JSON: {json_path}")
        click.echo(f"  配置: {config_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.command("mko")
@click.option(
    "--type",
    "opt_type",
    type=click.Choice(["ranking", "prompt", "routing", "retry", "all"]),
    default="all",
    help="优化类型",
)
@click.option("--trials", type=int, default=30, help="优化尝试次数")
@click.option("--output", type=click.Path(), default="data/mko", help="输出目录")
def mko(opt_type, trials, output):
    """灵族元知识优化 — 基于真实crush.db数据优化灵族token消耗

    \b
    lingminopt mko              # 全部优化
    lingminopt mko --type ranking  # 仅token排名
    lingminopt mko --type prompt   # 仅提示词优化
    """
    _setup_logging("INFO")

    try:
        from lingminopt.core.optimizer import MinimalOptimizer
        from lingminopt.meta_optimizer.evaluators import (
            PromptEvaluator,
            RetryEvaluator,
            RoutingEvaluator,
        )
        from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector
        from lingminopt.meta_optimizer.report_generator import ReportGenerator
        from lingminopt.meta_optimizer.search_spaces import (
            get_prompt_optimization_space,
            get_retry_optimization_space,
            get_routing_optimization_space,
        )

        collector = LingBusCollector()

        if opt_type == "ranking":
            stats = collector.collect_all_stats()
            ranked = sorted(
                stats.values(),
                key=lambda s: s.estimated_input_tokens + s.estimated_output_tokens,
                reverse=True,
            )
            total = sum(s.estimated_input_tokens + s.estimated_output_tokens for s in ranked)
            click.echo("\n=== 灵族Token消耗排名 ===")
            for s in ranked:
                t = s.estimated_input_tokens + s.estimated_output_tokens
                pct = t / max(total, 1) * 100
                ratio = s.estimated_output_tokens / max(s.estimated_input_tokens, 1)
                click.echo(
                    f"  {s.member:<16s} {t:>10,} tokens ({pct:5.1f}%) out/in={ratio:.1f}x tools={s.total_tool_calls:,}"
                )
            click.echo(f"  TOTAL: {total:,} tokens across {len(ranked)} members")
            return

        records = collector.collect_lingbus_messages(limit=500)
        if not records:
            click.echo("No LingBus data available")
            sys.exit(1)

        session_data = [
            {
                "query": r.query,
                "model": r.model,
                "agent": r.agent,
                "total_tokens": r.input_tokens + r.output_tokens,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "success": r.success,
                "quality_score": 0.85,
            }
            for r in records
        ]

        from lingminopt.config.config import ExperimentConfig

        results = {"target_member": "灵族"}
        import datetime as _dt

        results["generated_at"] = _dt.datetime.now().isoformat()

        task_map = {
            "prompt": (get_prompt_optimization_space, PromptEvaluator),
            "routing": (get_routing_optimization_space, RoutingEvaluator),
            "retry": (get_retry_optimization_space, RetryEvaluator),
        }

        if opt_type == "all":
            tasks = list(task_map.keys())
        else:
            tasks = [opt_type]

        for name in tasks:
            space_fn, eval_cls = task_map[name]
            space = space_fn()
            evaluator = eval_cls(session_data)
            click.echo(f"\n=== {name.capitalize()}优化 ({trials} trials) ===")
            config = ExperimentConfig(max_experiments=trials, direction="maximize")
            opt = MinimalOptimizer(
                evaluate=evaluator.evaluate,
                search_space=space,
                config=config,
                search_strategy="bayesian",
            )
            result = opt.run()
            click.echo(f"  Best score: {result.best_score:.4f}")
            click.echo(
                f"  Best params: {_json.dumps(result.best_params, indent=4, ensure_ascii=False)}"
            )
            results[f"{name}_optimization"] = result.best_params

        member_stats = collector.collect_all_stats() if opt_type == "all" else None
        out_dir = Path(output)
        gen = ReportGenerator(out_dir)
        md_path = gen.generate_markdown_report(results, member_stats=member_stats)
        json_path = gen.generate_json_report(results)
        config_path = gen.generate_config_file(results)

        click.echo(f"\n报告已保存: {md_path}")
        click.echo(f"JSON: {json_path}")
        click.echo(f"配置: {config_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if "--verbose" in sys.argv:
            import traceback

            traceback.print_exc()
        sys.exit(1)
