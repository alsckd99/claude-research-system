# Skill: bootstrap-project

## Trigger
- "새 프로젝트 만들어줘", "프로젝트 시작해줘"
- project directory is empty

## Purpose
사용자의 objective를 받아서, 연구 탐색 → 구현 → 실험 → 개선 루프까지
자동으로 수행하는 연구 프로젝트를 만든다.

---

## Phase 1: Collect info

사용자에게 질문:
1. **Objective** — 한 문장
2. **Train dataset** — 학습에 쓸 데이터 경로 또는 이름
3. **Test dataset** — 평가에 쓸 데이터 경로 또는 이름 (train과 같을 수 있음)
4. **GPU** — 사용 가능한 GPU (예: 0 / 0,1 / all / cpu)

질문하지 않는 것:
- 어떤 모델을 쓸지 (자동 탐색)
- 어떤 metric을 쓸지 (논문 기반 자동 결정)
- 어떤 방법론을 쓸지 (논문 기반 자동 결정)

---

## Phase 2: Objective analysis

Objective를 분석해서 이 프로젝트에 **무엇이 필요한지** 판단한다.

1. Objective에서 핵심 task와 goal을 추출
2. 이 goal을 달성하려면 어떤 연구가 필요한지 판단
3. 판단 결과를 사용자에게 보여주고 확인

```
## Project Analysis

Objective: {objective}
Core task: {무엇을 하는 프로젝트인지}
Research direction: {어떤 연구가 필요한지 — 자유 서술}
What to search: {어떤 모델/논문/기법을 찾아야 하는지}

이 방향으로 진행할까요?
```

### Project structure

```
{project}/
├── CLAUDE.md
├── configs/base.yaml
├── data/                  # immutable inputs
├── models/                # cloned repos + checkpoints
├── results/runs/          # per-iteration results
├── src/                   # objective에 맞게 자유롭게 구성
├── scripts/               # pipeline scripts
├── docs/                  # eval_policy, baselines
└── tests/
```

`src/` 하위 구조는 objective 분석 결과에 따라 자유롭게 결정.

conda 환경 생성:
```bash
conda create -n {project_name} python=3.10 pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
```

---

## Phase 3: Research (researcher agent, parallel tracks)

Phase 2의 분석을 바탕으로 **두 track을 병렬 수행**.

### Track A: Base 탐색

이 프로젝트의 출발점이 되는 모델/코드를 찾는다.
몇 개를, 왜 찾는지는 Phase 2 분석에서 결정된다.

각 후보에 대해:
```
Model: {name}
Paper: {title} ({venue} {year})
GitHub: {url} (stars: {N}, last commit: {date})
Role in this project: {이 프로젝트에서 어떤 역할인지}
Strengths: {이 task에서 잘하는 것}
Weaknesses: {한계점}
Checkpoint: available / needs training / needs fine-tuning
```

### Track B: 개선 방향 탐색

이 프로젝트의 성능을 높일 수 있는 기법/논문을 찾는다.
무엇을 찾을지는 Phase 2 분석과 Track A의 모델 약점에서 결정된다.

각 후보에 대해:
```
Improvement: {name}
Paper: {title} ({venue} {year})
What it changes: {무엇을 바꾸는 기법인지}
Why applicable: {이 프로젝트의 어떤 문제를 해결하는지}
Implementation complexity: low / medium / high
Expected impact: {근거와 함께}
```

모든 후보를 `docs/baselines.md`에 기록. 초기 baseline 1개만 선정.

사용자에게 연구 결과 보고 후 확인.

---

## Phase 4: Setup

사용자 확인 후:

1. **Clone repos**: `git clone {repo_url} models/{model_name}`
2. **Checkpoint download**: README 읽고 다운로드 (HuggingFace / GDrive / wget / 수동)
3. **Usage mode 판단**: pretrained 그대로 / fine-tune / train from scratch
4. **Register**: `models/model_registry.json`에 기록

---

## Phase 5: Evaluation framework (researcher agent)

"Objective: '{objective}'.
Models: {from model_registry.json}.
Design evaluation metrics.
Include sanity checks from .claude/skills/result-analyzer/sanity_checks.md.
Pay special attention to dataset class balance."

Output: `docs/eval_policy.md`

---

## Phase 6: Implement (engineer agent)

"Objective: '{objective}'.
Models: see model_registry.json.
Baseline: {from Track B}.
Evaluation: see docs/eval_policy.md.

Implement the pipeline. src/ 구조와 scripts/는 objective에 맞게 설계.
Each script independently runnable.
Implement scripts/run_all.sh and scripts/improve_loop.py.
Tests must pass."

---

## Phase 7: Run baseline (runner agent)

"Run the full pipeline. Save results to results/runs/."

---

## Phase 7.5: Safety gate — DO NOT SKIP

Verify:
1. `pytest -q` passes
2. docs/eval_policy.md has confirmed primary metric
3. At least 1 completed evaluation in results/
4. models/model_registry.json has at least 1 model with status "ready"
5. Sanity checks pass on baseline results

If any fails → fix before proceeding.

---

## Phase 8: Autonomous improvement loop

매 iteration마다 결과를 분석하고, 그 분석에서 나온 약점을 해결하는 논문을 찾아서 적용한다.

Loop:
1. **result-analyzer**: 결과 분석 + sanity checks → 현재 약점 파악
2. **literature-scout**: 약점을 해결하는 논문 검색 (무엇을 찾을지는 분석 결과가 결정)
3. **method-reviser**: 논문의 기법을 구현 (한 번에 하나씩)
4. **experiment-runner**: 실행
5. **result-analyzer**: 비교, 다음 방향 결정
6. Repeat

#### Phase A (reproduction)
새 기법 적용 전, 해당 논문의 방법을 원본대로 재현:
- 논문의 보고 수치와 비교 (within 5%)
- 재현 실패 → 엔지니어링 이슈 해결
- 재현 성공 → gap analysis

#### Phase B (적용 & 개선)
- 재현된 기법을 프로젝트에 적용
- 개선됨 → 새 baseline, 다음 약점 분석
- 악화됨 → revert, 다음 후보
- 한 번에 하나의 변경만 적용

**Escalation triggers:**
- stall_count >= 2: 2+ loops 개선 없음
- Same error 3+ times
- Sanity check flag 3+ consecutive
- pytest fails → 즉시 중단

---

## Notes
- 프로젝트마다 필요한 연구, 구조, 개선 방향이 전부 다르다 — 이 skill은 프레임워크만 제공하고, 내용은 objective 분석에서 동적으로 결정된다
- 한 번에 하나의 변경만 적용 (ablation 가능)
- pretrain checkpoint 있으면 우선 사용
- 데이터셋 불균형은 eval framework에서 선제 대응
