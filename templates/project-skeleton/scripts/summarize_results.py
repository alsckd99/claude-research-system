"""
최근 실험 결과를 요약하여 experiments/reports/latest.md를 갱신한다.
hooks의 Stop 이벤트 또는 experiment-runner 완료 후 자동 실행.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path


def load_registry() -> list:
    registry_path = Path("experiments/registry.json")
    if not registry_path.exists():
        return []
    with open(registry_path) as f:
        data = json.load(f)
    return data.get("runs", [])


def load_metrics(run_dir: str) -> dict:
    metrics_path = Path(run_dir) / "metrics.json"
    if not metrics_path.exists():
        return {}
    with open(metrics_path) as f:
        return json.load(f)


def load_config_snapshot(run_dir: str) -> dict:
    config_path = Path(run_dir) / "config_snapshot.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def format_table(runs: list) -> str:
    if not runs:
        return "_실험 결과 없음_"

    header = "| Run ID | Primary Metric | Status | Timestamp |\n"
    header += "|--------|---------------|--------|----------|\n"

    rows = []
    for run in runs[-10:]:  # 최근 10개
        run_id = run.get("run_id", "")[:16]
        value = run.get("primary_metric_value", "N/A")
        status = run.get("status", "unknown")
        ts = run.get("timestamp", "")[:16]
        rows.append(f"| {run_id} | {value} | {status} | {ts} |")

    return header + "\n".join(rows)


def find_best_run(runs: list) -> dict:
    completed = [r for r in runs if r.get("status") == "completed"]
    if not completed:
        return {}
    return max(completed, key=lambda r: r.get("primary_metric_value", 0.0))


def generate_report(runs: list) -> str:
    best = find_best_run(runs)
    recent = runs[-1] if runs else {}

    report = f"""# Latest Experiment Report
_Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}_

## Summary
- **Total runs**: {len(runs)}
- **Completed**: {sum(1 for r in runs if r.get("status") == "completed")}
- **Failed**: {sum(1 for r in runs if r.get("status") == "failed")}

## Best Performance
"""
    if best:
        report += f"""- **Run**: `{best.get("run_id", "N/A")}`
- **Primary metric**: {best.get("primary_metric_value", "N/A")}
- **Timestamp**: {best.get("timestamp", "N/A")[:16]}
"""
    else:
        report += "_완료된 실험 없음_\n"

    report += "\n## Recent Runs (last 10)\n\n"
    report += format_table(runs)

    if recent:
        metrics_data = load_metrics(recent.get("run_dir", ""))
        if metrics_data.get("secondary_metrics"):
            report += "\n\n## Latest Run Secondary Metrics\n"
            for k, v in metrics_data["secondary_metrics"].items():
                report += f"- **{k}**: {v}\n"

    report += "\n\n---\n_See `experiments/reports/error_analysis.md` for failure analysis._\n"
    report += "_See `experiments/reports/next_actions.md` for next steps._\n"

    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()

    runs = load_registry()

    if not runs and not args.auto:
        print("[summarize] 실험 결과 없음.")
        return

    report = generate_report(runs)

    output_path = Path("experiments/reports/latest.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)

    print(f"[summarize] 보고서 갱신 완료: {output_path}")
    if runs:
        best = find_best_run(runs)
        if best:
            print(f"[summarize] 최고 성능: {best.get('primary_metric_value')} (run: {best.get('run_id', '')[:16]})")


if __name__ == "__main__":
    main()
