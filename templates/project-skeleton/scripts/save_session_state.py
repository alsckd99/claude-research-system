"""
Save session state to .session_state.json.
Called by hooks (PreCompact, Stop) to persist loop state across sessions.

Usage:
    python scripts/save_session_state.py --action "pre-compact save"
    python scripts/save_session_state.py --action "session stop"
"""
import argparse
import json
import os
from datetime import datetime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", default="checkpoint", help="action label for state")
    args = parser.parse_args()

    reports_dir = "results"
    if not os.path.isdir(reports_dir):
        return

    state: dict = {}
    registry_path = "results/registry.json"
    if os.path.exists(registry_path):
        with open(registry_path) as f:
            reg = json.load(f)
        runs = [r for r in reg.get("runs", []) if r.get("status") == "completed"]
        if runs:
            best = max(runs, key=lambda r: r.get("primary_metric_value", 0.0))
            state["best_metric"] = best.get("primary_metric_value", "unknown")
            state["loop_iteration"] = len(runs)
            if len(runs) >= 2:
                vals = [r.get("primary_metric_value", 0.0) for r in runs[-5:]]
                stall, peak = 0, vals[0]
                for v in vals[1:]:
                    if v <= peak:
                        stall += 1
                    else:
                        stall, peak = 0, v
                state["stall_count"] = stall

    for fname in ["next_actions.md", "error_analysis.md"]:
        fpath = os.path.join(reports_dir, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                state[fname] = f.read()[:500]

    failed = []
    ea_path = os.path.join(reports_dir, "error_analysis.md")
    if os.path.exists(ea_path):
        with open(ea_path) as f:
            for line in f:
                stripped = line.strip()
                if any(k in stripped.lower() for k in [
                    "failed", "blocked", "does not work",
                    "do not retry", "unsuccessful", "no improvement"
                ]) and len(stripped) > 10:
                    failed.append(stripped[:200])
    if failed:
        state["do_not_retry"] = failed[:10]

    state["last_action"] = args.action
    state["saved_at"] = datetime.now().isoformat()

    with open(os.path.join(reports_dir, ".session_state.json"), "w") as f:
        json.dump(state, f, indent=2)

    print(f"[session] state saved ({args.action})")


if __name__ == "__main__":
    main()
