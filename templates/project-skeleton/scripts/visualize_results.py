"""
Cross-run visualization generator.
Generates comparison graphs across all experiment runs.
Only shows top N runs by default to avoid clutter.

Usage:
    python scripts/visualize_results.py --auto
    python scripts/visualize_results.py --output results/reports/plots --top 10
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# max runs to show in detailed charts (trend shows all, others are capped)
DEFAULT_TOP_N = 10


def load_all_runs(results_dir: Path) -> list[dict[str, Any]]:
    """Load metrics from all completed runs, sorted by timestamp."""
    runs = []
    runs_dir = results_dir / "runs"
    if not runs_dir.exists():
        return runs

    for run_dir in sorted(runs_dir.iterdir()):
        metrics_file = run_dir / "metrics.json"
        if not metrics_file.exists():
            continue
        try:
            metrics = json.loads(metrics_file.read_text())
            metrics["_run_id"] = run_dir.name
            metrics["_run_dir"] = str(run_dir)
            runs.append(metrics)
        except (json.JSONDecodeError, OSError):
            continue

    return runs


def load_registry(results_dir: Path) -> list[dict[str, Any]]:
    """Load registry for additional run metadata."""
    reg_file = results_dir / "registry.json"
    if not reg_file.exists():
        return []
    try:
        return json.loads(reg_file.read_text()).get("runs", [])
    except (json.JSONDecodeError, OSError):
        return []


def plot_metric_trend(runs: list[dict], output_dir: Path, plt) -> None:
    """Plot primary metric across all runs — shows improvement trajectory."""
    values = []
    labels = []
    for r in runs:
        pm = r.get("primary_metric", {})
        val = pm.get("value")
        if val is not None:
            values.append(float(val))
            labels.append(r["_run_id"][:8])

    if len(values) < 2:
        print("[viz] not enough runs for trend plot — skip")
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(values))
    ax.plot(x, values, "o-", color="tab:blue", linewidth=2, markersize=8)

    # highlight best
    best_idx = max(range(len(values)), key=lambda i: values[i])
    ax.plot(best_idx, values[best_idx], "o", color="tab:red", markersize=14,
            zorder=5, label=f"best: {values[best_idx]:.4f}")

    # annotate improvement from first to best
    if best_idx > 0:
        delta = values[best_idx] - values[0]
        pct = (delta / max(abs(values[0]), 1e-8)) * 100
        ax.annotate(
            f"+{delta:.4f} ({pct:+.1f}%)",
            xy=(best_idx, values[best_idx]),
            xytext=(best_idx, values[best_idx] + 0.02 * max(values)),
            fontsize=10, ha="center", color="tab:red",
        )

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_xlabel("Run")
    ax.set_ylabel(runs[0].get("primary_metric", {}).get("name", "metric"))
    ax.set_title("Primary Metric Trend Across Runs")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "metric_trend.png", dpi=150)
    plt.close(fig)
    print(f"[viz] saved: metric_trend.png ({len(values)} runs)")


def filter_top_runs(runs: list[dict], top_n: int) -> list[dict]:
    """Keep only top N runs by primary metric + the latest run. Avoids clutter."""
    if len(runs) <= top_n:
        return runs

    scored = []
    for r in runs:
        val = r.get("primary_metric", {}).get("value")
        scored.append((float(val) if val is not None else float("-inf"), r))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [r for _, r in scored[:top_n]]

    # always include the latest run
    latest = runs[-1]
    if latest not in top:
        top.append(latest)

    return top


def plot_secondary_comparison(runs: list[dict], output_dir: Path, plt, top_n: int = 5) -> None:
    """Bar chart comparing secondary metrics across top runs only."""
    import numpy as np

    # take top runs by primary metric, not just latest
    with_secondary = [r for r in runs if r.get("secondary_metrics")]
    recent = filter_top_runs(with_secondary, top_n)[-top_n:]
    if len(recent) < 2:
        print("[viz] not enough runs for secondary comparison — skip")
        return

    all_keys = set()
    for r in recent:
        all_keys.update(r["secondary_metrics"].keys())
    metric_names = sorted(all_keys)

    if not metric_names:
        return

    n_runs = len(recent)
    n_metrics = len(metric_names)
    x = np.arange(n_metrics)
    width = 0.8 / n_runs

    fig, ax = plt.subplots(figsize=(max(8, n_metrics * 2), 5))
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, n_runs))

    for i, r in enumerate(recent):
        vals = []
        for m in metric_names:
            v = r["secondary_metrics"].get(m, 0)
            vals.append(float(v) if isinstance(v, (int, float)) else 0.0)
        bars = ax.bar(x + i * width, vals, width, label=r["_run_id"][:8], color=colors[i])
        ax.bar_label(bars, fmt="%.3f", fontsize=7, padding=2)

    ax.set_xticks(x + width * (n_runs - 1) / 2)
    ax.set_xticklabels(metric_names, rotation=30, ha="right")
    ax.set_title("Secondary Metrics — Recent Runs Comparison")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "secondary_comparison.png", dpi=150)
    plt.close(fig)
    print(f"[viz] saved: secondary_comparison.png ({n_runs} runs)")


def plot_run_status_summary(runs: list[dict], output_dir: Path, plt) -> None:
    """Pie chart of run statuses (completed, failed, skipped)."""
    status_counts: dict[str, int] = {}
    for r in runs:
        s = r.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    if not status_counts:
        return

    fig, ax = plt.subplots(figsize=(6, 6))
    colors_map = {
        "completed": "tab:green",
        "failed": "tab:red",
        "skipped": "tab:gray",
        "unknown": "tab:orange",
    }
    labels = list(status_counts.keys())
    sizes = list(status_counts.values())
    colors = [colors_map.get(l, "tab:blue") for l in labels]

    ax.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%", startangle=90)
    ax.set_title(f"Run Status Summary (total: {sum(sizes)})")
    fig.tight_layout()
    fig.savefig(output_dir / "run_status_summary.png", dpi=150)
    plt.close(fig)
    print(f"[viz] saved: run_status_summary.png")


def plot_improvement_waterfall(runs: list[dict], output_dir: Path, plt, top_n: int = DEFAULT_TOP_N) -> None:
    """Waterfall chart showing per-run improvement delta. Last N runs only."""
    values = []
    labels = []
    for r in runs[-top_n:]:  # only recent runs
        pm = r.get("primary_metric", {})
        val = pm.get("value")
        if val is not None:
            values.append(float(val))
            labels.append(r["_run_id"][:8])

    if len(values) < 2:
        return

    deltas = [values[0]] + [values[i] - values[i - 1] for i in range(1, len(values))]
    colors = ["tab:blue"] + ["tab:green" if d >= 0 else "tab:red" for d in deltas[1:]]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(deltas)), deltas, color=colors)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("Δ metric (vs previous)")
    ax.set_title("Per-Run Improvement (Waterfall)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "improvement_waterfall.png", dpi=150)
    plt.close(fig)
    print(f"[viz] saved: improvement_waterfall.png")


def generate_summary_text(runs: list[dict], output_dir: Path) -> None:
    """Write a text summary alongside the plots."""
    values = []
    for r in runs:
        pm = r.get("primary_metric", {})
        val = pm.get("value")
        if val is not None:
            values.append((r["_run_id"], float(val), r.get("status", "unknown")))

    completed = [r for r in runs if r.get("status") == "completed"]
    failed = [r for r in runs if r.get("status") == "failed"]

    lines = [
        f"# Visualization Summary",
        f"generated: {datetime.now().isoformat()}",
        f"",
        f"## Overview",
        f"- Total runs: {len(runs)}",
        f"- Completed: {len(completed)}",
        f"- Failed: {len(failed)}",
        f"",
    ]

    if values:
        best = max(values, key=lambda x: x[1])
        worst = min(values, key=lambda x: x[1])
        first = values[0]
        last = values[-1]
        lines.extend([
            f"## Primary Metric",
            f"- Best: {best[1]:.4f} (run {best[0]})",
            f"- Worst: {worst[1]:.4f} (run {worst[0]})",
            f"- First → Last: {first[1]:.4f} → {last[1]:.4f} "
            f"(Δ{last[1] - first[1]:+.4f})",
            f"",
            f"## Generated Plots",
            f"- `metric_trend.png` — primary metric across all runs",
            f"- `secondary_comparison.png` — secondary metrics for recent runs",
            f"- `improvement_waterfall.png` — per-run delta",
            f"- `run_status_summary.png` — completed vs failed",
        ])

    (output_dir / "visualization_summary.md").write_text("\n".join(lines))
    print(f"[viz] saved: visualization_summary.md")


def main():
    parser = argparse.ArgumentParser(description="Cross-run visualization generator")
    parser.add_argument("--auto", action="store_true", help="Auto mode (no prompts)")
    parser.add_argument("--output", default="results/reports/plots",
                        help="Output directory for plots")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_N,
                        help=f"Max runs to show in detailed charts (default: {DEFAULT_TOP_N})")
    args = parser.parse_args()

    results_dir = Path("results")
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    runs = load_all_runs(results_dir)
    if not runs:
        print("[viz] no runs found — nothing to visualize")
        return

    print(f"[viz] found {len(runs)} runs (showing top {args.top} in detail charts)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[viz] matplotlib not installed — skip plots, writing text summary only")
        generate_summary_text(runs, output_dir)
        return

    # trend plot shows ALL runs (overview)
    plot_metric_trend(runs, output_dir, plt)
    # detail charts show only top N to avoid clutter
    plot_secondary_comparison(runs, output_dir, plt, top_n=args.top)
    plot_run_status_summary(runs, output_dir, plt)
    plot_improvement_waterfall(runs, output_dir, plt, top_n=args.top)
    generate_summary_text(runs, output_dir)

    print(f"[viz] done: {output_dir}")


if __name__ == "__main__":
    main()
