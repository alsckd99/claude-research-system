"""
Decision report generator.
Collects model selection rationale, improvement reasoning, and experiment outcomes
into a unified decision log with visualized decision flow.

Usage:
    python scripts/generate_decision_report.py --auto
    python scripts/generate_decision_report.py --auto
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def read_file(path: Path) -> str:
    return path.read_text().strip() if path.exists() else ""


def _find_latest_timestamp(results_dir: Path) -> str | None:
    import re
    if not results_dir.exists():
        return None
    dirs = sorted(
        [d.name for d in results_dir.iterdir()
         if d.is_dir() and re.match(r"\d{8}_\d{6}", d.name)],
        reverse=True,
    )
    return dirs[0] if dirs else None


def load_runs(results_dir: Path) -> list[dict[str, Any]]:
    """Load all run metrics sorted by timestamp."""
    import re
    runs = []

    if not results_dir.exists():
        return runs

    for run_dir in sorted(results_dir.iterdir()):
        if not run_dir.is_dir() or not re.match(r"\d{8}_\d{6}", run_dir.name):
            continue
        metrics_file = run_dir / "metrics.json"
        if not metrics_file.exists():
            continue
        try:
            m = json.loads(metrics_file.read_text())
            m["_run_id"] = run_dir.name
            m["_run_dir"] = str(run_dir)

            # load config snapshot for method info
            config_file = run_dir / "config_snapshot.yaml"
            if config_file.exists():
                try:
                    import yaml
                    m["_config"] = yaml.safe_load(config_file.read_text()) or {}
                except (ImportError, Exception):
                    m["_config"] = {}

            # load debug summary if exists
            debug_summary = run_dir / "debug" / "debug_summary.json"
            if debug_summary.exists():
                m["_debug"] = json.loads(debug_summary.read_text())

            runs.append(m)
        except (json.JSONDecodeError, OSError):
            continue
    return runs


def parse_model_selection_log(docs_dir: Path) -> list[dict[str, str]]:
    """Parse docs/model_selection_log.md into structured entries."""
    content = read_file(docs_dir / "model_selection_log.md")
    if not content:
        return []

    entries = []
    current: dict[str, str] = {}
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("## ") and " — " in line:
            if current:
                entries.append(current)
            parts = line[3:].split(" — ", 1)
            current = {"model": parts[0].strip(), "date": parts[1].strip() if len(parts) > 1 else ""}
        elif line.startswith("- ") and ": " in line and current:
            key, val = line[2:].split(": ", 1)
            current[key.strip()] = val.strip()

    if current:
        entries.append(current)
    return entries


def parse_synthesis_proposals(docs_dir: Path) -> list[dict[str, str]]:
    """Parse docs/synthesis_proposals.md into structured entries."""
    content = read_file(docs_dir / "synthesis_proposals.md")
    if not content:
        return []

    proposals = []
    current: dict[str, str] = {}
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("## Proposal"):
            if current:
                proposals.append(current)
            current = {"title": line[3:].strip()}
        elif ": " in line and current and not line.startswith("#"):
            key, val = line.split(": ", 1)
            current[key.strip()] = val.strip()

    if current:
        proposals.append(current)
    return proposals


def parse_handoffs(docs_dir: Path) -> list[dict[str, str]]:
    """Collect handoff documents for decision tracing."""
    handoffs = []
    for pattern in ["handoff_*.md"]:
        for f in sorted(docs_dir.glob(pattern)):
            content = f.read_text().strip()
            handoffs.append({"file": f.name, "content": content[:500]})
    return handoffs


def generate_decision_flow(models: list, proposals: list, runs: list) -> str:
    """Generate ASCII decision flow diagram."""
    lines = ["```"]
    lines.append("┌─────────────────────────────────────────┐")
    lines.append("│           DECISION FLOW                  │")
    lines.append("└──────────────────┬──────────────────────┘")

    if models:
        lines.append("                   │")
        lines.append("    ┌──────────────▼──────────────┐")
        lines.append(f"    │  Model Selection ({len(models)} models) │")
        lines.append("    └──────────────┬──────────────┘")
        for m in models:
            reason = m.get("선정 이유", m.get("reason", "N/A"))[:50]
            lines.append(f"       ├─ {m.get('model', '?')}: {reason}")

    if proposals:
        lines.append("                   │")
        lines.append("    ┌──────────────▼──────────────┐")
        lines.append(f"    │  Proposals ({len(proposals)} ideas)       │")
        lines.append("    └──────────────┬──────────────┘")
        for p in proposals:
            lines.append(f"       ├─ {p.get('title', '?')[:50]}")

    if runs:
        lines.append("                   │")
        lines.append("    ┌──────────────▼──────────────┐")
        lines.append(f"    │  Experiments ({len(runs)} runs)       │")
        lines.append("    └──────────────┬──────────────┘")

        completed = [r for r in runs if r.get("status") == "completed"]
        failed = [r for r in runs if r.get("status") == "failed"]
        lines.append(f"       ├─ Completed: {len(completed)}")
        lines.append(f"       └─ Failed: {len(failed)}")

        if completed:
            values = [
                r.get("primary_metric", {}).get("value", 0)
                for r in completed if r.get("primary_metric", {}).get("value") is not None
            ]
            if values:
                lines.append("                   │")
                lines.append("    ┌──────────────▼──────────────┐")
                lines.append(f"    │  Best: {max(values):.4f}                │")
                lines.append(f"    │  Latest: {values[-1]:.4f}              │")
                lines.append("    └───────────────────────────────┘")

    lines.append("```")
    return "\n".join(lines)


def generate_report(
    project_dir: Path,
    runs: list,
    models: list,
    proposals: list,
    handoffs: list,
) -> str:
    """Generate the full decision report markdown."""
    sections = []

    # header
    sections.append(f"# Decision Report")
    sections.append(f"generated: {datetime.now().isoformat()}")
    sections.append(f"project: {project_dir.name}")
    sections.append("")

    # decision flow diagram
    sections.append("## Decision Flow")
    sections.append(generate_decision_flow(models, proposals, runs))
    sections.append("")

    # model selection rationale
    sections.append("## Model Selection Rationale")
    if models:
        sections.append(f"Total models selected: {len(models)}\n")
        for i, m in enumerate(models, 1):
            sections.append(f"### {i}. {m.get('model', 'Unknown')}")
            sections.append(f"- **Date**: {m.get('date', 'N/A')}")
            sections.append(f"- **Paper**: {m.get('paper', 'N/A')}")
            sections.append(f"- **Repo**: {m.get('repo', 'N/A')}")
            sections.append(f"- **Reported performance**: {m.get('reported performance', 'N/A')}")
            reason = m.get("선정 이유", m.get("reason", "N/A"))
            sections.append(f"- **Why this model**: {reason}")
            alternatives = m.get("대안으로 고려한 모델", m.get("alternatives", "N/A"))
            sections.append(f"- **Alternatives considered**: {alternatives}")
            sections.append("")
    else:
        sections.append("*No model selection log found (docs/model_selection_log.md)*\n")

    # improvement rationale
    sections.append("## Improvement Rationale")
    if proposals:
        for p in proposals:
            sections.append(f"### {p.get('title', 'Unknown')}")
            for k, v in p.items():
                if k != "title":
                    sections.append(f"- **{k}**: {v}")
            sections.append("")
    else:
        sections.append("*No synthesis proposals found (docs/synthesis_proposals.md)*\n")

    # experiment outcomes with decisions
    sections.append("## Experiment Outcomes")
    if runs:
        # table header
        sections.append("| Run | Status | Primary Metric | Debug Errors | Debug Warnings |")
        sections.append("|-----|--------|---------------|-------------|----------------|")
        for r in runs:
            run_id = r["_run_id"][:12]
            status = r.get("status", "?")
            pm = r.get("primary_metric", {})
            val = f"{pm.get('value', 0):.4f}" if pm.get("value") is not None else "N/A"
            debug = r.get("_debug", {})
            errors = debug.get("errors", "–")
            warnings = debug.get("warnings", "–")
            sections.append(f"| {run_id} | {status} | {val} | {errors} | {warnings} |")
        sections.append("")

        # improvement chain
        completed = [r for r in runs if r.get("status") == "completed"
                      and r.get("primary_metric", {}).get("value") is not None]
        if len(completed) >= 2:
            sections.append("### Improvement Chain")
            prev_val = None
            for r in completed:
                val = r["primary_metric"]["value"]
                delta = f" (Δ{val - prev_val:+.4f})" if prev_val is not None else " (baseline)"
                method = r.get("_config", {}).get("method", r["_run_id"][:8])
                sections.append(f"1. **{method}**: {val:.4f}{delta}")
                prev_val = val
            sections.append("")
    else:
        sections.append("*No experiment runs found*\n")

    # handoff trail
    if handoffs:
        sections.append("## Agent Handoff Trail")
        for h in handoffs:
            sections.append(f"### {h['file']}")
            sections.append(h["content"][:300] + ("..." if len(h["content"]) > 300 else ""))
            sections.append("")

    # key takeaways placeholder
    sections.append("## Key Takeaways")
    sections.append("")

    if runs:
        completed = [r for r in runs if r.get("status") == "completed"
                      and r.get("primary_metric", {}).get("value") is not None]
        if completed:
            values = [r["primary_metric"]["value"] for r in completed]
            best_val = max(values)
            best_run = completed[values.index(best_val)]
            sections.append(f"- **Best result**: {best_val:.4f} (run {best_run['_run_id'][:12]})")
            if len(values) >= 2:
                improvement = best_val - values[0]
                sections.append(f"- **Total improvement**: {improvement:+.4f} over {len(values)} runs")

        failed = [r for r in runs if r.get("status") == "failed"]
        if failed:
            sections.append(f"- **Failed runs**: {len(failed)} — check debug reports for root causes")

        debug_flagged = sum(
            1 for r in runs
            if r.get("_debug", {}).get("value_checks_flagged", 0) > 0
        )
        if debug_flagged:
            sections.append(f"- **Runs with value flags**: {debug_flagged} — review value_checks.json")

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Decision report generator")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--output", default=None,
                        help="Output path (default: results/{latest}/report/decision_report.md)")
    args = parser.parse_args()

    project_dir = Path(".").resolve()
    results_dir = Path("results")
    docs_dir = Path("docs")

    runs = load_runs(results_dir)
    models = parse_model_selection_log(docs_dir)
    proposals = parse_synthesis_proposals(docs_dir)
    handoffs = parse_handoffs(docs_dir)

    report = generate_report(project_dir, runs, models, proposals, handoffs)

    if args.output:
        output_path = Path(args.output)
    else:
        latest_ts = _find_latest_timestamp(results_dir)
        if latest_ts:
            output_path = Path(f"results/{latest_ts}/report/decision_report.md")
        else:
            output_path = Path("results/decision_report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)

    print(f"[decision] report saved: {output_path}")
    print(f"[decision] models: {len(models)}, proposals: {len(proposals)}, "
          f"runs: {len(runs)}, handoffs: {len(handoffs)}")


if __name__ == "__main__":
    main()
