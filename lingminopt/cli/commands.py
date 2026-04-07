"""
Command-line interface for lingminopt
"""

import re
import click
import json
import os
import sys
import warnings
from pathlib import Path

from ..core import MinimalOptimizer, SearchSpace, OptimizationResult
from ..config.config import ExperimentConfig

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


def validate_project_name(name: str) -> str:
    """
    Validate project name to prevent path traversal.

    Args:
        name: Project name to validate

    Returns:
        Validated project name

    Raises:
        ValueError: If name is invalid
    """
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError(
            "Invalid project name. Use only letters, numbers, underscores, and hyphens."
        )
    if name in ['.', '..'] or '/' in name or '\\' in name:
        raise ValueError("Path traversal not allowed")
    if len(name) > 100:
        raise ValueError("Project name too long (max 100 characters)")
    return name


def validate_config_file(filepath: str) -> dict:
    """
    Safely load and validate config file.

    Args:
        filepath: Path to config file

    Returns:
        Parsed config dictionary

    Raises:
        ValueError: If config is invalid
    """
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        raise ValueError(f"Error reading config file: {e}")

    # Validate config structure
    if not isinstance(data, dict):
        raise ValueError("Config must be a JSON object")

    # Validate output file path to prevent path traversal
    output_config = data.get("output", {})
    if "results_file" in output_config:
        results_file = output_config["results_file"]
        if '..' in results_file or results_file.startswith('/'):
            raise ValueError("Invalid results_file: path traversal not allowed")
        if not results_file.endswith('.json'):
            raise ValueError("results_file must be a JSON file")

    # Validate optimizer config
    optimizer_config = data.get("optimizer", {})
    if "direction" in optimizer_config:
        if optimizer_config["direction"] not in ["minimize", "maximize"]:
            raise ValueError("direction must be 'minimize' or 'maximize'")

    return data


@click.group()
@click.version_option(version="0.1.0")
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
        # Validate project name
        project_name = validate_project_name(project_name)

        # Check if directory exists
        if os.path.exists(project_name) and not force:
            click.echo(f"Error: Directory '{project_name}' already exists. Use --force to overwrite.")
            sys.exit(1)

        # Create project directory
        os.makedirs(project_name, exist_ok=True)

        # Create fixed.py
        fixed_content = _get_fixed_template(template)
        with open(os.path.join(project_name, "fixed.py"), "w") as f:
            f.write(fixed_content)

        # Create variable.py
        variable_content = _get_variable_template(template)
        with open(os.path.join(project_name, "variable.py"), "w") as f:
            f.write(variable_content)

        # Create README.md
        readme_content = _get_readme_template(project_name, template)
        with open(os.path.join(project_name, "README.md"), "w") as f:
            f.write(readme_content)

        # Create config.json
        config_content = _get_config_template(template)
        with open(os.path.join(project_name, "config.json"), "w") as f:
            json.dump(config_content, f, indent=2)

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
        # Load and validate config
        config_data = validate_config_file(config)

        # Check if variable.py exists
        variable_path = Path(os.getcwd()) / 'variable.py'
        if not variable_path.exists():
            click.echo("Error: variable.py not found in current directory")
            sys.exit(1)

        # Warn about dynamic import
        warnings.warn(
            "Loading user code from variable.py. Only run code from trusted sources.",
            UserWarning,
            stacklevel=2
        )

        # Import variable.py (the experiment definition)
        sys.path.insert(0, os.getcwd())
        import variable

        # Create search space
        search_space = SearchSpace()
        if hasattr(variable, "search_space"):
            search_space = variable.search_space
        else:
            # Try to build from config
            if "search_space" in config_data:
                search_space.add_from_dict(config_data["search_space"])

        # Create config
        exp_config = ExperimentConfig(
            max_experiments=max_experiments or config_data.get("optimizer", {}).get("max_experiments", 100),
            improvement_threshold=config_data.get("optimizer", {}).get("improvement_threshold", 0.001),
            time_budget=config_data.get("resources", {}).get("time_budget", 300.0),
            early_stopping_patience=config_data.get("optimizer", {}).get("early_stopping_patience", 10),
            direction=config_data.get("optimizer", {}).get("direction", "minimize"),
        )

        # Create optimizer
        if hasattr(variable, "run_experiment"):
            evaluator = variable.run_experiment
        else:
            click.echo("Error: variable.py must define a run_experiment() function")
            sys.exit(1)

        search_strategy = config_data.get("optimizer", {}).get("search_strategy", "random")

        optimizer = MinimalOptimizer(
            evaluate=evaluator,
            search_space=search_space,
            config=exp_config,
            search_strategy=search_strategy,
        )

        # Run optimization
        result = optimizer.run()

        # Save results
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


