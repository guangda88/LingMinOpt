"""
Command-line interface for lingminopt
"""

import click
import json
import os
import sys
import warnings
from pathlib import Path

from ..core import MinimalOptimizer, SearchSpace, OptimizationResult
from ..config.config import ExperimentConfig
from .. import __version__
from .templates import (
    _get_fixed_template,
    _get_variable_template,
    _get_readme_template,
    _get_config_template,
)
from .validators import validate_project_name, validate_config_file
from .inbox_cmd import _inbox_read, _inbox_reply
from .meta_optimize import meta_optimize

# Setup logging
logger = None


def setup_logging(level: str = "INFO"):
    """Setup logging for CLI"""
    import logging
    global logger
    logger = logging.getLogger("lingminopt")
    logger.setLevel(getattr(logging, level.upper()))
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)


def _load_search_space(variable, config_data: dict) -> SearchSpace:
    if hasattr(variable, "search_space"):
        return variable.search_space
    search_space = SearchSpace()
    if "search_space" in config_data:
        search_space.add_from_dict(config_data["search_space"])
    return search_space


def _build_experiment_config(config_data: dict, max_experiments: int | None) -> ExperimentConfig:
    return ExperimentConfig(
        max_experiments=max_experiments or config_data.get("optimizer", {}).get("max_experiments", 100),
        improvement_threshold=config_data.get("optimizer", {}).get("improvement_threshold", 0.001),
        time_budget=config_data.get("resources", {}).get("time_budget", 300.0),
        early_stopping_patience=config_data.get("optimizer", {}).get("early_stopping_patience", 10),
        direction=config_data.get("optimizer", {}).get("direction", "minimize"),
    )


def _load_evaluator(variable):
    if hasattr(variable, "run_experiment"):
        return variable.run_experiment
    click.echo("Error: variable.py must define a run_experiment() function")
    sys.exit(1)


@click.group()
@click.version_option(version=__version__)
def cli():
    """Minimal Optimizer - A universal self-optimization framework"""
    pass


@cli.command()
@click.argument("project_name", default="my-optimization")
@click.option(
    "--template",
    type=click.Choice(["ml-optimization", "database-optimization", "game-optimization", "minimal"]),
    default="minimal",
    help="Template to use"
)
@click.option("--force", is_flag=True, help="Overwrite existing directory")
def init(project_name, template, force):
    """Initialize a new optimization project"""
    try:
        project_name = validate_project_name(project_name)

        if os.path.exists(project_name) and not force:
            click.echo(f"Error: Directory '{project_name}' already exists. Use --force to overwrite.")
            sys.exit(1)

        os.makedirs(project_name, exist_ok=True)

        with open(os.path.join(project_name, "fixed.py"), "w") as f:
            f.write(_get_fixed_template(template))

        with open(os.path.join(project_name, "variable.py"), "w") as f:
            f.write(_get_variable_template(template))

        with open(os.path.join(project_name, "README.md"), "w") as f:
            f.write(_get_readme_template(project_name, template))

        with open(os.path.join(project_name, "config.json"), "w") as f:
            json.dump(_get_config_template(template), f, indent=2)

        click.echo(f"✓ Created project '{project_name}' using template '{template}'")
        click.echo("  - Edit variable.py to define your experiment")
        click.echo("  - Run 'lingminopt run' to start optimization")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error creating project: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="config.json",
    help="Configuration file"
)
@click.option("--max-experiments", type=int, help="Override max experiments")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def run(config, max_experiments, verbose):
    """Run optimization"""
    setup_logging("DEBUG" if verbose else "INFO")

    try:
        config_data = validate_config_file(config)

        variable_path = Path(os.getcwd()) / 'variable.py'
        if not variable_path.exists():
            click.echo("Error: variable.py not found in current directory")
            sys.exit(1)

        warnings.warn(
            "Loading user code from variable.py. Only run code from trusted sources.",
            UserWarning,
            stacklevel=2
        )

        sys.path.insert(0, os.getcwd())
        import variable

        search_space = _load_search_space(variable, config_data)
        exp_config = _build_experiment_config(config_data, max_experiments)
        evaluator = _load_evaluator(variable)
        search_strategy = config_data.get("optimizer", {}).get("search_strategy", "random")

        optimizer = MinimalOptimizer(
            evaluate=evaluator,
            search_space=search_space,
            config=exp_config,
            search_strategy=search_strategy,
        )

        result = optimizer.run()

        results_file = config_data.get("output", {}).get("results_file", "results.json")
        result.save(results_file)

        click.echo("\n" + "="*60)
        click.echo("Optimization Complete!")
        click.echo("="*60)
        click.echo(f"Best score: {result.best_score:.6f}")
        click.echo(f"Best params: {result.best_params}")
        click.echo(f"Improvement: {result.improvement:.6f}")
        click.echo(f"Total experiments: {result.total_experiments}")
        click.echo(f"Total time: {result.total_time:.2f}s")
        click.echo(f"\nResults saved to: {results_file}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error running optimization: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option(
    "--results",
    type=click.Path(exists=True),
    default="results.json",
    help="Results file"
)
def report(results):
    """Generate optimization report"""
    result = OptimizationResult.load(results)

    click.echo("\n" + "="*60)
    click.echo("Optimization Report")
    click.echo("="*60)

    click.echo(f"\nBest Score: {result.best_score:.6f}")
    click.echo("Best Parameters:")
    for key, value in result.best_params.items():
        click.echo(f"  {key}: {value}")

    click.echo(f"\nImprovement: {result.improvement:.6f}")
    click.echo(f"Total Experiments: {result.total_experiments}")
    click.echo(f"Total Time: {result.total_time:.2f}s")

    click.echo("\nExperiment History:")
    click.echo(f"{'ID':<5} {'Score':<12} {'Timestamp'}")
    click.echo("-" * 50)
    for exp in result.history:
        click.echo(f"{exp.experiment_id:<5} {exp.score:<12.6f} {exp.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


cli.add_command(meta_optimize)

@cli.command()
@click.option("--agent", default="lingjiyou", help="Agent ID to check messages for")
@click.option("--threads/--no-threads", default=True, help="Show active threads")
@click.option("--unread/--all", default=True, help="Only show unread messages")
@click.option("--reply", default=None, help="Reply to a thread by ID")
@click.option("--message", default=None, help="Message content for reply")
@click.option("--db-url", default=None, help="Database URL (or set LINGMESSAGE_DB_URL)")
def inbox(agent, threads, unread, reply, message, db_url):
    """灵信收件箱 — 查看和回复灵信消息"""
    db = db_url or os.environ.get("LINGMESSAGE_DB_URL")
    if not db:
        click.echo("❌ 请设置环境变量 LINGMESSAGE_DB_URL 或使用 --db-url 参数")
        return

    if reply and message:
        _inbox_reply(db, agent, reply, message)
        return

    _inbox_read(db, agent, threads, unread)


if __name__ == "__main__":
    cli()
