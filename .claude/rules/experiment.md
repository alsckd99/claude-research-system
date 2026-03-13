---
paths:
  - "scripts/**/*.py"
  - "src/**/*.py"
  - "tests/**/*.py"
  - "configs/**/*.yaml"
---

# Experiment & Coding Rules

- Python 3.10+, type hints 필수, docstring은 public 함수만
- config 값은 configs/*.yaml에서 — 하드코딩 금지
- 새 기능은 반드시 테스트와 함께 추가
- 새 의존성 추가 시 requirements.txt도 함께 수정
- 커밋 전 `pytest -q tests/` 실행
- 한 번에 하나의 변경만 적용 — 여러 method 동시 적용 금지
- train/test data split 변경 금지
- metric 변경은 literature evidence 필수 (policy-evolver 경유)
