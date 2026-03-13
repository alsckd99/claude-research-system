"""
Structured debug logger for experiment runs.
Captures intermediate values, timing, and diagnostics at each pipeline step.

Usage:
    from scripts.debug_logger import DebugLogger

    logger = DebugLogger(run_dir="results/runs/20260313_120000")
    logger.step("data_loading", status="ok", rows=1000, shape=(1000, 512))
    logger.step("model_init", status="ok", params=1_200_000)
    logger.step("inference", status="ok", output_shape=(1000, 2), time_sec=3.2)
    logger.value_check("scores", scores, expected_range=(0, 1))
    logger.finalize()
"""
import json
import sys
import time
import traceback
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any


class DebugLogger:
    """Structured debug logger that saves diagnostics per experiment run."""

    def __init__(self, run_dir: str | Path):
        self.run_dir = Path(run_dir)
        self.debug_dir = self.run_dir / "debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)

        self.steps: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.value_checks: list[dict[str, Any]] = []
        self._start_time = time.time()
        self._step_timers: dict[str, float] = {}

        # redirect stdout/stderr capture
        self._stdout_capture = StringIO()
        self._stderr_capture = StringIO()

        print(f"[debug] logger initialized: {self.debug_dir}")

    def step(self, name: str, status: str = "ok", **details: Any) -> None:
        """Log a pipeline step with status and optional details."""
        elapsed = time.time() - self._start_time
        entry = {
            "step": name,
            "status": status,
            "elapsed_sec": round(elapsed, 3),
            "timestamp": datetime.now().isoformat(),
            **{k: _serialize(v) for k, v in details.items()},
        }
        self.steps.append(entry)

        icon = "✓" if status == "ok" else "✗" if status == "error" else "⚠"
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items() if k != "traceback")
        print(f"[debug] {icon} {name}: {status}" + (f" — {detail_str}" if detail_str else ""))

        if status == "error":
            self.errors.append(entry)

    def step_start(self, name: str) -> None:
        """Mark the start of a timed step."""
        self._step_timers[name] = time.time()

    def step_end(self, name: str, status: str = "ok", **details: Any) -> None:
        """Mark the end of a timed step and log duration."""
        start = self._step_timers.pop(name, time.time())
        duration = time.time() - start
        self.step(name, status=status, duration_sec=round(duration, 3), **details)

    def value_check(
        self,
        name: str,
        values: Any,
        expected_range: tuple[float, float] | None = None,
        expect_no_nan: bool = True,
        expect_no_constant: bool = True,
    ) -> dict[str, Any]:
        """Check intermediate values for common issues."""
        result: dict[str, Any] = {"name": name, "timestamp": datetime.now().isoformat()}
        flags: list[str] = []

        try:
            import numpy as np
            arr = np.asarray(values, dtype=float).flatten()

            result["shape"] = list(np.asarray(values).shape)
            result["dtype"] = str(np.asarray(values).dtype)
            result["min"] = float(np.nanmin(arr))
            result["max"] = float(np.nanmax(arr))
            result["mean"] = float(np.nanmean(arr))
            result["std"] = float(np.nanstd(arr))
            result["n_elements"] = len(arr)

            # NaN check
            nan_count = int(np.isnan(arr).sum())
            result["nan_count"] = nan_count
            if expect_no_nan and nan_count > 0:
                flags.append(f"NaN detected: {nan_count}/{len(arr)} elements")

            # Inf check
            inf_count = int(np.isinf(arr).sum())
            result["inf_count"] = inf_count
            if inf_count > 0:
                flags.append(f"Inf detected: {inf_count}/{len(arr)} elements")

            # Range check
            if expected_range is not None:
                lo, hi = expected_range
                out_of_range = int(((arr < lo) | (arr > hi)).sum())
                result["out_of_range"] = out_of_range
                if out_of_range > 0:
                    flags.append(
                        f"Out of range [{lo}, {hi}]: {out_of_range}/{len(arr)} elements "
                        f"(actual: [{result['min']:.4f}, {result['max']:.4f}])"
                    )

            # Constant check
            if expect_no_constant and len(arr) > 1:
                if np.nanstd(arr) < 1e-8:
                    flags.append(f"Near-constant output (std={result['std']:.2e})")

        except ImportError:
            result["error"] = "numpy not available"
            flags.append("numpy not available — value check skipped")
        except Exception as e:
            result["error"] = str(e)
            flags.append(f"value check failed: {e}")

        result["flags"] = flags
        result["status"] = "flag" if flags else "pass"
        self.value_checks.append(result)

        if flags:
            for f in flags:
                print(f"[debug] ⚠ value_check({name}): {f}")
                self.warnings.append({"source": f"value_check({name})", "message": f})
        else:
            print(f"[debug] ✓ value_check({name}): pass")

        return result

    def log_exception(self, step_name: str, exc: Exception) -> None:
        """Log an exception with full traceback."""
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        self.step(step_name, status="error", error=str(exc), traceback="".join(tb))

    def log_config(self, config: dict[str, Any]) -> None:
        """Log the experiment config for debugging context."""
        (self.debug_dir / "config_debug.json").write_text(
            json.dumps(config, indent=2, default=str)
        )
        self.step("config_logged", status="ok", keys=list(config.keys()))

    def finalize(self) -> Path:
        """Write all debug info to files and return the debug directory path."""
        total_time = time.time() - self._start_time

        summary = {
            "run_id": self.run_dir.name,
            "total_time_sec": round(total_time, 3),
            "total_steps": len(self.steps),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "value_checks_run": len(self.value_checks),
            "value_checks_flagged": sum(1 for v in self.value_checks if v["status"] == "flag"),
            "generated_at": datetime.now().isoformat(),
        }

        # Write structured JSON logs
        (self.debug_dir / "debug_summary.json").write_text(
            json.dumps(summary, indent=2)
        )
        (self.debug_dir / "debug_steps.json").write_text(
            json.dumps(self.steps, indent=2, default=str)
        )
        (self.debug_dir / "value_checks.json").write_text(
            json.dumps(self.value_checks, indent=2, default=str)
        )

        # Write human-readable markdown report
        md_lines = [
            f"# Debug Report — {self.run_dir.name}",
            f"generated: {datetime.now().isoformat()}",
            f"total time: {total_time:.1f}s",
            f"",
            f"## Summary",
            f"- Steps: {len(self.steps)}",
            f"- Errors: {len(self.errors)}",
            f"- Warnings: {len(self.warnings)}",
            f"- Value checks: {len(self.value_checks)} "
            f"({summary['value_checks_flagged']} flagged)",
            f"",
        ]

        if self.errors:
            md_lines.append("## Errors")
            for e in self.errors:
                md_lines.append(f"### {e['step']}")
                md_lines.append(f"- time: {e['elapsed_sec']}s")
                if "error" in e:
                    md_lines.append(f"- error: `{e['error']}`")
                if "traceback" in e:
                    md_lines.append(f"```\n{e['traceback']}```")
                md_lines.append("")

        if self.warnings:
            md_lines.append("## Warnings")
            for w in self.warnings:
                md_lines.append(f"- **{w['source']}**: {w['message']}")
            md_lines.append("")

        if self.value_checks:
            md_lines.append("## Value Checks")
            for vc in self.value_checks:
                status_icon = "✓" if vc["status"] == "pass" else "⚠"
                md_lines.append(f"### {status_icon} {vc['name']}")
                for k in ["shape", "dtype", "min", "max", "mean", "std", "nan_count"]:
                    if k in vc:
                        md_lines.append(f"- {k}: `{vc[k]}`")
                if vc.get("flags"):
                    for f in vc["flags"]:
                        md_lines.append(f"- **FLAG**: {f}")
                md_lines.append("")

        md_lines.append("## Step Timeline")
        for s in self.steps:
            icon = "✓" if s["status"] == "ok" else "✗" if s["status"] == "error" else "⚠"
            md_lines.append(f"- `{s['elapsed_sec']:>7.3f}s` {icon} **{s['step']}** — {s['status']}")

        (self.debug_dir / "debug_report.md").write_text("\n".join(md_lines))

        print(f"\n[debug] === Debug Summary ===")
        print(f"[debug] Steps: {len(self.steps)} | Errors: {len(self.errors)} | "
              f"Warnings: {len(self.warnings)} | Value flags: {summary['value_checks_flagged']}")
        print(f"[debug] Total time: {total_time:.1f}s")
        print(f"[debug] Report: {self.debug_dir / 'debug_report.md'}")

        return self.debug_dir


def _serialize(v: Any) -> Any:
    """Make a value JSON-serializable."""
    if isinstance(v, (str, int, float, bool, type(None))):
        return v
    if isinstance(v, (list, tuple)):
        return [_serialize(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _serialize(val) for k, val in v.items()}
    try:
        import numpy as np
        if isinstance(v, np.ndarray):
            if v.size <= 10:
                return v.tolist()
            return f"ndarray(shape={v.shape}, dtype={v.dtype})"
        if isinstance(v, (np.integer, np.floating)):
            return v.item()
    except ImportError:
        pass
    return str(v)
