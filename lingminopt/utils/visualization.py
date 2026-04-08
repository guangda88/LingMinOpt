"""Optimization visualization module.

Generates plots from OptimizationResult objects using matplotlib/seaborn.
All functions gracefully degrade if visualization dependencies are missing.
"""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

_DEPS_MISSING = False
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    _DEPS_MISSING = True

try:
    import seaborn as sns
    sns.set_style("whitegrid")
except ImportError:
    pass


def _check_deps() -> None:
    if _DEPS_MISSING:
        raise ImportError(
            "Visualization dependencies not installed. "
            "Run: pip install lingminopt[visualization]"
        )


def plot_convergence(
    result: Any,
    title: str = "Optimization Convergence",
    save_path: Optional[str] = None,
    show: bool = False,
) -> Optional["plt.Figure"]:
    """Plot best score over experiments.

    Args:
        result: OptimizationResult object
        title: Plot title
        save_path: If provided, save figure to this path
        show: If True, call plt.show()

    Returns:
        matplotlib Figure object (if deps available)
    """
    _check_deps()

    history = result.history
    if not history:
        logger.warning("No history to plot")
        return None

    best_scores: List[float] = []
    current_best = float("inf")
    for exp in history:
        current_best = min(current_best, exp.score)
        best_scores.append(current_best)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(range(1, len(history) + 1), [e.score for e in history],
            "o", alpha=0.3, label="Experiment score", markersize=4)
    ax.plot(range(1, len(best_scores) + 1), best_scores,
            "-", linewidth=2, label="Best score", color="tab:blue")
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.legend()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Convergence plot saved to {save_path}")
    if show:
        plt.show()

    return fig


def plot_score_distribution(
    result: Any,
    title: str = "Score Distribution",
    save_path: Optional[str] = None,
    show: bool = False,
) -> Optional["plt.Figure"]:
    """Plot histogram of all experiment scores.

    Args:
        result: OptimizationResult object
        title: Plot title
        save_path: If provided, save figure to this path
        show: If True, call plt.show()

    Returns:
        matplotlib Figure object
    """
    _check_deps()

    history = result.history
    if not history:
        logger.warning("No history to plot")
        return None

    scores = [e.score for e in history]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(scores, bins=min(30, max(5, len(scores) // 3)),
            edgecolor="black", alpha=0.7, color="tab:blue")
    ax.axvline(result.best_score, color="red", linestyle="--",
               linewidth=2, label=f"Best: {result.best_score:.4f}")
    ax.set_xlabel("Score")
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.legend()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Distribution plot saved to {save_path}")
    if show:
        plt.show()

    return fig


def plot_param_importance(
    result: Any,
    title: str = "Parameter Importance",
    save_path: Optional[str] = None,
    show: bool = False,
) -> Optional["plt.Figure"]:
    """Plot parameter importance based on score correlation.

    For each parameter, computes the absolute correlation between
    its values and the resulting scores across experiments.

    Args:
        result: OptimizationResult object
        title: Plot title
        save_path: If provided, save figure to this path
        show: If True, call plt.show()

    Returns:
        matplotlib Figure object
    """
    _check_deps()

    history = result.history
    if not history:
        logger.warning("No history to plot")
        return None

    import numpy as np

    scores = np.array([e.score for e in history])
    param_names = list(result.best_params.keys())

    correlations: Dict[str, float] = {}
    for name in param_names:
        values = np.array([e.params.get(name, 0) for e in history])
        try:
            numeric_vals = values.astype(float)
            if np.std(numeric_vals) < 1e-12:
                correlations[name] = 0.0
            else:
                corr = np.corrcoef(numeric_vals, scores)[0, 1]
                correlations[name] = abs(corr) if not np.isnan(corr) else 0.0
        except (ValueError, TypeError):
            correlations[name] = 0.0

    sorted_params = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
    names = [p[0] for p in sorted_params]
    values = [p[1] for p in sorted_params]

    fig, ax = plt.subplots(figsize=(10, max(4, len(names) * 0.5)))
    ax.barh(names, values, color="tab:green", edgecolor="black", alpha=0.7)
    ax.set_xlabel("|Correlation with Score|")
    ax.set_title(title)
    ax.invert_yaxis()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Importance plot saved to {save_path}")
    if show:
        plt.show()

    return fig


def plot_timeline(
    result: Any,
    title: str = "Experiment Timeline",
    save_path: Optional[str] = None,
    show: bool = False,
) -> Optional["plt.Figure"]:
    """Plot experiment scores over time.

    Args:
        result: OptimizationResult object
        title: Plot title
        save_path: If provided, save figure to this path
        show: If True, call plt.show()

    Returns:
        matplotlib Figure object
    """
    _check_deps()

    history = result.history
    if not history:
        logger.warning("No history to plot")
        return None

    from datetime import datetime

    timestamps = []
    for exp in history:
        ts = exp.timestamp
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        timestamps.append(ts)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.scatter(timestamps, [e.score for e in history],
               c=[e.score for e in history], cmap="RdYlGn_r",
               s=30, edgecolors="black", linewidth=0.5)
    ax.set_xlabel("Time")
    ax.set_ylabel("Score")
    ax.set_title(title)
    fig.autofmt_xdate()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Timeline plot saved to {save_path}")
    if show:
        plt.show()

    return fig


def generate_report(
    result: Any,
    output_dir: str = ".",
    prefix: str = "optimization",
) -> List[str]:
    """Generate a full visual report with all plots.

    Args:
        result: OptimizationResult object
        output_dir: Directory to save plots
        prefix: Filename prefix

    Returns:
        List of saved file paths
    """
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    saved: List[str] = []

    for plot_fn, suffix in [
        (plot_convergence, "convergence"),
        (plot_score_distribution, "distribution"),
        (plot_param_importance, "importance"),
        (plot_timeline, "timeline"),
    ]:
        try:
            path = str(out / f"{prefix}_{suffix}.png")
            fig = plot_fn(result, save_path=path)
            if fig is not None:
                plt.close(fig)
                saved.append(path)
        except Exception as e:
            logger.warning(f"Failed to generate {suffix} plot: {e}")

    return saved
