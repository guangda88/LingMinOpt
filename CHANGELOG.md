# Changelog

All notable changes to LingMinOpt will be documented in this file.

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
