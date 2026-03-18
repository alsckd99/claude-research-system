#!/usr/bin/env python3
"""Workspace organizer — auto-organize scattered files and archive obsolete scripts."""

import argparse
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def get_project_root() -> Path:
    """Find git root or use cwd."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())
    except Exception:
        return Path.cwd()


def find_latest_run(root: Path) -> str | None:
    """Find the latest timestamp run directory."""
    runs_dir = root / "results" / "runs"
    if not runs_dir.exists():
        return None
    dirs = sorted(
        [d.name for d in runs_dir.iterdir() if d.is_dir() and re.match(r"\d{8}_\d{6}", d.name)],
        reverse=True,
    )
    return dirs[0] if dirs else None


def organize_files(root: Path) -> list[str]:
    """Move scattered files into proper directories."""
    today = datetime.now().strftime("%Y%m%d")
    latest_run = find_latest_run(root)
    moved: list[str] = []

    rules: list[tuple[str, str, Path]] = [
        # (glob pattern relative to root, file check, target dir)
    ]

    # Rule 1: log files → logs/YYYYMMDD/
    log_dir = root / "logs" / today
    for f in list(root.glob("*.log")) + list((root / "logs").glob("*.log")) if (root / "logs").exists() else list(root.glob("*.log")):
        if f.parent == root or f.parent == root / "logs":
            log_dir.mkdir(parents=True, exist_ok=True)
            dest = log_dir / f.name
            if not dest.exists():
                shutil.move(str(f), str(dest))
                moved.append(f"  {f.name} → logs/{today}/")

    # Rule 2: images/pdf at root → results/reports/plots/
    plots_dir = root / "results" / "reports" / "plots"
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.pdf"):
        for f in root.glob(ext):
            if f.parent == root:
                plots_dir.mkdir(parents=True, exist_ok=True)
                dest = plots_dir / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    moved.append(f"  {f.name} → results/reports/plots/")

    # Rule 3: *_results*.json at root → results/
    results_dir = root / "results"
    for f in root.glob("*_results*.json"):
        if f.parent == root:
            results_dir.mkdir(parents=True, exist_ok=True)
            dest = results_dir / f.name
            if not dest.exists():
                shutil.move(str(f), str(dest))
                moved.append(f"  {f.name} → results/")

    # Rule 4: debug files at root → latest run debug/
    if latest_run:
        debug_dir = root / "results" / "runs" / latest_run / "debug"
        for f in root.glob("debug_*"):
            if f.parent == root and f.is_file():
                debug_dir.mkdir(parents=True, exist_ok=True)
                dest = debug_dir / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    moved.append(f"  {f.name} → results/runs/{latest_run}/debug/")

    # Rule 5: analysis files at root → latest run analysis/
    if latest_run:
        analysis_dir = root / "results" / "runs" / latest_run / "analysis"
        for f in root.glob("*_analysis*"):
            if f.parent == root and f.is_file():
                analysis_dir.mkdir(parents=True, exist_ok=True)
                dest = analysis_dir / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    moved.append(f"  {f.name} → results/runs/{latest_run}/analysis/")

    # Rule 6: tmp/temp files → _archive/YYYYMMDD/
    archive_dir = root / "_archive" / today
    for pattern in ("tmp_*", "temp_*"):
        for f in root.glob(pattern):
            if f.parent == root and f.is_file():
                archive_dir.mkdir(parents=True, exist_ok=True)
                dest = archive_dir / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    moved.append(f"  {f.name} → _archive/{today}/")

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
    """Check if a script is referenced by other files."""
    name = script.stem  # without .py
    fname = script.name  # with .py

    # Check hooks.json
    hooks_file = root / "hooks" / "hooks.json"
    if not hooks_file.exists():
        hooks_file = root / ".claude" / "hooks" / "hooks.json"
    if hooks_file.exists():
        content = hooks_file.read_text()
        if fname in content or name in content:
            return True

    # Check other py/sh/yaml/md files for references
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
    """Find and archive obsolete scripts."""
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

        # Check if it's a temp script
        is_temp = any(script.name.startswith(p) for p in TEMP_PREFIXES)

        # Check if referenced anywhere
        referenced = is_referenced(script, root)

        if not referenced or is_temp:
            # Verify it's committed to git
            result = subprocess.run(
                ["git", "log", "--oneline", "-1", "--", str(script)],
                capture_output=True, text=True,
            )
            if not result.stdout.strip():
                # Not in git — commit first
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
    """Stage changes and commit."""
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(
        ["git", "diff", "--staged", "--quiet"],
        cwd=root, capture_output=True,
    )
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
