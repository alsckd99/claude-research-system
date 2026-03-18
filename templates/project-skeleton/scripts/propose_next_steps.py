"""
최근 실험 결과와 error_analysis를 바탕으로 next_actions.md를 갱신한다.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path


def _find_latest_timestamp() -> str | None:
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


def load_registry() -> list:
    registry_path = Path("results/registry.json")
    if not registry_path.exists():
        return []
    with open(registry_path) as f:
        return json.load(f).get("runs", [])


def detect_trend(runs: list) -> str:
    completed = [r for r in runs if r.get("status") == "completed"]
    if len(completed) < 2:
        return "insufficient_data"

    recent = completed[-5:]
    values = [r.get("primary_metric_value", 0.0) for r in recent]

    if len(values) < 2:
        return "insufficient_data"

    last = values[-1]
    prev_avg = sum(values[:-1]) / len(values[:-1])

    if prev_avg == 0:
        return "insufficient_data"

    ratio = last / prev_avg
    if ratio > 1.01:
        return "improving"
    elif ratio < 0.99:
        return "degrading"
    else:
        return "plateau"


def count_consecutive_failures(runs: list) -> int:
    count = 0
    for run in reversed(runs):
        if run.get("status") == "failed":
            count += 1
        else:
            break
    return count


def generate_next_actions(runs: list, trend: str, failures: int) -> str:
    actions = []

    if not runs:
        actions = [
            "1. **[즉시]** baseline 코드 구현 완료 확인",
            "2. **[즉시]** smoke test 실행: `pytest -q tests/`",
            "3. **[즉시]** 첫 baseline 실험 실행",
        ]
    elif failures >= 3:
        actions = [
            f"1. **[긴급]** 연속 {failures}회 실패 — stdout.log 에러 원인 분석",
            "2. **[긴급]** error_analysis.md 확인",
            "3. **[권장]** result-analyzer skill 실행하여 실패 분류",
        ]
    elif trend == "plateau":
        actions = [
            "1. **[분석]** result-analyzer skill 실행 — 성능 정체 원인 파악",
            "2. **[탐색]** literature-scout skill 실행 — 새 방법 탐색",
            "3. **[검토]** docs/baselines.md — 아직 시도 안 한 방법 확인",
        ]
    elif trend == "degrading":
        actions = [
            "1. **[긴급]** 최근 변경 사항 확인 (`git log --oneline -5`)",
            "2. **[긴급]** result-analyzer skill 실행 — 성능 하락 원인 파악",
            "3. **[검토]** rollback 여부 검토",
        ]
    elif trend == "improving":
        actions = [
            "1. **[계속]** 현재 방향 유지 — 다음 실험 실행",
            "2. **[선택]** ablation 실험으로 어떤 변경이 효과 있는지 확인",
            "3. **[선택]** secondary metric도 함께 확인",
        ]
    else:
        actions = [
            "1. **[확인]** 첫 실험 결과 분석",
            "2. **[다음]** result-analyzer skill 실행",
        ]

    return "\n".join(actions)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()

    runs = load_registry()
    trend = detect_trend(runs)
    failures = count_consecutive_failures(runs)

    content = f"""# Next Actions
_Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}_

## Status
- **Trend**: {trend}
- **Total runs**: {len(runs)}
- **Consecutive failures**: {failures}

## Recommended Actions

{generate_next_actions(runs, trend, failures)}
"""

    # Save to latest timestamp directory
    latest_ts = _find_latest_timestamp()
    if latest_ts:
        output_path = Path(f"results/{latest_ts}/report/next_actions.md")
    else:
        output_path = Path("results/next_actions.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)

    print(f"[propose] next_actions.md 갱신 완료 (trend: {trend})")


if __name__ == "__main__":
    main()
