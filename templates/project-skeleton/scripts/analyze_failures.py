"""
최근 실험 결과를 분석하여 실패 양상을 분류하고 error_analysis.md를 갱신한다.
result-analyzer skill이 호출하거나 nightly workflow에서 실행.
"""
import json
from datetime import datetime
from pathlib import Path


def _find_latest_timestamp() -> str | None:
    """Find the latest YYYYMMDD_HHMMSS directory under results/."""
    import re
    results_dir = Path("results")
    if not results_dir.exists():
        return None
    dirs = sorted(
        [d.name for d in results_dir.iterdir()
         if d.is_dir() and re.match(r"\d{8}_\d{6}", d.name)],
        reverse=True,
    )
    return dirs[0] if dirs else None


def load_recent_runs(n: int = 10) -> list:
    registry_path = Path("results/registry.json")
    if not registry_path.exists():
        return []
    with open(registry_path) as f:
        runs = json.load(f).get("runs", [])
    return runs[-n:]


def load_metrics_for_runs(runs: list) -> list:
    results = []
    for run in runs:
        run_dir = Path(run.get("run_dir", ""))
        metrics_file = run_dir / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                metrics = json.load(f)
            results.append({**run, "metrics": metrics})
        else:
            results.append({**run, "metrics": {}})
    return results


def analyze_runs(runs_with_metrics: list) -> dict:
    """실험 결과를 분석한다. 고정된 분류가 아니라 데이터에서 패턴을 찾는다."""
    analysis = {
        "failed_runs": [],
        "patterns": [],
    }

    failed = [r for r in runs_with_metrics if r.get("status") == "failed"]
    analysis["failed_runs"] = [r.get("run_id", "") for r in failed]

    completed = [r for r in runs_with_metrics if r.get("status") == "completed"]
    if len(completed) >= 3:
        values = [r.get("primary_metric_value", 0.0) for r in completed[-5:]]
        if len(values) >= 3:
            value_range = max(values) - min(values)
            mean_val = sum(values) / len(values)

            # 변화가 거의 없으면 plateau 가능성 (threshold는 metric 범위에 비례)
            if mean_val != 0 and value_range / abs(mean_val) < 0.01:
                analysis["patterns"].append({
                    "type": "plateau",
                    "confidence": "likely",
                    "detail": f"최근 {len(values)}회 실험에서 변화폭 {value_range:.4f}",
                })

            # 변화가 크면 instability 가능성
            if mean_val != 0 and value_range / abs(mean_val) > 0.1:
                analysis["patterns"].append({
                    "type": "instability",
                    "confidence": "hypothesis",
                    "detail": f"실험 간 변화폭 {value_range:.4f}",
                })

    return analysis


def generate_error_analysis(runs_with_metrics: list, analysis: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    completed = [r for r in runs_with_metrics if r.get("status") == "completed"]
    failed = [r for r in runs_with_metrics if r.get("status") == "failed"]

    report = f"""# Error Analysis
_Updated: {now}_

## Analysis Target
- Total runs analyzed: {len(runs_with_metrics)}
- Completed: {len(completed)}
- Failed: {len(failed)}

## Performance Trend
"""
    if completed:
        report += "| Run ID | Primary Metric | Timestamp |\n"
        report += "|--------|---------------|----------|\n"
        for r in completed[-5:]:
            run_id = r.get("run_id", "")[:16]
            value = r.get("primary_metric_value", "N/A")
            ts = r.get("timestamp", "")[:16]
            report += f"| {run_id} | {value} | {ts} |\n"
    else:
        report += "_완료된 실험 없음_\n"

    report += "\n## Detected Patterns\n"

    if analysis["failed_runs"]:
        report += f"\n### Failed Runs\n"
        for run_id in analysis["failed_runs"]:
            report += f"- `{run_id}`: stdout.log 확인 필요\n"

    for pattern in analysis["patterns"]:
        report += f"\n### {pattern['type'].title()} ({pattern['confidence']})\n"
        report += f"- {pattern['detail']}\n"

    if not analysis["failed_runs"] and not analysis["patterns"]:
        report += "\n_특이 패턴 없음 — 실험 계속 진행 권장_\n"

    report += "\n---\n_이 파일은 자동 생성됩니다. 수동 보완은 아래에 추가하세요._\n\n"
    report += "## Manual Notes\n_여기에 수동으로 관찰 사항을 기록하세요._\n"

    return report


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()

    runs = load_recent_runs(n=10)
    if not runs:
        if not args.auto:
            print("[analyze] 실험 결과 없음.")
        return

    runs_with_metrics = load_metrics_for_runs(runs)
    analysis = analyze_runs(runs_with_metrics)
    report = generate_error_analysis(runs_with_metrics, analysis)

    # Save to latest timestamp directory
    latest_ts = _find_latest_timestamp()
    if latest_ts:
        output_path = Path(f"results/{latest_ts}/report/error_analysis.md")
    else:
        output_path = Path("results/error_analysis.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)

    print("[analyze] error_analysis.md 갱신 완료")
    for pattern in analysis["patterns"]:
        print(f"[analyze] 감지: {pattern['type']} ({pattern['confidence']})")


if __name__ == "__main__":
    main()
