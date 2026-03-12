"""
Experiment runner script.
Called by the experiment-runner skill.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def save_metrics(output_dir: Path, metrics: dict, config_path: str) -> None:
    git_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()

    result = {
        "timestamp": datetime.now().isoformat(),
        "git_commit": git_commit,
        "config": config_path,
        "primary_metric": metrics.get("primary_metric", {"name": "unknown", "value": 0.0}),
        "secondary_metrics": metrics.get("secondary_metrics", {}),
        "train_epochs": metrics.get("train_epochs", 0),
        "best_epoch": metrics.get("best_epoch", 0),
        "status": metrics.get("status", "completed"),
    }

    with open(output_dir / "metrics.json", "w") as f:
        json.dump(result, f, indent=2)


def save_plots(output_dir: Path, metrics: dict) -> None:
    """Save matplotlib visualizations to plots/ subdirectory."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        print("[runner] matplotlib not installed — skipping plots")
        return

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    # training curve
    history = metrics.get("history", {})
    train_loss = history.get("train_loss", [])
    val_loss = history.get("val_loss", [])
    if train_loss or val_loss:
        fig, ax = plt.subplots(figsize=(8, 5))
        if train_loss:
            ax.plot(train_loss, label="train loss")
        if val_loss:
            ax.plot(val_loss, label="val loss")
        ax.set_xlabel("epoch")
        ax.set_ylabel("loss")
        ax.set_title("Training Curve")
        ax.legend()
        fig.tight_layout()
        fig.savefig(plots_dir / "training_curve.png", dpi=150)
        plt.close(fig)
        print(f"[runner] saved: plots/training_curve.png")

    # metric curve
    primary_name = metrics.get("primary_metric", {}).get("name", "metric")
    metric_history = history.get(primary_name, history.get("val_metric", []))
    if metric_history:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(metric_history, color="tab:green")
        best_epoch = metrics.get("best_epoch", 0)
        if 0 <= best_epoch < len(metric_history):
            ax.axvline(best_epoch, color="red", linestyle="--", label=f"best epoch {best_epoch}")
        ax.set_xlabel("epoch")
        ax.set_ylabel(primary_name)
        ax.set_title(f"{primary_name} over epochs")
        ax.legend()
        fig.tight_layout()
        fig.savefig(plots_dir / "metric_curve.png", dpi=150)
        plt.close(fig)
        print(f"[runner] saved: plots/metric_curve.png")

    # secondary metrics bar chart
    secondary = metrics.get("secondary_metrics", {})
    if secondary:
        fig, ax = plt.subplots(figsize=(7, 4))
        names = list(secondary.keys())
        values = [v if isinstance(v, (int, float)) else 0.0 for v in secondary.values()]
        bars = ax.bar(names, values, color="tab:blue")
        ax.bar_label(bars, fmt="%.4f", padding=3)
        ax.set_title("Secondary Metrics")
        ax.set_ylabel("value")
        fig.tight_layout()
        fig.savefig(plots_dir / "secondary_metrics.png", dpi=150)
        plt.close(fig)
        print(f"[runner] saved: plots/secondary_metrics.png")


def update_registry(run_dir: Path, metrics: dict) -> None:
    registry_path = Path("results/registry.json")
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
    else:
        registry = {"runs": []}

    primary_value = metrics.get("primary_metric", {}).get("value", 0.0)
    registry["runs"].append({
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "primary_metric_value": primary_value,
        "status": metrics.get("status", "completed"),
        "timestamp": datetime.now().isoformat(),
        "notes": "",
    })

    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(args.config)
    shutil.copy(args.config, output_dir / "config_snapshot.yaml")

    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    (output_dir / "git_commit.txt").write_text(git_commit)

    print(f"[runner] start: {output_dir.name}")
    print(f"[runner] config: {args.config}")
    print(f"[runner] git: {git_commit[:8]}")

    try:
        from src.train import train
        from src.evaluate import evaluate

        model = train(config)
        metrics = evaluate(model, config)
        metrics["status"] = "completed"
        print(f"[runner] primary metric: {metrics.get('primary_metric', {})}")

    except ImportError:
        print("[runner] src/train.py or src/evaluate.py not found — saving dummy results")
        metrics = {
            "primary_metric": {"name": config.get("primary_metric", "metric"), "value": 0.0},
            "secondary_metrics": {},
            "history": {},
            "train_epochs": 0,
            "best_epoch": 0,
            "status": "completed",
        }
    except Exception as e:
        print(f"[runner] experiment failed: {e}")
        metrics = {"status": "failed", "error": str(e), "history": {}}

    save_metrics(output_dir, metrics, args.config)
    save_plots(output_dir, metrics)
    update_registry(output_dir, metrics)

    print(f"[runner] done: {output_dir}")


if __name__ == "__main__":
    main()
