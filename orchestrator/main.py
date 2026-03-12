"""
research-os autonomous loop orchestrator.

Usage:
    python orchestrator/main.py --project /path/to/project --mode nightly
    python orchestrator/main.py --project /path/to/project --mode full-loop
    python orchestrator/main.py --project /path/to/project --mode analyze-only

Modes:
    analyze-only  : analyze + update reports only (no experiments)
    nightly       : analyze -> 1 experiment -> re-analyze
    full-loop     : analyze -> N experiments -> literature -> policy -> agent analysis

Requirements:
    pip install anthropic pyyaml requests
    export ANTHROPIC_API_KEY=...
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


RESEARCH_OS_ROOT = Path(os.environ.get("RESEARCH_OS_ROOT", Path(__file__).parent.parent))


# --- utils ---

def run(cmd: list, cwd: Path, capture: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd, cwd=str(cwd),
        capture_output=capture, text=True
    )
    if not capture:
        return result
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0 and result.stderr:
        print(f"[stderr] {result.stderr.rstrip()}", file=sys.stderr)
    return result


def read_file(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def load_registry(project: Path) -> list:
    reg = project / "results" / "registry.json"
    if not reg.exists():
        return []
    return json.loads(reg.read_text()).get("runs", [])


# --- improvement-based stop condition (Reflexion p.7) ---

def no_improvement(project: Path, k: int) -> bool:
    """Return True if primary_metric has not improved over the last k completed runs."""
    runs = [r for r in load_registry(project) if r.get("status") == "completed"]
    if len(runs) < k:
        return False
    recent = runs[-k:]
    values = [
        r.get("metrics", {}).get("primary_metric", {}).get("value")
        for r in recent
    ]
    values = [v for v in values if v is not None]
    if len(values) < k:
        return False
    # no improvement = best of last k is no better than the first of those k
    return max(values) <= values[0]


# --- reproducibility snapshot ---

def save_reproducibility_snapshot(project: Path, run_dir: Path) -> None:
    """Save environment and agent/skill file hashes for reproducibility."""
    snapshot: dict = {"timestamp": datetime.now().isoformat()}

    env_file = project / "environment.yml"
    if env_file.exists():
        content = env_file.read_text()
        snapshot["environment_yml_hash"] = hashlib.md5(content.encode()).hexdigest()
        (run_dir / "environment.yml").write_text(content)

    claude_dir = project / ".claude"
    for subdir in ["agents", "skills"]:
        d = claude_dir / subdir
        if d.exists():
            hashes = {
                str(f.relative_to(claude_dir)): hashlib.md5(f.read_bytes()).hexdigest()
                for f in sorted(d.rglob("*.md"))
            }
            snapshot[f"{subdir}_hashes"] = hashes

    (run_dir / "reproducibility.json").write_text(json.dumps(snapshot, indent=2))


# --- phases ---

def phase_analyze(project: Path) -> dict:
    print("\n[analyze] start")
    for script in ["analyze_failures.py", "summarize_results.py", "propose_next_steps.py"]:
        script_path = project / "scripts" / script
        if script_path.exists():
            run([sys.executable, str(script_path), "--auto"], cwd=project)
        else:
            print(f"  skip: scripts/{script} not found")

    return {
        "latest_report": read_file(project / "results" / "reports" / "latest.md"),
        "error_analysis": read_file(project / "results" / "reports" / "error_analysis.md"),
        "next_actions": read_file(project / "results" / "reports" / "next_actions.md"),
    }


def phase_experiment(project: Path) -> dict:
    print("\n[experiment] start")

    test_result = run([sys.executable, "-m", "pytest", "-q", "tests/"], cwd=project)
    if test_result.returncode != 0:
        print("[experiment] tests failed — skip")
        return {"status": "skipped", "reason": "tests_failed"}

    config_script = project / "scripts" / "validate_config.py"
    if config_script.exists():
        cfg_result = run([sys.executable, str(config_script)], cwd=project)
        if cfg_result.returncode != 0:
            print("[experiment] config validation failed — skip")
            return {"status": "skipped", "reason": "config_invalid"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project / "results" / "runs" / timestamp

    exp_script = project / "scripts" / "run_experiment.py"
    if not exp_script.exists():
        print("[experiment] scripts/run_experiment.py not found — skip")
        return {"status": "skipped", "reason": "no_script"}

    result = run(
        [sys.executable, str(exp_script),
         "--config", "configs/base.yaml",
         "--output", str(output_dir)],
        cwd=project
    )

    metrics_file = output_dir / "metrics.json"
    metrics = json.loads(metrics_file.read_text()) if metrics_file.exists() else {}

    status = "completed" if result.returncode == 0 else "failed"
    print(f"[experiment] status: {status}")
    if metrics.get("primary_metric"):
        print(f"[experiment] primary metric: {metrics['primary_metric']}")

    # reproducibility snapshot
    if output_dir.exists():
        save_reproducibility_snapshot(project, output_dir)

    return {"status": status, "run_dir": str(output_dir), "metrics": metrics}


def phase_literature(project: Path, max_turns: int) -> None:
    print("\n[literature] start")
    if not _claude_available():
        print("[literature] claude CLI not found — skip")
        return

    error_analysis = read_file(project / "results" / "reports" / "error_analysis.md")
    prompt = (
        "Run the literature-scout skill. "
        f"Current failure analysis:\n{error_analysis[:500]}\n\n"
        "Find 3+ relevant papers and update docs/baselines.md."
    )
    _run_claude(prompt, cwd=project, max_turns=max_turns)


def phase_policy(project: Path, max_turns: int) -> None:
    print("\n[policy] start")
    proposed = project / "results" / "reports" / "proposed_policy_changes.md"
    if not proposed.exists() or not proposed.read_text().strip():
        print("[policy] no proposals — skip")
        return

    if not _claude_available():
        print("[policy] claude CLI not found — skip")
        return

    prompt = (
        "Run the policy-evolver skill. "
        "Review proposals in proposed_policy_changes.md with policy_guard "
        "and apply only approved changes to docs/eval_policy.md."
    )
    _run_claude(prompt, cwd=project, max_turns=max_turns)


def phase_claude_agent(project: Path, context: dict) -> None:
    print("\n[agent] deep analysis start")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[agent] ANTHROPIC_API_KEY not set — skip")
        return

    try:
        import anthropic
    except ImportError:
        print("[agent] anthropic package not installed: pip install anthropic")
        return

    client = anthropic.Anthropic(api_key=api_key)

    claude_md = read_file(project / "CLAUDE.md")
    prompt = f"""You are an ML research agent.

