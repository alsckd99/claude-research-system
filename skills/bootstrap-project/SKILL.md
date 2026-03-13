# Skill: bootstrap-project

## Trigger
- "새 프로젝트 만들어줘", "프로젝트 시작해줘"
- project directory is empty

## Purpose
사용자의 objective를 받아서 연구 프로젝트를 만들고, 자동 개선 루프를 돌린다.

---

## Core principle: 연구는 비선형이다

어느 단계에서든 새 발견이 있으면 기존 계획을 수정한다.
변경 시 `docs/research_log.md`에 기록:
```
## {date} — Direction change
Trigger: {무엇을 하다가 발견했는지}
Found: {무엇을 발견했는지}
Impact: {기존 계획에서 무엇이 바뀌는지}
```

아래 Phase 0~7은 최초 셋업 순서. 한번 loop에 진입하면 분석, 탐색, 구현, 실험이 유기적으로 반복.

---

## Phase 0: System check

1. GPU 확인 — `python scripts/server_utils.py`로 GPU 상태 + 다른 사용자 확인
   - 다른 사용자가 사용 중인 GPU는 자동 회피
   - 가용 GPU가 없으면 그때만 사용자에게 질문

## Phase 1: Collect info

필수 질문 (한 번에 모아서, **추가 확인 질문 하지 않는다**):
1. Objective — 한 문장
2. Train dataset — 경로 또는 이름
3. Test dataset — 경로 또는 이름

## Phase 2: Initial research + Data audit

1. 관련 논문에서 기존 모델/코드 검색 (직접 설계 X)
2. 찾은 논문의 참조도 따라감
3. 모델 선정 이유를 `docs/model_selection_log.md`에 기록
4. data-auditor skill로 데이터셋 분석

사용자에게 간단히 보고하고 **확인을 기다리지 않고 바로 진행**.

## Phase 3: Setup

1. Project structure 생성
2. Clone repos & download checkpoints
3. Register: `models/model_registry.json`
4. conda 환경 생성

## Phase 4: Evaluation framework

Objective와 dataset에 맞는 evaluation metrics 설계.
Sanity checks from `.claude/skills/result-analyzer/sanity_checks.md` 포함.
Output: `docs/eval_policy.md`

## Phase 5: Implement & run baseline

Engineer agent → pipeline 구현, Runner → baseline 실행

## Phase 6: Safety gate — DO NOT SKIP

1. `pytest -q` passes
2. `docs/eval_policy.md` has confirmed primary metric
3. At least 1 completed evaluation in results/
4. Sanity checks pass on baseline results

## Phase 7: Improvement loop (continuous, background)

파이프라인 세팅 후 자동으로 continuous 모드 진입. 사용자에게 물어보지 않고 반복.

매 iteration:
1. 분석: 결과 + sanity checks로 약점 파악
2. 이미 완료된 method는 스킵
3. 탐색: 약점 해결 논문 검색 (3 iteration마다 또는 실패 시)
4. 구현: 한 번에 하나씩
5. 실행 → 비교 → 개선/revert → Repeat

Escalation (자동 대응):
- 2+ loops 개선 없음 → literature search
- Same error 3+ times → 다음 method로 전환
- pytest fails → fix 후 재실행

## Notes
- 한 번에 하나의 변경만 적용
- pretrain checkpoint 있으면 우선 사용
- 프로젝트 마무리 시 report-writer skill로 리포트 생성
