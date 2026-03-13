---
name: bootstrap-project
description: New project initialization — collect info, research, setup, run baseline, enter loop
disable-model-invocation: false
---

# Skill: bootstrap-project

## Contract
- Phase 6 safety gate를 반드시 통과한 후에만 improvement loop 진입.
- 사용자에게 질문은 Phase 1에서 한 번만. 이후 추가 확인 질문 하지 않는다.
- 모든 모델 선정 이유를 `docs/model_selection_log.md`에 기록한다.

## Trigger
- "새 프로젝트 만들어줘", "프로젝트 시작해줘"
- project directory is empty

## Core principle: 연구는 비선형이다

어느 단계에서든 새 발견이 있으면 기존 계획을 수정한다.
변경 시 `docs/research_log.md`에 기록.

Phase 0~7은 최초 셋업 순서. Loop 진입 후에는 분석/탐색/구현/실험이 유기적으로 반복.

---

## Phase 0: System check

GPU 확인 — `python scripts/server_utils.py`. 다른 사용자 GPU 자동 회피. 가용 GPU 없으면 그때만 질문.

## Phase 1: Collect info

필수 질문 (한 번에 모아서):
1. Objective — 한 문장
2. Train dataset — 경로 또는 이름
3. Test dataset — 경로 또는 이름

## Phase 2: Initial research + Data audit

1. 관련 논문에서 기존 모델/코드 검색 (직접 설계 X)
2. 찾은 논문의 참조도 따라감
3. 모델 선정 이유를 `docs/model_selection_log.md`에 기록
4. data-auditor skill로 데이터셋 분석

보고 후 **확인을 기다리지 않고 바로 진행**.

## Phase 3: Setup

1. Project structure 생성
2. Clone repos & download checkpoints
3. Register: `models/model_registry.json`
4. conda 환경 생성

## Phase 4: Evaluation framework

eval metrics 설계. Sanity checks from `sanity_checks.md` 포함. Output: `docs/eval_policy.md`

## Phase 5: Implement & run baseline

Engineer agent → pipeline 구현 → baseline 실행

## Phase 6: Safety gate — DO NOT SKIP

1. `pytest -q` passes
2. `docs/eval_policy.md` has confirmed primary metric
3. At least 1 completed evaluation in results/
4. Sanity checks pass on baseline results

## Phase 7: Improvement loop (continuous, background)

자동으로 continuous 모드 진입. 매 iteration:
1. 분석 → 2. 완료된 method 스킵 → 3. 논문 검색 (3iter마다) → 4. 구현 → 5. 실행/비교/개선 or revert → Repeat

Escalation: 2+ loops 개선없음→literature search, error 3+회→다음 method, pytest fail→fix후 재실행