def _get_fixed_template(template: str) -> str:
    """Get fixed.py template content"""
    if template == "minimal":
        return '''"""
Fixed constraints (DO NOT MODIFY)

This file contains the fixed constraints and environment configuration
for your optimization experiments.
"""

# Resource limits
TIME_BUDGET = 300  # seconds per experiment
MEMORY_LIMIT = 8   # MB (optional)
MAX_COST = 100    # Budget limit (optional)

# Environment configuration
ENV_CONFIG = {
    "device": "cpu",
    "random_seed": 42,
}

def get_environment():
    """Get environment configuration"""
    return ENV_CONFIG
'''
    elif template == "ml-optimization":
        return '''"""
Fixed constraints for ML optimization (DO NOT MODIFY)
"""

import os

# Resource limits
TIME_BUDGET = 300  # 5 minutes per experiment
DEVICE = "cuda" if os.path.exists("/dev/nvidia0") else "cpu"

# Data paths (example)
DATA_DIR = "./data"
TRAIN_DATA = f"{DATA_DIR}/train.csv"
VAL_DATA = f"{DATA_DIR}/val.csv"

def load_data():
    """Load training and validation data (DO NOT MODIFY)"""
    # Implement your data loading here
    train = []
    val = []
    return train, val

def evaluate_model(model, val_data):
    """Evaluate model and return metrics (DO NOT MODIFY)"""
    # Implement your evaluation here
    loss = model.evaluate(val_data)
    return {"loss": loss, "bpc": loss / 2.3}  # Example metric
'''
    else:
        return _get_fixed_template("minimal")


def _get_variable_template(template: str) -> str:
    """Get variable.py template content"""
    if template == "minimal":
        return '''"""
Variable parameters and experiment logic (MODIFY THIS)

This file defines what the AI can modify during optimization.
"""

from lingminopt import SearchSpace

# Define search space
search_space = SearchSpace()

# Example: Add discrete parameters
search_space.add_discrete("param1", ["option_a", "option_b", "option_c"])

# Example: Add continuous parameters
search_space.add_continuous("param2", 0.0, 1.0)
search_space.add_continuous("param3", -10.0, 10.0)

def run_experiment(params):
    """
    Run a single experiment with given parameters.

    Args:
        params: Dictionary of parameters from search space

    Returns:
        float: Evaluation score (lower is better by default)
    """
    # 1. Extract parameters
    param1 = params["param1"]
    param2 = params["param2"]
    param3 = params["param3"]

    # 2. Run your experiment here
    # Example: simple quadratic function
    score = param2**2 + param3**2

    # 3. Return score
    return score
'''
    elif template == "ml-optimization":
        return '''"""
Variable parameters for ML optimization (MODIFY THIS)
"""

from lingminopt import SearchSpace
import fixed

# Define search space
search_space = SearchSpace()

# Model architecture
search_space.add_discrete("model_type", ["small", "medium", "large"])
search_space.add_discrete("activation", ["relu", "gelu"])

# Training hyperparameters
search_space.add_continuous("learning_rate", 1e-5, 1e-2)
search_space.add_continuous("dropout", 0.0, 0.5)
search_space.add_discrete("optimizer", ["adam", "adamw"])

def run_experiment(params):
    """
    Run ML training experiment.

    Returns:
        float: Validation BPC (lower is better)
    """
    # 1. Load data
    train_data, val_data = fixed.load_data()

    # 2. Build model based on params
    model = build_model(params)

    # 3. Train model (within TIME_BUDGET)
    train_model(model, train_data, val_data, params)

    # 4. Evaluate model
    metrics = fixed.evaluate_model(model, val_data)

    # 5. Return BPC
    return metrics["bpc"]

# Helper functions (you need to implement)
def build_model(params):
    """Build model based on parameters"""
    raise NotImplementedError("Implement build_model()")

def train_model(model, train_data, val_data, params):
    """Train model"""
    raise NotImplementedError("Implement train_model()")
'''
    else:
        return _get_variable_template("minimal")


