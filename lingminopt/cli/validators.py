"""
Validation helpers for lingminopt CLI.
"""

import json
import re
from pathlib import Path


def validate_project_name(name: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(
            "Invalid project name. Use only letters, numbers, underscores, and hyphens."
        )
    if name in [".", ".."] or "/" in name or "\\" in name:
        raise ValueError("Path traversal not allowed")
    if len(name) > 100:
        raise ValueError("Project name too long (max 100 characters)")
    return name


def _validate_output_config(output_config: dict) -> None:
    if "results_file" in output_config:
        results_file = output_config["results_file"]
        if ".." in results_file or Path(results_file).is_absolute():
            raise ValueError("Invalid results_file: path traversal not allowed")
        if not results_file.endswith(".json"):
            raise ValueError("results_file must be a JSON file")


def _validate_optimizer_config(optimizer_config: dict) -> None:
    if "direction" in optimizer_config:
        if optimizer_config["direction"] not in ["minimize", "maximize"]:
            raise ValueError("direction must be 'minimize' or 'maximize'")


def _validate_filepath(filepath: str) -> str:
    if ".." in filepath:
        raise ValueError("Invalid filepath: path traversal not allowed")
    return filepath


def validate_config_file(filepath: str) -> dict:
    _validate_filepath(filepath)
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    except (OSError, PermissionError) as e:
        raise ValueError(f"Error reading config file: {e}")

    if not isinstance(data, dict):
        raise ValueError("Config must be a JSON object")

    _validate_output_config(data.get("output", {}))
    _validate_optimizer_config(data.get("optimizer", {}))

    return data
