"""
claude-research-system: new project initializer.

Usage:
    python orchestrator/new_project.py \
        --name my_project \
        --objective "one sentence describing what you want to achieve" \
        --output /path/to/project
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
> This section is never modified automatically. Request a human to change it.

### Objective
{objective}

### GPU Configuration
- CUDA_VISIBLE_DEVICES: {gpus}
- All training and evaluation commands must set this environment variable

### Required Validation
1. Reproduce baseline before implementing any new method
2. `pytest -q` must pass after every code change
3. Save results under `results/runs/{{timestamp}}/` for every run

### Forbidden Actions
- Hardcoding (all config values go in configs/*.yaml)
- `git push --force` / `rm -rf`
- Running experiments without a passing test suite

---

## MUTABLE RESEARCH POLICY
> Modified only by policy-evolver skill + policy_guard agent after approval.

### Primary Metric
TBD — researcher agent will determine from related papers

### Secondary Metrics
TBD — researcher agent will determine from related papers

### Active Baselines
_literature-scout skill fills this in_

### Known Failure Taxonomy
_result-analyzer skill accumulates patterns here_

### Next Experiment Candidates
_proposed by researcher + result-analyzer, approved by reviewer before execution_
"""

BASE_CONFIG_TEMPLATE = """\
project_name: "{name}"
primary_metric: "TBD"
gpus: "{gpus}"
seed: 42

data:
  train_path: "data/train"
  val_path: "data/val"
  test_path: "data/test"

# Add project-specific config sections as needed.
# The sections below are common defaults — modify or remove based on your project.
"""


def copy_scripts(project_dir: Path) -> None:
    src_scripts = RESEARCH_OS_ROOT / "templates" / "project-skeleton" / "scripts"
    dst_scripts = project_dir / "scripts"
    dst_scripts.mkdir(exist_ok=True)

    if src_scripts.exists():
        for script in src_scripts.glob("*.py"):
            shutil.copy(script, dst_scripts / script.name)
            print(f"  [copy] scripts/{script.name}")
    else:
        (dst_scripts / "README.md").write_text(
            "# Scripts\n\nCopy or symlink research-os template scripts here:\n"
            f"\n    cp {RESEARCH_OS_ROOT}/templates/project-skeleton/scripts/*.py scripts/\n"
        )


def create_project(name: str, objective: str, gpus: str, project_dir: Path) -> None:
    print(f"\n[new_project] creating: {name}")
    print(f"[new_project] path: {project_dir}")

    dirs = [
        "docs", "configs",
        "data", "models",
        "results/runs",
        "src", "tests", "scripts",
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # CLAUDE.md
    (project_dir / "CLAUDE.md").write_text(
        CLAUDE_MD_TEMPLATE.format(objective=objective, gpus=gpus)
    )
    print("  [created] CLAUDE.md")

    # configs/base.yaml
    (project_dir / "configs" / "base.yaml").write_text(
        BASE_CONFIG_TEMPLATE.format(name=name, gpus=gpus)
    )
    print("  [created] configs/base.yaml")

    # docs/
    (project_dir / "docs" / "eval_policy.md").write_text(
        "# Evaluation Policy\n\n"
        "## Primary Metric\nTBD — researcher agent will determine from related papers\n\n"
        "## Secondary Metrics\nTBD\n\n"
        "## Test Protocol\nTBD — researcher agent will determine from related papers\n"
    )
    (project_dir / "docs" / "baselines.md").write_text(
        "# Baselines\n\n_literature-scout skill fills this in._\n"
    )
    (project_dir / "docs" / "research_log.md").write_text(
        "# Research Log\n\n_Direction changes and discoveries are recorded here._\n"
    )
    (project_dir / "docs" / "model_selection_log.md").write_text(
        "# Model Selection Log\n\n_Each model selection with reasoning is recorded here._\n"
    )
    print("  [created] docs/")

    # results/
    (project_dir / "results" / "registry.json").write_text(
        json.dumps({"runs": []}, indent=2)
    )
    print("  [created] results/")

    # src/ skeleton — only __init__.py, structure will be created by engineer
    (project_dir / "src" / "__init__.py").touch()
    print("  [created] src/")

    # tests/ skeleton
    (project_dir / "tests" / "__init__.py").touch()
    (project_dir / "tests" / "test_smoke.py").write_text(
        '"""Smoke tests"""\n\ndef test_placeholder():\n    assert True\n'
    )
    print("  [created] tests/")

    # scripts/
    copy_scripts(project_dir)

    cuda_prefix = f"CUDA_VISIBLE_DEVICES={gpus} " if gpus != "cpu" else ""
    (project_dir / "Makefile").write_text(
        ".PHONY: test experiment\n\n"
        f"GPUS ?= {gpus}\n\n"
        "test:\n\tpytest -q tests/\n\n"
        "experiment:\n\t@echo 'Configure run command in this Makefile based on your project'\n\n"
    )

    # pyproject.toml
    (project_dir / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n'
        'dependencies = ["pyyaml>=6", "numpy>=1.24"]\n\n'
        '[project.optional-dependencies]\ndev = ["pytest>=7.4"]\n\n'
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
    )

    (project_dir / "requirements.txt").write_text(
        "pyyaml>=6\nnumpy>=1.24\npytest>=7.4\n"
    )

    print(f"\n[new_project] done: {project_dir}")
    print(f"\nnext steps:")
    print(f"  1. cd {project_dir}")
    print(f"  2. researcher agent will design the evaluation framework from papers")
    print(f"  3. engineer agent will implement the pipeline")


def main():
    parser = argparse.ArgumentParser(description="claude-research-system new project initializer")
    parser.add_argument("--name", required=True, help="project name")
    parser.add_argument("--objective", default="[describe what you want to achieve]",
                        help="one sentence describing the project objective")
    parser.add_argument("--gpus", default="0",
                        help="which GPUs to use: 0 / 0,1 / 0,1,2 / all / cpu")
    parser.add_argument("--output", default=".", help="output path")
    args = parser.parse_args()

    project_dir = Path(args.output)
    project_dir.mkdir(parents=True, exist_ok=True)
    create_project(name=args.name, objective=args.objective, gpus=args.gpus, project_dir=project_dir)


if __name__ == "__main__":
    main()
