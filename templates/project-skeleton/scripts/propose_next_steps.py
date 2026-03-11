"""
최근 실험 결과와 error_analysis를 바탕으로 next_actions.md를 갱신한다.
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

    if last > prev_avg * 1.01:
        return "improving"
    elif last < prev_avg * 0.99:
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
            "1. **[즉시]** baseline 코드 구현 완료 확인 (`src/` 디렉토리)",
            "2. **[즉시]** smoke test 실행: `pytest -q tests/`",
            "3. **[즉시]** 첫 baseline 실험 실행: `python scripts/run_experiment.py --config configs/base.yaml --output experiments/runs/$(date +%Y%m%d_%H%M%S)`",
        ]
    elif failures >= 3:
        actions = [
            f"1. **[긴급]** 연속 {failures}회 실패 — `stdout.log` 에러 원인 분석",
            "2. **[긴급]** `experiments/reports/error_analysis.md` 확인",
            "3. **[권장]** result-analyzer skill 실행하여 실패 분류",
            "4. **[권장]** 작은 단위 테스트로 코드 디버깅",
        ]
    elif trend == "plateau":
        actions = [
            "1. **[분석]** result-analyzer skill 실행 — 성능 정체 원인 파악",
            "2. **[탐색]** literature-scout skill 실행 — 새 방법 탐색",
            "3. **[검토]** `docs/baselines.md` — 아직 시도 안 한 방법 확인",
            "4. **[제안]** `experiments/reports/proposed_policy_changes.md` 확인",
        ]
    elif trend == "degrading":
        actions = [
            "1. **[긴급]** 최근 변경 사항 확인 (`git log --oneline -5`)",
            "2. **[긴급]** result-analyzer skill 실행 — 성능 하락 원인 파악",
            "3. **[검토]** rollback 여부 검토 (`git diff` 확인)",
        ]
    elif trend == "improving":
        actions = [
            "1. **[계속]** 현재 방향 유지 — 다음 실험 실행",
            "2. **[선택]** ablation 실험으로 어떤 변경이 효과 있는지 확인",
            "3. **[선택]** secondary metric도 함께 확인 (지연시간, GPU 메모리)",
        ]
    else:
        actions = [
            "1. **[확인]** 첫 실험 결과 분석",
            "2. **[다음]** result-analyzer skill 실행",
        ]

    # 공통 추가 액션
    if runs and trend != "insufficient_data":
        actions.append("---")
        actions.append("**항상 확인:**")
        actions.append("- `experiments/reports/latest.md` — 현재 성능 요약")
        actions.append("- `experiments/reports/error_analysis.md` — 최근 실패 분석")
        actions.append("- `docs/baselines.md` — 비교 기준")

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

    output_path = Path("experiments/reports/next_actions.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)

    print(f"[propose] next_actions.md 갱신 완료 (trend: {trend})")


if __name__ == "__main__":
    main()
