"""
Template generators for lingminopt CLI init command.
"""


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

Optimization project using LingMinOpt (灵极优).

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