def _get_readme_template(project_name: str, template: str) -> str:
    """Get README.md template content"""
    return f'''# {project_name}

Optimization project using Minimal Optimizer (MinOpt).

## Getting Started

1. Edit `variable.py` to define your experiment
2. Run optimization: `lingminopt run`
3. View results: `lingminopt report`

## Configuration

Edit `config.json` to adjust optimization settings:
- max_experiments: Maximum number of experiments
- search_strategy: Strategy to use (random, grid, bayesian, annealing)
- time_budget: Time per experiment

## Results

Results are saved to `results.json` by default.

## Template

This project was created using the '{template}' template.

For more information, visit: https://github.com/yourusername/lingminopt
'''


def _get_config_template(template: str) -> dict:
    """Get config.json template content"""
    return {
        "optimizer": {
            "search_strategy": "random",
            "max_experiments": 100,
            "early_stopping_patience": 10,
            "improvement_threshold": 0.001,
            "direction": "minimize"
        },
        "search_space": {
            "discrete": {},
            "continuous": {}
        },
        "resources": {
            "time_budget": 300,
            "parallel_jobs": 1
        },
        "output": {
            "results_file": "results.json",
            "log_level": "INFO"
        }
    }


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


def _inbox_read(db_url: str, agent_id: str, show_threads: bool, unread_only: bool):
    """Read inbox messages from lingmessage database"""
    import asyncio

    async def _read():
        import asyncpg

        conn = await asyncpg.connect(db_url)
        try:
            if show_threads:
                rows = await conn.fetch(
                    "SELECT t.id, t.topic, t.status, t.priority, t.current_round, "
                    "  (SELECT COUNT(*) FROM lingmessage_messages m WHERE m.thread_id = t.id) as msg_count "
                    "FROM lingmessage_threads t "
                    "WHERE t.status = 'active' "
                    "ORDER BY t.priority = 'high' DESC, t.created_at DESC "
                    "LIMIT 20"
                )
                if not rows:
                    click.echo("📭 没有活跃的议事厅线程")
                    return
                click.echo(f"\n📋 议事厅线程 (共{len(rows)}个)")
                click.echo("=" * 70)
                for r in rows:
                    flag = "🔴" if r["priority"] == "high" else "🟢"
                    click.echo(f"  {flag} #{r['id']} [{r['status']}] {r['topic']} ({r['msg_count']}条消息)")

            rows = await conn.fetch(
                "SELECT m.id, m.thread_id, t.topic, a.display_name, "
                "  LEFT(m.content, 200) as preview, m.message_type, m.created_at "
                "FROM lingmessage_messages m "
                "JOIN lingmessage_threads t ON t.id = m.thread_id "
                "JOIN lingmessage_agents a ON a.agent_id = m.agent_id "
                "WHERE m.agent_id != $1 "
                "ORDER BY m.created_at DESC LIMIT 10",
                agent_id
            )
            if rows:
                click.echo(f"\n📬 最新消息 (共{len(rows)}条)")
                click.echo("=" * 70)
                for r in rows:
                    msg_type = r["message_type"]
                    tag = "📌" if msg_type == "task_assignment" else ("🔔" if msg_type == "direct_mention" else "💬")
                    preview = (r["preview"] or "")[:60]
                    click.echo(f"  {tag} [线程#{r['thread_id']}] {r['display_name']} → {preview}...")
                    click.echo(f"     ({r['created_at']})  回复: lingminopt inbox --reply {r['thread_id']} --message '你的回复'")
        finally:
            await conn.close()

    asyncio.run(_read())


def _inbox_reply(db_url: str, agent_id: str, thread_id: str, content: str):
    """Reply to a lingmessage thread"""
    import asyncio

    async def _reply():
        import asyncpg

        conn = await asyncpg.connect(db_url)
        try:
            await conn.execute(
                "INSERT INTO lingmessage_messages (thread_id, agent_id, round_number, content, message_type) "
                "SELECT $1::integer, $2, "
                "  COALESCE(MAX(round_number), 0) + 1, $3, 'response' "
                "FROM lingmessage_messages WHERE thread_id = $1::integer",
                int(thread_id), agent_id, content
            )
            click.echo(f"✅ 回复已发送到线程 #{thread_id}")
        finally:
            await conn.close()

    try:
        asyncio.run(_reply())
    except Exception as e:
        click.echo(f"❌ 发送失败: {e}")


if __name__ == "__main__":
    cli()
