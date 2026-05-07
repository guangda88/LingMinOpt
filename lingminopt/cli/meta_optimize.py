"""Meta-optimization CLI command."""

import logging
import sys

import click


def _setup_logging(level: str = "INFO"):
    """Setup logging for CLI"""
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
    help="Path to LingClaude sessions directory",
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
@click.option("--output", type=click.Path(), default="meta_opt_results", help="Output directory for reports")
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
