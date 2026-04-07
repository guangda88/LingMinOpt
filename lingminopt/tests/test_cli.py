"""
CLI tests for lingminopt
"""

import json
import os

import pytest
from click.testing import CliRunner

from lingminopt.cli.commands import (
    cli,
    validate_project_name,
    validate_config_file,
)


class TestValidateProjectName:
    def test_valid_simple(self):
        assert validate_project_name("my-project") == "my-project"

    def test_valid_with_underscores(self):
        assert validate_project_name("my_project") == "my_project"

    def test_valid_alphanumeric(self):
        assert validate_project_name("project123") == "project123"

    def test_invalid_dot_dot(self):
        with pytest.raises(ValueError):
            validate_project_name("..")

    def test_invalid_slash(self):
        with pytest.raises(ValueError, match="Invalid project name"):
            validate_project_name("../etc/passwd")

    def test_invalid_backslash(self):
        with pytest.raises(ValueError, match="Invalid project name"):
            validate_project_name("foo\\bar")

    def test_invalid_special_chars(self):
        with pytest.raises(ValueError, match="Invalid project name"):
            validate_project_name("project;rm -rf")

    def test_invalid_too_long(self):
        with pytest.raises(ValueError, match="too long"):
            validate_project_name("a" * 101)

    def test_invalid_dot(self):
        with pytest.raises(ValueError):
            validate_project_name(".")


class TestValidateConfigFile:
    def test_valid_config(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "optimizer": {"direction": "minimize", "max_experiments": 50},
            "output": {"results_file": "results.json"},
        }))
        data = validate_config_file(str(config_file))
        assert data["optimizer"]["direction"] == "minimize"

    def test_invalid_json(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json}")
        with pytest.raises(ValueError, match="Invalid JSON"):
            validate_config_file(str(config_file))

    def test_nonexistent_file(self):
        with pytest.raises(ValueError, match="Error reading"):
            validate_config_file("/nonexistent/path/config.json")

    def test_path_traversal_results_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "output": {"results_file": "../../../tmp/evil.json"},
        }))
        with pytest.raises(ValueError, match="path traversal"):
            validate_config_file(str(config_file))

    def test_absolute_path_results_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "output": {"results_file": "/tmp/results.json"},
        }))
        with pytest.raises(ValueError, match="path traversal"):
            validate_config_file(str(config_file))

    def test_non_json_results_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "output": {"results_file": "results.txt"},
        }))
        with pytest.raises(ValueError, match="JSON file"):
            validate_config_file(str(config_file))

    def test_invalid_direction(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "optimizer": {"direction": "optimize"},
        }))
        with pytest.raises(ValueError, match="direction"):
            validate_config_file(str(config_file))

    def test_config_not_dict(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("[1, 2, 3]")
        with pytest.raises(ValueError, match="JSON object"):
            validate_config_file(str(config_file))


class TestCLIInit:
    def test_init_minimal(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "test-project"])
            assert result.exit_code == 0
            assert os.path.exists("test-project/fixed.py")
            assert os.path.exists("test-project/variable.py")
            assert os.path.exists("test-project/config.json")
            assert os.path.exists("test-project/README.md")

    def test_init_with_template(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "ml-proj", "--template", "ml-optimization"])
            assert result.exit_code == 0
            assert os.path.exists("ml-proj/variable.py")
            with open("ml-proj/variable.py") as f:
                content = f.read()
                assert "search_space" in content

    def test_init_invalid_name(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "../evil"])
            assert result.exit_code != 0

    def test_init_duplicate_no_force(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "dup-project"])
            result = runner.invoke(cli, ["init", "dup-project"])
            assert result.exit_code != 0

    def test_init_duplicate_with_force(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "dup-project"])
            result = runner.invoke(cli, ["init", "dup-project", "--force"])
            assert result.exit_code == 0


class TestCLIReport:
    def test_report_with_valid_results(self, tmp_path):
        from lingminopt.core.models import Experiment, OptimizationResult
        from datetime import datetime

        experiments = [
            Experiment(experiment_id=1, params={"x": 1.0}, score=1.0, timestamp=datetime.now()),
            Experiment(experiment_id=2, params={"x": 2.0}, score=0.5, timestamp=datetime.now()),
        ]
        result = OptimizationResult(
            best_score=0.5,
            best_params={"x": 2.0},
            history=experiments,
            total_experiments=2,
            total_time=0.1,
            improvement=0.5,
        )

        results_file = tmp_path / "results.json"
        result.save(str(results_file))

        runner = CliRunner()
        output = runner.invoke(cli, ["report", "--results", str(results_file)])
        assert output.exit_code == 0
        assert "0.500000" in output.output

    def test_report_missing_file(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--results", "/nonexistent.json"])
        assert result.exit_code != 0


class TestCLIInbox:
    def test_inbox_no_db_url(self):
        runner = CliRunner()
        env = {k: v for k, v in os.environ.items() if k != "LINGMESSAGE_DB_URL"}
        result = runner.invoke(cli, ["inbox"], env=env)
        assert "LINGMESSAGE_DB_URL" in result.output

    def test_inbox_reply_no_db_url(self):
        runner = CliRunner()
        env = {k: v for k, v in os.environ.items() if k != "LINGMESSAGE_DB_URL"}
        result = runner.invoke(cli, ["inbox", "--reply", "1", "--message", "test"], env=env)
        assert "LINGMESSAGE_DB_URL" in result.output
