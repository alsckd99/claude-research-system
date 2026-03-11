"""
research-os: 새 프로젝트 초기화기.

사용법:
    python orchestrator/new_project.py \
        --name my_project \
        --mission "딥페이크 탐지 모델 구현" \
        --metric AUROC \
        --domain image \
        --gpu-memory 24 \
        --latency-ms 100 \
        --output /path/to/project

효과:
    지정 경로에 research-os 표준 최소 구조 생성.
    .claude/ 디렉토리는 생성하지 않는다 (전역 플러그인이 담당).
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path


RESEARCH_OS_ROOT = Path(os.environ.get("RESEARCH_OS_ROOT", Path(__file__).parent.parent))

CLAUDE_MD_TEMPLATE = """\
# CLAUDE.md

---

## IMMUTABLE CORE
> 이 구역은 절대 자동 수정하지 않는다. 변경 시 사람에게 요청.

### Mission
{mission}

### Primary Metric
- **Primary**: {metric}
- 모든 비교는 동일 데이터 분할 + 동일 seed 기준

### Hard Constraints
- GPU 메모리 한도: {gpu_memory}GB
- 추론 지연시간 한도: {latency_ms}ms
- 데이터 도메인: {domain}

### Required Validation
1. baseline 재현 먼저 — 새 방법 구현 전 baseline 수치 재현
2. 코드 수정 후 `pytest -q` 통과
3. 실험마다 `experiments/runs/{{timestamp}}/` 아래 결과 저장