## Project constitution
{claude_md[:1000]}

## Current performance summary
{context.get('latest_report', '')[:1500]}

## Error analysis
{context.get('error_analysis', '')[:800]}

## Next action candidates
{context.get('next_actions', '')[:500]}

---
Based on the above:
1. Interpret the current performance trend (2-3 sentences)
2. Top 3 next experiment directions with rationale
3. Literature search keywords if needed (3 terms)
4. One evaluation policy extension candidate if needed (include self-review of approval criteria)

Lead with conclusions. Keep each item to 3 lines or fewer.
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    output = response.content[0].text
    print(output)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = project / "results" / "reports" / f"agent_analysis_{ts}.md"
    out_path.write_text(
        f"# Agent Analysis\ngenerated: {datetime.now().isoformat()}\n\n{output}\n"
    )
    print(f"\n[agent] saved: {out_path.name}")


# --- helpers ---

def _claude_available() -> bool:
    return subprocess.run(["which", "claude"], capture_output=True).returncode == 0


def _run_claude(prompt: str, cwd: Path, max_turns: int = 10) -> None:
    result = subprocess.run(
        ["claude", "--print", f"--max-turns={max_turns}", prompt],
        cwd=str(cwd), capture_output=False, text=True
    )
    if result.returncode != 0:
        print(f"[claude] failed (returncode={result.returncode})")


# --- main ---

def main():
    parser = argparse.ArgumentParser(description="research-os autonomous loop")
    parser.add_argument("--project", default=".", help="project path")
    parser.add_argument(
        "--mode",
        choices=["analyze-only", "nightly", "full-loop"],
        default="nightly"
    )
    parser.add_argument("--max-experiments", type=int, default=1,
                        help="max experiment runs (cost control)")
    parser.add_argument("--max-turns", type=int, default=10,
                        help="max turns per Claude session (cost control)")
    parser.add_argument("--timeout-minutes", type=int, default=90,
                        help="total loop timeout in minutes")
    parser.add_argument("--no-improve-k", type=int, default=3,
                        help="stop if primary metric does not improve over last K runs (0 = disable)")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not (project / "CLAUDE.md").exists():
        print(f"[error] {project}/CLAUDE.md not found — not a research-os project")
        sys.exit(1)

    import signal

    def _timeout_handler(signum, frame):
        print(f"\n[orchestrator] timeout ({args.timeout_minutes}m) — exit")
        sys.exit(1)

    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(args.timeout_minutes * 60)

    print(f"[orchestrator] start  mode={args.mode}  project={project.name}")
    print(f"[orchestrator] time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[orchestrator] limits: max_experiments={args.max_experiments}, "
          f"max_turns={args.max_turns}, timeout={args.timeout_minutes}m, "
          f"no_improve_k={args.no_improve_k}")

    # 1. analyze
    context = phase_analyze(project)

    if args.mode == "analyze-only":
        print("\n[orchestrator] done (analyze-only)")
        return

    # 2. experiment loop
    for i in range(args.max_experiments):
        print(f"\n[orchestrator] experiment {i+1}/{args.max_experiments}")

        # improvement-based stop
        if args.no_improve_k > 0 and no_improvement(project, args.no_improve_k):
            print(f"[orchestrator] no improvement over last {args.no_improve_k} runs — stop")
            break

        result = phase_experiment(project)
        if result.get("status") == "failed":
            print("[orchestrator] experiment failed — stop loop")
            break

    # 3. re-analyze
    context = phase_analyze(project)

    if args.mode == "full-loop":
        phase_literature(project, max_turns=args.max_turns)
        phase_policy(project, max_turns=args.max_turns)
        phase_claude_agent(project, context)

    print(f"\n[orchestrator] done: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
