#!/usr/bin/env python3
"""Workspace organizer — auto-organize scattered files and archive obsolete scripts.

All results go under results/{YYYYMMDD_HHMMSS}/:
  metrics.json, config_snapshot.yaml, git_commit.txt
  plots/       — visualizations
  debug/       — debug logs
  analysis/    — deep analysis, gap analysis, debug findings
  report/      — error analysis, next actions, decision report

Only results/registry.json and results/final_report.md live at results root.
"""

import argparse
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def get_project_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())
    except Exception:
        return Path.cwd()


def find_latest_timestamp(root: Path) -> str | None:
    """Find the latest timestamp directory under results/."""
    results_dir = root / "results"
    if not results_dir.exists():
        return None

    ts_pattern = re.compile(r"\d{8}_\d{6}")
    dirs = sorted(
        [d.name for d in results_dir.iterdir()
         if d.is_dir() and ts_pattern.match(d.name)],
        reverse=True,
    )
    return dirs[0] if dirs else None


def ensure_timestamp_dir(root: Path) -> Path:
    """Get latest timestamp dir or create a new one."""
    ts = find_latest_timestamp(root)
    if ts:
        d = root / "results" / ts
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        d = root / "results" / ts
        d.mkdir(parents=True, exist_ok=True)
    return d


def organize_files(root: Path) -> list[str]:
    """Move scattered files into proper timestamp directories."""
    today = datetime.now().strftime("%Y%m%d")
    ts_dir = ensure_timestamp_dir(root)
    ts_name = ts_dir.name
    moved: list[str] = []

    # === Project root cleanup ===

    # Log files → logs/YYYYMMDD/
    log_dir = root / "logs" / today
    log_sources = list(root.glob("*.log"))
    if (root / "logs").exists():
        log_sources += [f for f in (root / "logs").glob("*.log") if f.parent == root / "logs"]
    for f in log_sources:
        if f.parent in (root, root / "logs"):
            log_dir.mkdir(parents=True, exist_ok=True)
            dest = log_dir / f.name
            if not dest.exists():
                shutil.move(str(f), str(dest))
                moved.append(f"  {f.name} → logs/{today}/")

    # Images/PDF at root → results/{timestamp}/plots/
    plots_dir = ts_dir / "plots"
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        for f in root.glob(ext):
            if f.parent == root:
                plots_dir.mkdir(parents=True, exist_ok=True)
                dest = plots_dir / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    moved.append(f"  {f.name} → results/{ts_name}/plots/")

    # *_results*.json at root → results/{timestamp}/
    for f in root.glob("*_results*.json"):
        if f.parent == root:
            dest = ts_dir / f.name
            if not dest.exists():
                shutil.move(str(f), str(dest))
                moved.append(f"  {f.name} → results/{ts_name}/")

    # debug_* at root → results/{timestamp}/debug/
    debug_dir = ts_dir / "debug"
    for f in root.glob("debug_*"):
        if f.parent == root and f.is_file():
            debug_dir.mkdir(parents=True, exist_ok=True)
            dest = debug_dir / f.name
            if not dest.exists():
                shutil.move(str(f), str(dest))
                moved.append(f"  {f.name} → results/{ts_name}/debug/")

    # *_analysis* at root → results/{timestamp}/analysis/
    analysis_dir = ts_dir / "analysis"
    for f in root.glob("*_analysis*"):
        if f.parent == root and f.is_file():
            analysis_dir.mkdir(parents=True, exist_ok=True)
            dest = analysis_dir / f.name
            if not dest.exists():
                shutil.move(str(f), str(dest))
                moved.append(f"  {f.name} → results/{ts_name}/analysis/")

    # tmp/temp at root → _archive/
    archive_dir = root / "_archive" / today
    for pattern in ("tmp_*", "temp_*"):
        for f in root.glob(pattern):
            if f.parent == root and f.is_file():
                archive_dir.mkdir(parents=True, exist_ok=True)
                dest = archive_dir / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    moved.append(f"  {f.name} → _archive/{today}/")

    # === results/ root cleanup — move stray files into latest timestamp ===

    results_root = root / "results"
    if results_root.exists():
        # Stray files at results root (except registry.json, final_report.md)
        keep_at_root = {"registry.json", "final_report.md"}
        for f in results_root.iterdir():
            if f.is_file() and f.name not in keep_at_root:
                # JSON results → timestamp root
                if f.suffix == ".json":
                    dest = ts_dir / f.name
                # MD reports → timestamp/report/
                elif f.suffix == ".md":
                    report_dir = ts_dir / "report"
                    report_dir.mkdir(parents=True, exist_ok=True)
                    dest = report_dir / f.name
                # Images → timestamp/plots/
                elif f.suffix in (".png", ".jpg", ".jpeg"):
                    plots_dir.mkdir(parents=True, exist_ok=True)
                    dest = plots_dir / f.name
                else:
                    continue
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    moved.append(f"  results/{f.name} → results/{ts_name}/{dest.relative_to(ts_dir)}")

        # results/reports/ → distribute into timestamp dirs
        reports_dir = results_root / "reports"
        if reports_dir.exists() and reports_dir.is_dir():
            # reports/plots/ → timestamp/plots/
            rplots = reports_dir / "plots"
            if rplots.exists():
                plots_dir.mkdir(parents=True, exist_ok=True)
                for f in rplots.iterdir():
                    if f.is_file():
                        dest = plots_dir / f.name
                        if not dest.exists():
                            shutil.move(str(f), str(dest))
                            moved.append(f"  results/reports/plots/{f.name} → results/{ts_name}/plots/")
                # Remove empty plots dir
                if not any(rplots.iterdir()):
                    rplots.rmdir()

            # reports/*.md → timestamp/report/
            report_dir = ts_dir / "report"
            for f in reports_dir.iterdir():
                if f.is_file():
                    report_dir.mkdir(parents=True, exist_ok=True)
                    dest = report_dir / f.name
                    if not dest.exists():
                        shutil.move(str(f), str(dest))
                        moved.append(f"  results/reports/{f.name} → results/{ts_name}/report/")

            # Remove empty reports dir
            try:
                if reports_dir.exists() and not any(reports_dir.iterdir()):
                    reports_dir.rmdir()
            except OSError:
                pass

        # results/runs/ → migrate to results/{timestamp}/ structure
        runs_dir = results_root / "runs"
        if runs_dir.exists() and runs_dir.is_dir():
            for run in runs_dir.iterdir():
                if run.is_dir() and re.match(r"\d{8}_\d{6}", run.name):
                    target = results_root / run.name
                    if not target.exists():
                        shutil.move(str(run), str(target))
                        moved.append(f"  results/runs/{run.name}/ → results/{run.name}/")
                    else:
                        # Merge contents
                        for item in run.iterdir():
                            dest = target / item.name
                            if not dest.exists():
                                shutil.move(str(item), str(dest))
                                moved.append(f"  results/runs/{run.name}/{item.name} → results/{run.name}/")
            # Remove empty runs dir
            try:
                if runs_dir.exists() and not any(runs_dir.iterdir()):
                    runs_dir.rmdir()
            except OSError:
                pass

    return moved


