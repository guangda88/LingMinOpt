# Changelog

All notable changes to LingMinOpt will be documented in this file.

## [0.3.0] - 2026-04-07

### Added
- Added `callbacks` parameter to `MinimalOptimizer.__init__()` — list of functions called after each experiment with full info dict (experiment_id, params, score, best_score, best_params, improved, elapsed, total_experiments)
- Added `Experiment.to_json()` method for JSON serialization
- Added `Experiment.save()` and `Experiment.load()` class methods for file persistence
- Added `Experiment.__post_init__` validation — rejects negative experiment_id, NaN scores, and inf scores
- Added `grid_points_per_axis` parameter to `GridSearch.__init__()` (default 5) for configurable grid density
- Added `setup_logger()` function with `RotatingFileHandler` support (10MB default, 5 backups)
- Added `file_level`, `max_bytes`, `backup_count` parameters to `setup_logger()` for flexible logging configuration
- Added exports to `__init__.py`: `SearchStrategy`, `create_strategy`, `setup_logger`, `__version__`
- Added comprehensive test suite for v0.3.0 features (24 new tests)

### Fixed
- Fixed `SimulatedAnnealing.suggest_next()` — now properly implements Metropolis-Hastings acceptance criterion:
  - Delta < 0 (improvement): always accept
  - Delta > 0 (worse): accept with probability exp(-delta/temp)
  - Initialize from best experiment in history when first called with history
- Fixed `SimulatedAnnealing` temperature cooling — now cools after each suggestion (not on first call)
- Fixed global random seed pollution — removed `random.seed()` call from `MinimalOptimizer.run()` to preserve global state
- Removed redundant `from datetime import datetime` inside loop in `MinimalOptimizer.run()`
- Fixed logger handler management — removed `logger.handlers.clear()` to avoid destroying external handlers, added `logger.propagate = False` guard

### Changed
- Updated `__version__` from "0.2.0" to "0.3.0"
- Updated `__all__` in `__init__.py` to include all new exports
- Updated CLI version option to use `__version__` from package instead of hardcoded "0.1.0"
- Fixed README template: "Minimal Optimizer (MinOpt)" → "LingMinOpt (灵极优)"
- Improved `Experiment.from_dict()` to handle missing `timestamp` gracefully (defaults to `now()`)

### Testing
- All 79 tests passing (55 existing + 24 new)
- New test classes:
  - `TestSimulatedAnnealingAcceptance` (4 tests)
  - `TestGridSearchConfigurablePoints` (3 tests)
  - `TestExperimentSerialization` (5 tests)
  - `TestOptimizerCallbacks` (3 tests)
  - `TestCreateStrategyKwargsForwarding` (3 tests)
  - `TestSetupLogger` (2 tests)
  - `TestPackageExports` (4 tests)

## [0.2.1] - 2026-04-07

### Security (Critical)
- **C1**: Fixed silent exception swallowing in optimizer — added consecutive failure tracking with abort after `max(3, max_experiments//5)` failures
- **C2**: Eliminated SQL injection in inbox CLI — replaced string concatenation with asyncpg parameterized queries
- **C3**: Removed hardcoded database credentials — now requires `LINGMESSAGE_DB_URL` env var or `--db-url` parameter

### Fixed
- **H1**: Resolved duplicate `ExperimentConfig` — `core/config.py` now re-exports from `config/config.py`
- **H2**: Fixed 4 instances of `minopt` → `lingminopt` in CLI templates
- **M3**: Removed unused `import subprocess`
- **M4**: Replaced variable name `l` with proper dict row access

### Refactored
- Converted package examples (`example1_quadratic.py`, `example2_ml_tuning.py`) from `print()` to `logging`
- Added type hints to `core/optimizer.py`, `core/searcher.py`, `core/evaluator.py`, `config/config.py`
- Added docstrings to `_inbox_read()` and `_inbox_reply()` CLI functions
- Fixed ruff warnings in external examples (f-string without placeholders, unused variable)

### Testing
- 55 tests total (29 core + 26 new CLI)
- New CLI tests: `validate_project_name` (9), `validate_config_file` (8), `cli init` (5), `cli report` (2), `cli inbox` (2)
- New audit regression tests: `test_consecutive_failures_abort`, `test_single_failure_does_not_abort`, `test_experiment_config_single_source`

### Documentation
- Added `AUDIT_REPORT.md` — full system audit against 灵通宪章 and 灵信章程
- Added `TASK_LIST.md` — P0/P1/P2 task tracking with status

## [0.2.0] - 2026-04-06

### Added
- Added `__len__` method to `SearchSpace` class
- Added `__contains__` method to `SearchSpace` class
- Added `from_dict` class method to `SearchSpace` class
- Added `add_from_dict` method to `SearchSpace` class
- Added input validation for discrete parameters (rejects empty choices)
- Added input validation for continuous parameters (rejects min >= max)
- Added project name validation to prevent path traversal attacks
- Added config file validation to validate results_file paths and direction
- Added warning when loading user code from `variable.py`

### Fixed
- Fixed broken imports in `__init__.py` - added missing exports for `Experiment`, `OptimizationResult`, evaluator classes, and search strategies
- Fixed CLI template package name - changed `from minopt import` to `from lingminopt import`
- Fixed timestamp type error - now uses `datetime.now()` instead of `time.time()` in `Experiment` creation
- Removed duplicate `ExperimentConfig` class from `optimizer.py`
- Removed duplicate `OptimizationResult` class from `optimizer.py`
- Implemented proper search strategy integration in `MinimalOptimizer`
- Fixed silent exception handling - now logs errors with stack traces
- Cleaned up unused imports and variables
- Fixed code warnings with ruff

### Changed
- Improved search strategy integration - strategies now receive history for context-aware suggestions
- `MinimalOptimizer` now accepts `search_strategy` and `seed` parameters
- Enhanced logging throughout optimization process
- Improved CLI security with input validation

### Security
- Fixed CLI path traversal vulnerability in project initialization
- Added warning for dynamic code loading from `variable.py`
- Validated config file paths to prevent directory traversal

### Testing
- All 26 tests passing
- Added validation tests for SearchSpace methods
- CLI commands tested end-to-end (init, run, report)

## [0.1.0] - 2025-12-XX

### Initial Release
- Basic optimization framework
- Random search, Grid search, Bayesian search, Simulated annealing strategies
- CLI tool with init, run, report commands
- Project templates (minimal, ml-optimization)
