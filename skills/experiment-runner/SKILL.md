# Skill: experiment-runner

## Trigger
- "실험 돌려줘", "학습 시작해줘"
- after engineer finishes code changes

## Pre-run checks
```bash
pytest -q tests/
```
Config validation 스크립트가 있으면 함께 실행.

## Run
프로젝트의 실행 방법에 맞게 실행 (scripts/run_all.sh, python scripts/run_experiment.py 등).
결과는 `results/runs/{timestamp}/`에 저장.

## Post-run: 시각화 저장

실험 결과와 함께 시각화를 자동 생성하여 run 디렉토리에 저장한다.
어떤 시각화가 필요한지는 프로젝트에 따라 다르지만, 가능한 것은 모두 저장한다.

공통 (대부분의 프로젝트에 해당):
- 학습 curve (loss, metric vs epoch/step) — training이 있는 경우
- Primary metric의 변화 추이 (이전 run들과 비교)

분류/탐지 task:
- Confusion matrix
- ROC curve, PR curve
- Score distribution (positive vs negative)
- Per-class/per-subgroup metric bar chart

생성 task:
- 생성 결과 sample 이미지/오디오
- Quality metric 분포

모델 내부 분석 (가능한 경우):
- Feature 분포 (중간 layer output의 histogram/t-SNE)
- Attention map / activation 시각화
- Score별 sample 예시 (high confidence correct, high confidence wrong, borderline)

시각화는 `results/runs/{timestamp}/plots/`에 저장.
matplotlib이 없거나 시각화 불가능한 경우 skip — 실험 자체를 중단하지 않는다.

## Post-run: 분석 스크립트
프로젝트에 분석 스크립트가 있으면 실행.

## Output layout
모든 결과물은 해당 run 디렉토리에 저장한다. run 하나가 완전한 기록이 되어야 한다.

```
results/runs/{timestamp}/
├── metrics.json              # primary/secondary metric 값
├── config_snapshot.yaml      # 이 run에 사용된 config 복사본
├── git_commit.txt            # 코드 버전
├── stdout.log                # 전체 stdout/stderr
├── plots/                    # 시각화
│   ├── ...
│   └── ...
└── analysis/                 # result-analyzer가 생성 (post-run)
    ├── sanity_checks.json    # 어떤 check가 통과/실패했는지
    ├── deep_analysis.md      # 코드/값 수준 분석 결과
    └── debug_findings.md     # 발견된 문제와 fix 제안
```

- results/registry.json도 함께 업데이트