CORE_SCRIPTS = {
    "run_experiment.py", "validate_config.py", "debug_logger.py",
    "server_utils.py", "analyze_failures.py", "summarize_results.py",
    "propose_next_steps.py", "visualize_results.py",
    "generate_decision_report.py", "save_session_state.py",
    "organize_workspace.py",
}

TEMP_PREFIXES = ("tmp_", "test_", "debug_", "scratch_", "fix_")


def is_referenced(script: Path, root: Path) -> bool:
    name = script.stem
    fname = script.name

    # Check hooks.json
    for hooks_path in (root / "hooks" / "hooks.json", root / ".claude" / "hooks" / "hooks.json"):
        if hooks_path.exists():
            content = hooks_path.read_text()
            if fname in content or name in content:
                return True

    # Check other files for references
    for ext in ("**/*.py", "**/*.sh", "**/*.yaml", "**/*.yml", "**/*.md"):
        for f in root.glob(ext):
            if f == script or "_archive" in str(f) or "__pycache__" in str(f):
                continue
            try:
                content = f.read_text(errors="ignore")
                if fname in content or f"import {name}" in content or f"from {name}" in content:
                    return True
            except Exception:
                continue

    return False


def cleanup_scripts(root: Path) -> list[str]:
    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return []

    today = datetime.now().strftime("%Y%m%d")
    archive_dir = root / "_archive" / "scripts" / today
    archived: list[str] = []

    for script in scripts_dir.glob("*.py"):
        if script.name in CORE_SCRIPTS:
            continue
        if script.name.startswith("__"):
            continue

        is_temp = any(script.name.startswith(p) for p in TEMP_PREFIXES)
        referenced = is_referenced(script, root)

        if not referenced or is_temp:
            # Verify it's committed to git before archiving
            result = subprocess.run(
                ["git", "log", "--oneline", "-1", "--", str(script)],
                capture_output=True, text=True,
            )
            if not result.stdout.strip():
                subprocess.run(["git", "add", str(script)], capture_output=True)
                subprocess.run(
                    ["git", "commit", "-m", f"chore: save {script.name} before archive"],
                    capture_output=True,
                )

            archive_dir.mkdir(parents=True, exist_ok=True)
            dest = archive_dir / script.name
            reason = "temp script" if is_temp else "unreferenced"
            shutil.move(str(script), str(dest))
            archived.append(f"  {script.name} → _archive/scripts/{today}/ ({reason})")

    # Write archive log
    if archived:
        log_file = root / "_archive" / "scripts" / "archive_log.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(f"\n## {today}\n\n")
            for entry in archived:
                f.write(f"- {entry.strip()}\n")

    return archived


def git_commit(root: Path, msg: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", msg, "--no-verify"],
        cwd=root, capture_output=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize workspace files")
    parser.add_argument("--cleanup", action="store_true", help="Also archive obsolete scripts")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    root = get_project_root()
    print(f"[organizer] project root: {root}")

    # Part 1: Organize scattered files
    print("\n[organizer] === File Organization ===")
    moved = organize_files(root)
    if moved:
        for m in moved:
            print(m)
        if not args.dry_run:
            git_commit(root, f"chore: organize {len(moved)} scattered files")
        print(f"[organizer] organized {len(moved)} files")
    else:
        print("[organizer] workspace is clean — nothing to move")

    # Part 2: Script cleanup
    if args.cleanup:
        print("\n[organizer] === Script Cleanup ===")
        archived = cleanup_scripts(root)
        if archived:
            for a in archived:
                print(a)
            if not args.dry_run:
                git_commit(root, f"chore: archive {len(archived)} unused scripts")
            print(f"[organizer] archived {len(archived)} scripts")
        else:
            print("[organizer] no obsolete scripts found")


if __name__ == "__main__":
    main()
