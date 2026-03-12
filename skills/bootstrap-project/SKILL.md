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

**어느 단계에서든 새 발견이 있으면 기존 계획을 수정한다.**
변경 시 `docs/research_log.md`에 기록:
```
## {date} — Direction change
Trigger: {무엇을 하다가 발견했는지}
Found: {무엇을 발견했는지}
Impact: {기존 계획에서 무엇이 바뀌는지}
```

아래 Phase 1~7은 **최초 셋업 순서**이다. 한번 loop에 진입하면 순서는 의미 없고,
분석 → 탐색 → 구현 → 실험이 유기적으로 반복된다.

---

## Phase 1: Collect info

사용자에게 질문:
1. **Objective** — 한 문장
2. **Train dataset** — 학습에 쓸 데이터 경로 또는 이름
3. **Test dataset** — 평가에 쓸 데이터 경로 또는 이름 (train과 같을 수 있음)
4. **GPU** — 사용 가능한 GPU (예: 0 / 0,1 / all / cpu)

질문하지 않는 것: 모델, metric, 방법론 (전부 자동 탐색)

---

## Phase 2: Initial research (researcher agent) + Data audit (data-auditor skill)

Objective를 바탕으로 첫 탐색을 수행한다.

1. 관련 논문/모델/기법을 검색
2. 찾은 논문을 읽으면서 추가로 참조된 기법이나 모델이 있으면 그것도 따라간다
3. 탐색 결과를 바탕으로 프로젝트의 출발점과 방향을 정리
4. **데이터 감사** — data-auditor skill로 데이터셋 분석 (분포, 불균형, 품질, leakage)
   - 결과는 Phase 4 eval_policy 설계에 반영

사용자에게 보고:
```
## Research Summary

### 출발점: {어떤 모델/코드를 base로 쓸지, 왜}
### 개선 후보 (priority order):
1. {기법/논문} — {왜}
2. ...

### 탐색 중 발견한 것:
- {논문 A에서 기법 X를 쓰고 있었는데, 이것도 적용 가능}
- {모델 B의 README에서 관련 체크포인트 발견}
- ...

이 방향으로 진행할까요?
```

모든 후보를 `docs/baselines.md`에 기록.

---

## Phase 3: Setup

사용자 확인 후:

1. **Project structure 생성** — `src/` 구조는 연구 결과에 맞게 자유롭게 결정
2. **Clone repos & download checkpoints**
3. **Usage mode 판단**: pretrained 그대로 / fine-tune / train from scratch
4. **Register**: `models/model_registry.json`
5. **conda 환경 생성**

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
- `scripts/run_all.sh`, `scripts/improve_loop.py` 포함
- Tests must pass

Runner agent:
- Baseline 실행, 결과 저장 (`results/runs/`)

---

## Phase 6: Safety gate — DO NOT SKIP

1. `pytest -q` passes
2. `docs/eval_policy.md` has confirmed primary metric
3. At least 1 completed evaluation in results/
4. Sanity checks pass on baseline results

If any fails → fix before proceeding.

---

## Phase 7: Improvement loop

매 iteration:
1. **분석**: 결과 + sanity checks → 현재 약점
2. **탐색**: 약점을 해결하는 논문 검색
   - 논문을 읽다가 다른 유용한 기법을 발견하면 그것도 후보에 추가
   - 관련 논문의 reference를 따라가다 더 좋은 접근을 발견할 수 있음
3. **구현**: 한 번에 하나씩 적용
4. **실행**: 실험
5. **비교**: 개선됨 → 새 baseline / 악화됨 → revert, 다음 후보
6. Repeat

새 기법 적용 시 가능하면 해당 논문의 방법을 먼저 원본대로 재현 (within 5%) 후 적용.

**Escalation triggers:**
- 2+ loops 개선 없음
- Same error 3+ times
- Sanity check flag 3+ consecutive
- pytest fails → 즉시 중단

---

## Notes
- 이 skill은 프레임워크만 제공한다. 내용은 전부 objective와 논문 탐색에서 동적으로 결정된다.
- 연구 중 발견한 것은 언제든 계획을 바꿀 수 있다 — `docs/research_log.md`에 기록.
- 한 번에 하나의 변경만 적용 — 여러 component 동시 적용 시 ablation-planner skill로 기여도 검증
- pretrain checkpoint 있으면 우선 사용
- 데이터셋 불균형은 data-auditor + eval framework에서 선제 대응
- 프로젝트 마무리 또는 중간 정리 시 report-writer skill로 전체 리포트 생성
- 환경 문제 발생 시 environment_manager agent 활용
