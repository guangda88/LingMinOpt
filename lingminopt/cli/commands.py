"""
Command-line interface for minopt
"""

import click
import json
import os
import sys
from pathlib import Path
from typing import Optional

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
    click.echo(f"  - Edit variable.py to define your experiment")
    click.echo(f"  - Run 'minopt run' to start optimization")


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

    # Load config
    with open(config, "r") as f:
        config_data = json.load(f)

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
    click.echo(f"Best Parameters:")
    for key, value in result.best_params.items():
        click.echo(f"  {key}: {value}")

    click.echo(f"\nImprovement: {result.improvement:.6f}")
    click.echo(f"Total Experiments: {result.total_experiments}")
    click.echo(f"Total Time: {result.total_time:.2f}s")

    click.echo(f"\nExperiment History:")
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

from minopt import SearchSpace

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

from minopt import SearchSpace
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
2. Run optimization: `minopt run`
3. View results: `minopt report`

## Configuration

Edit `config.json` to adjust optimization settings:
- max_experiments: Maximum number of experiments
- search_strategy: Strategy to use (random, grid, bayesian, annealing)
- time_budget: Time per experiment

## Results

Results are saved to `results.json` by default.

## Template

This project was created using the '{template}' template.

For more information, visit: https://github.com/yourusername/minopt
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


if __name__ == "__main__":
    cli()
