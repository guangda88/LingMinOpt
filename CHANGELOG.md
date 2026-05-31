# Changelog — lingminopt

All notable changes to this project will be documented in this file.

## [0.6.0] - 2026-05-31

### Security (P0 Fix)
- Removed all exec()/eval()/compile() from mcp_server.py — replaced with declarative evaluator registry
- 6 built-in evaluators: sphere, rastrigin, rosenbrock, ackley, quadratic, neg_mean
- API change: `evaluate_code: str` → `evaluator: str` (registry key) in run_optimization/optimization_pipeline
- All 4 bypass vectors identified by lingclaude eliminated (startswith/CWD/while-DoS/params-sidechannel)
- Path validation `_validate_data_path()` restricts file access to data/ and results/

### Added
- `list_evaluators` MCP tool (16 tools total, up from 15)

### Changed
- AST sandbox removed — no longer needed without dynamic code execution

## [0.5.0] - 2026-04-18

### Added
- Initial changelog tracking
- VERSION file created