### Forbidden Actions
- primary metric 교체 (사람 승인 없이)
- baseline 없이 새 구조 먼저 실험
- 하드코딩 (설정값은 configs/*.yaml만)
- `git push --force` / `rm -rf`

---

## MUTABLE RESEARCH POLICY
> policy-evolver skill + policy_guard agent가 승인 후 수정 가능.

### Secondary Metrics
- F1 (macro)
- Latency (p95)
- GPU memory (peak)

### Active Baselines
- *literature-scout skill이 채워나간다*

### Known Failure Taxonomy
- *result-analyzer skill이 발견한 패턴을 누적*

### Next Experiment Candidates
- *researcher + result-analyzer 제안, reviewer 승인 후 실행*
"""

BASE_CONFIG_TEMPLATE = """\
project_name: "{name}"
primary_metric: "{metric}"
seed: 42

data:
  train_path: "data/train"
  val_path: "data/val"
  test_path: "data/test"
  num_workers: 4

model:
  name: "baseline"

training:
  epochs: 50
  batch_size: 32
  learning_rate: 1.0e-4
  optimizer: "adam"
  weight_decay: 1.0e-4
  scheduler: "cosine"
  early_stopping_patience: 10

evaluation:
  metrics: ["{metric}", "f1_macro", "latency_p95", "gpu_memory"]
  save_best: true
"""


def copy_scripts(project_dir: Path) -> None:
    """research-os의 공용 스크립트를 프로젝트 scripts/에 복사."""
    src_scripts = RESEARCH_OS_ROOT / "templates" / "project-skeleton" / "scripts"
    dst_scripts = project_dir / "scripts"
    dst_scripts.mkdir(exist_ok=True)

    if src_scripts.exists():
        for script in src_scripts.glob("*.py"):
            shutil.copy(script, dst_scripts / script.name)
            print(f"  [copy] scripts/{script.name}")
    else:
        # 스크립트 없으면 안내
        (dst_scripts / "README.md").write_text(
            "# Scripts\n\nresearch-os 공용 스크립트를 여기에 복사하거나 symlink하세요.\n"
            f"\n    cp {RESEARCH_OS_ROOT}/templates/project-skeleton/scripts/*.py scripts/\n"
        )


def create_project(
    name: str,
    mission: str,
    metric: str,
    domain: str,
    gpu_memory: int,
    latency_ms: int,
    project_dir: Path,
) -> None:
    print(f"\n[new_project] 생성: {name}")
    print(f"[new_project] 경로: {project_dir}")

    # 디렉토리 구조
    dirs = [
        "docs", "configs",
        "experiments/runs", "experiments/reports",
        "src", "tests", "scripts", "data",
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # CLAUDE.md
    (project_dir / "CLAUDE.md").write_text(
        CLAUDE_MD_TEMPLATE.format(
            mission=mission, metric=metric, domain=domain,
            gpu_memory=gpu_memory, latency_ms=latency_ms,
        )
    )
    print("  [created] CLAUDE.md")

    # configs/base.yaml
    (project_dir / "configs" / "base.yaml").write_text(
        BASE_CONFIG_TEMPLATE.format(name=name, metric=metric)
    )
    print("  [created] configs/base.yaml")

    # docs/
    (project_dir / "docs" / "eval_policy.md").write_text(
        f"# Evaluation Policy\n\n## Primary Metric\n**{metric}** — 변경 불가\n\n"
        "## Secondary Metrics\n- f1_macro\n- latency_p95\n- gpu_memory\n\n"
        "## Test Protocol\n- seed: 42\n- split: 70/15/15\n- 최소 3 seed 평균\n"
    )
    (project_dir / "docs" / "baselines.md").write_text(
        "# Baselines\n\n_literature-scout skill이 여기에 방법을 추가합니다._\n"
    )
    print("  [created] docs/")

    # experiments/
    (project_dir / "experiments" / "registry.json").write_text(
        json.dumps({"runs": []}, indent=2)
    )
    for report in [
        "latest.md", "error_analysis.md", "next_actions.md",
        "proposed_policy_changes.md", "policy_changelog.md",
    ]:
        path = project_dir / "experiments" / "reports" / report
        if not path.exists():
            path.write_text(f"# {report.replace('.md','').replace('_',' ').title()}\n\n_초기화됨_\n")
    print("  [created] experiments/")

    # src/ 골격
    (project_dir / "src" / "__init__.py").touch()
    for f in ["model.py", "dataset.py", "train.py", "evaluate.py", "utils.py"]:
        p = project_dir / "src" / f
        if not p.exists():
            p.write_text(f'"""\n{f} — {name}\nTODO: 구현\n"""\n')
    print("  [created] src/")

    # tests/ 골격
    (project_dir / "tests" / "__init__.py").touch()
    (project_dir / "tests" / "test_smoke.py").write_text(
        '"""Smoke tests"""\nimport pytest\n\ndef test_placeholder():\n    assert True\n'
    )
    print("  [created] tests/")

    # scripts/ 복사
    copy_scripts(project_dir)

    # Makefile
    (project_dir / "Makefile").write_text(
        ".PHONY: install test lint experiment analyze\n\n"
        "install:\n\tpip install -e '.[dev]'\n\n"
        "test:\n\tpytest -q tests/\n\n"
        "lint:\n\truff check src/ && black --check src/\n\n"
        "experiment:\n\t@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \\\n"
        "\tpython scripts/run_experiment.py --config configs/base.yaml --output experiments/runs/$$TIMESTAMP\n\n"
        "analyze:\n\tpython scripts/analyze_failures.py\n"
        "\tpython scripts/summarize_results.py\n"
        "\tpython scripts/propose_next_steps.py\n\n"
        "loop: test experiment analyze\n"
    )

    # pyproject.toml
    (project_dir / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n'
        'dependencies = ["pyyaml>=6", "numpy>=1.24"]\n\n'
        '[project.optional-dependencies]\ndev = ["pytest>=7.4", "ruff>=0.1", "black>=23"]\n\n'
        '[tool.ruff]\nline-length = 100\ntarget-version = "py311"\n\n'
        '[tool.black]\nline-length = 100\n\n'
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
    )

    (project_dir / "requirements.txt").write_text(
        "pyyaml>=6\nnumpy>=1.24\npytest>=7.4\nruff>=0.1\nblack>=23\n"
        "# torch>=2.1  # 필요 시 추가\n"
    )

    print(f"\n[new_project] 완료!")
    print(f"\n다음 할 일:")
    print(f"  1. cd {project_dir}")
    print(f"  2. pip install -e '.[dev]'")
    print(f"  3. src/ 구현")
    print(f"  4. make test && make experiment")


def main():
    parser = argparse.ArgumentParser(description="research-os 새 프로젝트 초기화")
    parser.add_argument("--name", required=True, help="프로젝트 이름")
    parser.add_argument("--mission", default="[미션을 입력하세요]", help="프로젝트 미션 한 문장")
    parser.add_argument("--metric", default="AUROC", help="Primary metric")
    parser.add_argument("--domain", default="image", help="데이터 도메인")
    parser.add_argument("--gpu-memory", type=int, default=24, help="GPU 메모리 한도 (GB)")
    parser.add_argument("--latency-ms", type=int, default=100, help="지연시간 한도 (ms)")
    parser.add_argument("--output", default=".", help="프로젝트 생성 경로")
    args = parser.parse_args()

    project_dir = Path(args.output)
    project_dir.mkdir(parents=True, exist_ok=True)

    create_project(
        name=args.name,
        mission=args.mission,
        metric=args.metric,
        domain=args.domain,
        gpu_memory=args.gpu_memory,
        latency_ms=args.latency_ms,
        project_dir=project_dir,
    )


if __name__ == "__main__":
    main()
