"""
research-os autonomous loop orchestrator.

Usage:
    python orchestrator/main.py --project /path/to/project --mode nightly
    python orchestrator/main.py --project /path/to/project --mode full-loop
    python orchestrator/main.py --project /path/to/project --mode analyze-only
    python orchestrator/main.py --project /path/to/project --mode continuous

Modes:
    analyze-only  : analyze + update reports only (no experiments)
    nightly       : analyze -> 1 experiment -> re-analyze
    full-loop     : analyze -> N experiments -> literature -> policy -> agent analysis
    continuous    : non-stop loop — analyze -> experiment -> improve -> repeat

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


def get_completed_methods(project: Path) -> set[str]:
    """Return set of method names that already have completed runs."""
    methods = set()
    runs_dir = project / "results" / "runs"
    if not runs_dir.exists():
        return methods
    for run_dir in sorted(runs_dir.iterdir()):
        metrics_file = run_dir / "metrics.json"
        config_file = run_dir / "config_snapshot.yaml"
        if not metrics_file.exists():
            continue
        try:
            metrics = json.loads(metrics_file.read_text())
            if metrics.get("status") != "completed":
                continue
            # extract method name from config
            if config_file.exists():
                try:
                    import yaml
                    config = yaml.safe_load(config_file.read_text()) or {}
                    method = config.get("method", config.get("model", ""))
                    if method:
                        methods.add(str(method))
                except Exception:
                    pass
        except (json.JSONDecodeError, OSError):
            continue
    return methods


# --- improvement-based stop condition (Reflexion p.7) ---

def no_improvement(project: Path, k: int) -> bool:
    """Return True if primary_metric has not improved over the last k completed runs."""
    runs = [r for r in load_registry(project) if r.get("status") == "completed"]
    if len(runs) < k:
        return False
    recent = runs[-k:]
    values = [
        r.get("primary_metric_value")
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


def phase_experiment(project: Path, skip_methods: set[str] | None = None) -> dict:
    """Run experiment. Skip methods already completed if skip_methods is provided."""
    print("\n[experiment] start")

    # check if current config method was already run
    if skip_methods:
        try:
            import yaml
            config_path = project / "configs" / "base.yaml"
            if config_path.exists():
                config = yaml.safe_load(config_path.read_text()) or {}
                method = config.get("method", config.get("model", ""))
                if method and method in skip_methods:
                    print(f"[experiment] method '{method}' already completed — skip")
                    return {"status": "skipped", "reason": "already_completed", "method": method}
        except Exception:
            pass

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
        "Find 3+ relevant papers and update docs/baselines.md. "
        "Do NOT ask for confirmation — proceed autonomously."
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
        "and apply only approved changes to docs/eval_policy.md. "
        "Do NOT ask for confirmation — proceed autonomously."
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


def phase_visualize(project: Path) -> None:
    """Generate cross-run visualization plots and summary."""
    print("\n[visualize] start")
    viz_script = project / "scripts" / "visualize_results.py"
    if not viz_script.exists():
        print("  skip: scripts/visualize_results.py not found")
        return
    run([sys.executable, str(viz_script), "--auto"], cwd=project)


def phase_decision_report(project: Path) -> None:
    """Generate decision report documenting model choices and improvement rationale."""
    print("\n[decision] start")
    dec_script = project / "scripts" / "generate_decision_report.py"
    if not dec_script.exists():
        print("  skip: scripts/generate_decision_report.py not found")
        return
    run([sys.executable, str(dec_script), "--auto"], cwd=project)


# --- helpers ---

def _claude_available() -> bool:
    return subprocess.run(["which", "claude"], capture_output=True).returncode == 0


def _run_claude(prompt: str, cwd: Path, max_turns: int = 10) -> None:
    result = subprocess.run(
        ["claude", "--print", f"--max-turns={max_turns}",
         "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,Agent,WebFetch,WebSearch,"
         "mcp__arxiv__search_papers,mcp__arxiv__read_paper,mcp__arxiv__list_papers,"
         "mcp__fetch__fetch_readable,mcp__fetch__fetch_json,"
         "mcp__brave-search__brave_web_search",
         "--yes",  # no interactive prompts
         prompt],
        cwd=str(cwd), capture_output=False, text=True
    )
    if result.returncode != 0:
        print(f"[claude] failed (returncode={result.returncode})")


def _save_loop_state(project: Path, iteration: int, action: str) -> None:
    """Save loop state for session resume."""
    reports_dir = project / "results" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "loop_iteration": iteration,
        "last_action": action,
        "saved_at": datetime.now().isoformat(),
    }

    registry = load_registry(project)
    completed = [r for r in registry if r.get("status") == "completed"]
    if completed:
        best = max(completed, key=lambda r: r.get("primary_metric_value", 0.0))
        state["best_metric"] = best.get("primary_metric_value", "unknown")

    (reports_dir / ".session_state.json").write_text(json.dumps(state, indent=2))


# --- main ---

def main():
    parser = argparse.ArgumentParser(description="research-os autonomous loop")
    parser.add_argument("--project", default=".", help="project path")
    parser.add_argument(
        "--mode",
        choices=["analyze-only", "nightly", "full-loop", "continuous"],
        default="nightly"
    )
    parser.add_argument("--max-experiments", type=int, default=1,
                        help="max experiment runs per iteration (cost control)")
    parser.add_argument("--max-turns", type=int, default=10,
                        help="max turns per Claude session (cost control)")
    parser.add_argument("--timeout-minutes", type=int, default=0,
                        help="total loop timeout in minutes (0 = no timeout)")
    parser.add_argument("--no-improve-k", type=int, default=3,
                        help="stop if primary metric does not improve over last K runs (0 = disable)")
    parser.add_argument("--skip-completed", action="store_true", default=True,
                        help="skip methods that already have completed runs (default: True)")
    parser.add_argument("--no-skip-completed", dest="skip_completed", action="store_false",
                        help="re-run all methods even if already completed")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not (project / "CLAUDE.md").exists():
        print(f"[error] {project}/CLAUDE.md not found — not a research-os project")
        sys.exit(1)

    # timeout setup (0 = no timeout for continuous mode)
    if args.timeout_minutes > 0:
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
          f"no_improve_k={args.no_improve_k}, skip_completed={args.skip_completed}")

    if args.mode == "continuous":
        _run_continuous(project, args)
        return

    # --- single-pass modes ---

    # 1. analyze
    context = phase_analyze(project)

    if args.mode == "analyze-only":
        print("\n[orchestrator] done (analyze-only)")
        return

    # 2. experiment loop
    skip_methods = get_completed_methods(project) if args.skip_completed else None

    for i in range(args.max_experiments):
        print(f"\n[orchestrator] experiment {i+1}/{args.max_experiments}")

        # improvement-based stop
        if args.no_improve_k > 0 and no_improvement(project, args.no_improve_k):
            print(f"[orchestrator] no improvement over last {args.no_improve_k} runs — stop")
            break

        result = phase_experiment(project, skip_methods=skip_methods)
        if result.get("status") == "failed":
            print("[orchestrator] experiment failed — stop loop")
            break

    # 3. re-analyze
    context = phase_analyze(project)

    # 4. visualize results
    phase_visualize(project)

    # 5. generate decision report
    phase_decision_report(project)

    if args.mode == "full-loop":
        phase_literature(project, max_turns=args.max_turns)
        phase_policy(project, max_turns=args.max_turns)
        phase_claude_agent(project, context)

    print(f"\n[orchestrator] done: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def _run_continuous(project: Path, args) -> None:
    """Non-stop improvement loop: analyze → experiment → literature → improve → repeat."""
    iteration = 0
    consecutive_failures = 0
    max_consecutive_failures = 5

    while True:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"[orchestrator] === ITERATION {iteration} ===")
        print(f"[orchestrator] time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        _save_loop_state(project, iteration, "starting")

        # improvement-based stop
        if args.no_improve_k > 0 and no_improvement(project, args.no_improve_k):
            print(f"[orchestrator] no improvement over last {args.no_improve_k} runs")
            print("[orchestrator] running literature search for new directions...")
            phase_literature(project, max_turns=args.max_turns)
            # reset after literature search — new methods may help
            # but if still stuck after another K runs, the next check will fire again

        # 1. analyze current state
        context = phase_analyze(project)

        # 2. run experiments (skip already-completed methods)
        skip_methods = get_completed_methods(project) if args.skip_completed else None
        exp_failed = False
        for i in range(args.max_experiments):
            result = phase_experiment(project, skip_methods=skip_methods)
            if result.get("status") == "failed":
                exp_failed = True
                consecutive_failures += 1
                print(f"[orchestrator] consecutive failures: {consecutive_failures}")
                break
            elif result.get("status") == "completed":
                consecutive_failures = 0

        if consecutive_failures >= max_consecutive_failures:
            print(f"[orchestrator] {max_consecutive_failures} consecutive failures — "
                  "searching literature for alternative approaches")
            phase_literature(project, max_turns=args.max_turns)
            consecutive_failures = 0

        # 3. re-analyze
        context = phase_analyze(project)

        # 4. visualize
        phase_visualize(project)

        # 5. decision report
        phase_decision_report(project)

        # 6. literature + policy (every 3rd iteration or when needed)
        if iteration % 3 == 0 or exp_failed:
            phase_literature(project, max_turns=args.max_turns)
            phase_policy(project, max_turns=args.max_turns)

        # 7. agent analysis (every 5th iteration)
        if iteration % 5 == 0:
            phase_claude_agent(project, context)

        _save_loop_state(project, iteration, "completed")
        print(f"\n[orchestrator] iteration {iteration} done: "
              f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
