# Skill: bootstrap-project

## Trigger
- "새 프로젝트 만들어줘", "프로젝트 시작해줘"
- project directory is empty

## Purpose
사용자의 objective를 받아서 연구 프로젝트를 만들고, 자동 개선 루프를 돌린다.

---

## Core principle: 연구는 비선형이다

논문을 찾다가 새로운 기법을 발견하면 그게 곧 새 방향이 된다.
결과를 분석하다가 논문에서 본 기법이 떠오르면 그걸 적용한다.
모델을 세팅하다가 README에서 관련 논문을 발견하면 그것도 후보에 넣는다.

어느 단계에서든 새 발견이 있으면 기존 계획을 수정한다.
변경 시 `docs/research_log.md`에 기록:
```
## {date} — Direction change
Trigger: {무엇을 하다가 발견했는지}
Found: {무엇을 발견했는지}
Impact: {기존 계획에서 무엇이 바뀌는지}
```

아래 Phase 0~7은 최초 셋업 순서이다. 한번 loop에 진입하면 순서는 의미 없고,
분석, 탐색, 구현, 실험이 유기적으로 반복된다.

---

## Phase 0: System check (프로젝트 시작 전)

프로젝트 작업에 앞서 자동으로 수행 (사용자에게 묻지 않는다):

1. system-updater — 최신 업데이트 확인. 중대 업데이트만 사용자에게 알림, 나머지는 자동 적용.
2. GPU 확인 — `python scripts/server_utils.py`로 GPU 상태 + 다른 사용자 확인.
   - **다른 사용자가 사용 중인 GPU는 자동 회피** (`find_free_gpus(avoid_other_users=True)`)
   - 비어있는 GPU를 자동 선택. 가용 GPU가 없으면 그때만 사용자에게 질문.

---

## Phase 1: Collect info

사용자에게 질문은 **최소한으로** — objective에서 유추 가능한 것은 묻지 않는다.

필수 질문 (한 번에 모아서):
1. Objective — 한 문장
2. Train dataset — 학습에 쓸 데이터 경로 또는 이름
3. Test dataset — 평가에 쓸 데이터 경로 또는 이름 (train과 같을 수 있음)

질문하지 않는 것: 모델, metric, 방법론, GPU (전부 자동)
**추가 확인 질문 하지 않는다** — 큰 문제 없으면 바로 진행.

---

## Phase 2: Initial research (researcher agent) + Data audit (data-auditor skill)

Objective를 바탕으로 첫 탐색을 수행한다.

1. 관련 논문에서 기존 모델/코드를 검색한다 (직접 설계하지 않는다)
   - 최신 모델 우선 (최근 1~2년)
   - 코드 공개 + checkpoint 있는 모델 우선
   - 각 모델이 서로 다른 고유 특성을 가져야 한다
2. 찾은 논문을 읽으면서 추가로 참조된 모델이나 기법이 있으면 그것도 따라간다
3. 모델 선정 이유를 `docs/model_selection_log.md`에 기록 (왜 이 모델인지, 대안은 뭐였는지)
4. 탐색 결과를 바탕으로 프로젝트의 출발점과 방향을 정리
5. 데이터 감사 — data-auditor skill로 데이터셋 분석 (분포, 불균형, 품질, leakage)
   - 결과는 Phase 4 eval_policy 설계에 반영

사용자에게 간단히 보고하고 **확인을 기다리지 않고 바로 진행한다**:
```
## Research Summary
출발점: {어떤 모델/코드를 base로 쓸지, 왜}
개선 후보: {1-3개 핵심만}
→ 셋업 진행합니다.
```

모든 후보를 `docs/baselines.md`에 기록.

---

## Phase 3: Setup

확인 없이 바로 진행:

1. Project structure 생성 — `src/` 구조는 연구 결과에 맞게 자유롭게 결정
2. Clone repos & download checkpoints
3. Usage mode 판단: pretrained 그대로 / fine-tune / train from scratch
4. Register: `models/model_registry.json`
5. conda 환경 생성

셋업 중 README, 코드, 논문 등에서 새 발견이 있으면 Phase 2 결과를 수정한다.

---

## Phase 4: Evaluation framework (researcher agent)

Objective와 dataset에 맞는 evaluation metrics 설계.
Sanity checks from `.claude/skills/result-analyzer/sanity_checks.md` 포함.

Output: `docs/eval_policy.md`

---

## Phase 5: Implement & run baseline

Engineer agent:
- Objective, 모델, baseline approach, eval_policy에 맞게 pipeline 구현
- `src/train.py`, `src/evaluate.py` 구현 (run_experiment.py가 호출하는 진입점)
- Tests must pass

Runner agent:
- Baseline 실행, 결과 저장 (`results/runs/`)

---

## Phase 6: Safety gate — DO NOT SKIP

1. `pytest -q` passes
2. `docs/eval_policy.md` has confirmed primary metric
3. At least 1 completed evaluation in results/
4. Sanity checks pass on baseline results

If any fails, fix before proceeding.

---

## Phase 7: Improvement loop (continuous, background)

**파이프라인이 세팅되면 자동으로 continuous 모드에 진입한다.**
사용자에게 물어보지 않고 계속 반복한다.

```bash
# 자동으로 이 명령이 실행됨 (백그라운드 데몬)
python orchestrator/scheduler.py --project . --mode continuous
```

매 iteration:
1. 분석: 결과 + sanity checks로 현재 약점 파악
2. **이미 완료된 method는 스킵** — 새 method만 실험
3. 탐색: 약점을 해결하는 논문 검색 (3 iteration마다 또는 실패 시)
4. 구현: 한 번에 하나씩 적용
5. 실행: 실험
6. 비교: 개선됨이면 새 baseline / 악화됨이면 revert, 다음 후보
7. Repeat — **멈추지 않는다**

**중간에 확인 질문 하지 않는다** — 큰 문제(pytest fail, 5회 연속 실패) 없으면 자동 진행.

새 기법 적용 시 가능하면 해당 논문의 방법을 먼저 원본대로 재현 (within 5%) 후 적용.

Escalation triggers (자동 대응, 멈추지 않음):
- 2+ loops 개선 없음 → literature search 자동 트리거
- Same error 3+ times → 다음 method로 자동 전환
- 5+ consecutive failures → literature search 후 재시도
- pytest fails → fix 시도 후 재실행

---

## Notes
- 이 skill은 프레임워크만 제공한다. 내용은 전부 objective와 논문 탐색에서 동적으로 결정된다.
- 연구 중 발견한 것은 언제든 계획을 바꿀 수 있다 — `docs/research_log.md`에 기록.
- 한 번에 하나의 변경만 적용 — 여러 component 동시 적용 시 ablation-planner skill로 기여도 검증
- pretrain checkpoint 있으면 우선 사용
- 데이터셋 불균형은 data-auditor + eval framework에서 선제 대응
- 프로젝트 마무리 또는 중간 정리 시 report-writer skill로 전체 리포트 생성
- 환경 문제 발생 시 environment_manager agent 활용
