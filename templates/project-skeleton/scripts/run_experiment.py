"""
실험 실행 스크립트.
experiment-runner skill이 호출하는 메인 실험 스크립트.
"""
import argparse
import json
import os
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


def update_registry(run_dir: Path, metrics: dict) -> None:
    registry_path = Path("experiments/registry.json")
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

    # config snapshot 저장
    config = load_config(args.config)
    import shutil
    shutil.copy(args.config, output_dir / "config_snapshot.yaml")

    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    (output_dir / "git_commit.txt").write_text(git_commit)

    print(f"[runner] 실험 시작: {output_dir.name}")
    print(f"[runner] Config: {args.config}")
    print(f"[runner] Git commit: {git_commit[:8]}")

    # === 여기에 실제 학습/평가 코드 연결 ===
    try:
        from src.train import train
        from src.evaluate import evaluate

        model = train(config)
        metrics = evaluate(model, config)

        metrics["status"] = "completed"
        print(f"[runner] Primary metric: {metrics.get('primary_metric', {})}")

    except ImportError:
        print("[runner] src/train.py 또는 src/evaluate.py가 없습니다. 더미 결과 저장.")
        metrics = {
            "primary_metric": {"name": config.get("primary_metric", "metric"), "value": 0.0},
            "secondary_metrics": {},
            "train_epochs": 0,
            "best_epoch": 0,
            "status": "completed",
        }
    except Exception as e:
        print(f"[runner] 실험 실패: {e}")
        metrics = {"status": "failed", "error": str(e)}

    save_metrics(output_dir, metrics, args.config)
    update_registry(output_dir, metrics)

    print(f"[runner] 결과 저장 완료: {output_dir}")


if __name__ == "__main__":
    main()
