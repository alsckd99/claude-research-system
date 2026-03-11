"""
최근 실험 결과를 분석하여 실패 양상을 분류하고 error_analysis.md를 갱신한다.
result-analyzer skill이 호출하거나 nightly workflow에서 실행.
"""
import json
from datetime import datetime
from pathlib import Path


def load_recent_runs(n: int = 10) -> list:
    registry_path = Path("experiments/registry.json")
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


def classify_failures(runs_with_metrics: list) -> dict:
    classifications = {
        "failed_runs": [],
        "plateau": False,
        "potential_overfitting": False,
        "instability": False,
        "data_issues": False,
    }

    failed = [r for r in runs_with_metrics if r.get("status") == "failed"]
    classifications["failed_runs"] = [r.get("run_id", "") for r in failed]

    completed = [r for r in runs_with_metrics if r.get("status") == "completed"]
    if len(completed) >= 3:
        values = [r.get("primary_metric_value", 0.0) for r in completed[-5:]]
        if len(values) >= 3:
            variance = max(values) - min(values)
            if variance < 0.005:
                classifications["plateau"] = True
            if variance > 0.05:
                classifications["instability"] = True

    return classifications


def generate_error_analysis(runs_with_metrics: list, classifications: dict) -> str:
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

    report += "\n## Failure Classification\n"

    if classifications["failed_runs"]:
        report += f"\n### Failed Runs\n"
        for run_id in classifications["failed_runs"]:
            report += f"- `{run_id}`: stdout.log 확인 필요\n"

    if classifications["plateau"]:
        report += "\n### Performance Plateau (가능성 높음)\n"
        report += "- 최근 실험에서 성능 변화가 거의 없음\n"
        report += "- **권장**: literature-scout skill 실행으로 새 방법 탐색\n"

    if classifications["instability"]:
        report += "\n### Training Instability (가설)\n"
        report += "- 실험 간 성능 분산이 큼\n"
        report += "- **권장**: seed 고정 확인, learning rate 조정 검토\n"

    if not any([classifications["failed_runs"], classifications["plateau"], classifications["instability"]]):
        report += "\n_특이 패턴 없음 — 실험 계속 진행 권장_\n"

    report += "\n## Recommended Next Actions\n"
    if classifications["failed_runs"]:
        report += "1. **[긴급]** failed run의 stdout.log 확인\n"
    if classifications["plateau"]:
        report += "1. **[권장]** literature-scout skill 실행\n"
        report += "2. **[권장]** result-analyzer skill 실행으로 정체 원인 심층 분석\n"

    report += "\n---\n_이 파일은 자동 생성됩니다. 수동 보완은 아래에 추가하세요._\n\n"
    report += "## Manual Notes\n_여기에 수동으로 관찰 사항을 기록하세요._\n"

    return report


def main():
    runs = load_recent_runs(n=10)
    if not runs:
        print("[analyze] 실험 결과 없음.")
        return

    runs_with_metrics = load_metrics_for_runs(runs)
    classifications = classify_failures(runs_with_metrics)
    report = generate_error_analysis(runs_with_metrics, classifications)

    output_path = Path("experiments/reports/error_analysis.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)

    print(f"[analyze] error_analysis.md 갱신 완료")
    if classifications["plateau"]:
        print("[analyze] 경고: 성능 정체 감지 — literature-scout 실행 권장")
    if classifications["instability"]:
        print("[analyze] 경고: 학습 불안정 의심")


if __name__ == "__main__":
    main()
