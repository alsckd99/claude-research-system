"""
research-os 스케줄러.
cron 없이 Python만으로 주기 실행. 터미널이 꺼져도 돌아간다.
공유 서버에서 안전: 자기 프로세스만 관리, 다른 사용자 보호.

사용법:
    # 기본: 백그라운드 데몬으로 실행 (터미널 종료해도 계속 실행)
    python orchestrator/scheduler.py --project /path/to/project --mode continuous

    # 포그라운드 (터미널에서 직접 보기)
    python orchestrator/scheduler.py --project . --mode continuous --foreground

    # PID 확인 / 정지
    python orchestrator/scheduler.py --project . --status
    python orchestrator/scheduler.py --project . --stop
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def parse_interval(interval_str: str) -> int:
    """'2h', '30m', '1d' → 초 단위 변환."""
    unit = interval_str[-1].lower()
    value = int(interval_str[:-1])
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if unit not in units:
        raise ValueError(f"지원하지 않는 단위: {unit} (s/m/h/d 사용)")
    return value * units[unit]


def run_loop(project: Path, mode: str, max_experiments: int) -> int:
    """orchestrator/main.py 실행."""
    orchestrator = Path(__file__).parent / "main.py"
    result = subprocess.run(
        [sys.executable, str(orchestrator),
         "--project", str(project),
         "--mode", mode,
         "--max-experiments", str(max_experiments),
         "--skip-completed",
         "--timeout-minutes", "0"],
        capture_output=False
    )
    return result.returncode


# --- PID file with owner verification ---

def _pid_file_path(project: Path) -> Path:
    return project / "results" / ".scheduler.pid"


def _write_pid_file(project: Path) -> None:
    """Write PID file with current user's UID for ownership verification."""
    pid_data = {
        "pid": os.getpid(),
        "uid": os.getuid(),
        "user": os.environ.get("USER", str(os.getuid())),
        "started_at": datetime.now().isoformat(),
        "project": str(project),
    }
    pid_file = _pid_file_path(project)
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(json.dumps(pid_data, indent=2))


def _read_pid_file(project: Path) -> dict | None:
    """Read PID file. Returns None if not found or invalid."""
    pid_file = _pid_file_path(project)
    if not pid_file.exists():
        return None
    try:
        data = json.loads(pid_file.read_text())
        return data if "pid" in data else None
    except (json.JSONDecodeError, OSError):
        return None


def _is_my_process(pid_data: dict) -> bool:
    """Check if the PID file belongs to the current user."""
    return pid_data.get("uid") == os.getuid()


def _process_alive(pid: int) -> bool:
    """Check if a process is running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def check_running(project: Path) -> dict | None:
    """Check if scheduler is running. Returns pid_data or None."""
    pid_data = _read_pid_file(project)
    if pid_data is None:
        return None

    pid = pid_data.get("pid", 0)
    if not _process_alive(pid):
        # stale PID file — only clean up if it's ours
        if _is_my_process(pid_data):
            _pid_file_path(project).unlink(missing_ok=True)
        return None

    return pid_data


def daemonize(project: Path) -> None:
    """Double-fork to detach from terminal. Process survives terminal close."""
    pid = os.fork()
    if pid > 0:
        print(f"[scheduler] daemon started (pid={pid})")
        sys.exit(0)

    os.setsid()

    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    log_dir = project / "results" / "reports"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "scheduler.log"

    sys.stdout.flush()
    sys.stderr.flush()

    devnull = open(os.devnull, "r")
    log_fd = open(log_file, "a")

    os.dup2(devnull.fileno(), sys.stdin.fileno())
    os.dup2(log_fd.fileno(), sys.stdout.fileno())
    os.dup2(log_fd.fileno(), sys.stderr.fileno())

    _write_pid_file(project)

    def _cleanup(signum, frame):
        _pid_file_path(project).unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".", help="프로젝트 경로")
    parser.add_argument("--mode", choices=["analyze-only", "nightly", "full-loop", "continuous"],
                        default="continuous")
    parser.add_argument("--interval", default="0",
                        help="실행 주기 (예: 6h, 30m). continuous 모드에서는 0=즉시 반복")
    parser.add_argument("--max-experiments", type=int, default=1)
    parser.add_argument("--once", action="store_true", help="한 번만 실행")
    parser.add_argument("--foreground", action="store_true",
                        help="포그라운드 실행 (터미널에서 직접 보기)")
    parser.add_argument("--stop", action="store_true", help="실행 중인 스케줄러 정지")
    parser.add_argument("--status", action="store_true", help="스케줄러 상태 확인")
    args = parser.parse_args()

    project = Path(args.project).resolve()

    # --status
    if args.status:
        pid_data = check_running(project)
        if pid_data:
            owner = pid_data.get("user", "unknown")
            pid = pid_data.get("pid")
            started = pid_data.get("started_at", "?")
            is_mine = _is_my_process(pid_data)
            label = "내 프로세스" if is_mine else f"다른 사용자 ({owner})"
            print(f"[scheduler] running — pid={pid}, user={owner} ({label}), started={started}")
            log = project / "results" / "reports" / "scheduler.log"
            if log.exists() and is_mine:
                lines = log.read_text().splitlines()
                for line in lines[-10:]:
                    print(f"  {line}")
        else:
            print("[scheduler] not running")
        return

    # --stop
    if args.stop:
        pid_data = check_running(project)
        if pid_data is None:
            print("[scheduler] not running")
            return

        if not _is_my_process(pid_data):
            owner = pid_data.get("user", "unknown")
            print(f"[scheduler] ERROR: 이 스케줄러는 '{owner}'의 프로세스입니다. "
                  f"본인의 프로세스만 정지할 수 있습니다.")
            sys.exit(1)

        pid = pid_data["pid"]
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[scheduler] stopped (pid={pid})")
            _pid_file_path(project).unlink(missing_ok=True)
        except ProcessLookupError:
            print("[scheduler] already stopped (stale pid)")
            _pid_file_path(project).unlink(missing_ok=True)
        except PermissionError:
            print("[scheduler] ERROR: 권한 없음 — 본인의 프로세스가 아닙니다")
            sys.exit(1)
        return

    # check if already running
    pid_data = check_running(project)
    if pid_data:
        owner = pid_data.get("user", "unknown")
        pid = pid_data.get("pid")
        if _is_my_process(pid_data):
            print(f"[scheduler] 이미 실행 중 (pid={pid}) — --stop 후 재시작하세요")
        else:
            print(f"[scheduler] '{owner}'가 이미 이 프로젝트에서 스케줄러를 실행 중입니다 (pid={pid})")
            print(f"[scheduler] 같은 프로젝트에서 중복 실행은 허용되지 않습니다.")
        sys.exit(1)

    interval_sec = parse_interval(args.interval) if args.interval != "0" else 0

    print(f"[scheduler] 시작: project={project.name}, user={os.environ.get('USER', '?')}")
    print(f"[scheduler] mode={args.mode}, interval={args.interval}")

    if args.once:
        run_loop(project, args.mode, args.max_experiments)
        return

    if not args.foreground:
        print(f"[scheduler] daemonizing... log: {project}/results/reports/scheduler.log")
        print(f"[scheduler] stop: python orchestrator/scheduler.py --project {project} --stop")
        daemonize(project)
    else:
        _write_pid_file(project)

    # main loop
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[scheduler] {now} — 루프 시작")

        try:
            returncode = run_loop(project, args.mode, args.max_experiments)
            if returncode != 0:
                print(f"[scheduler] 루프 실패 (code={returncode}) — 다음 주기에 재시도")
        except KeyboardInterrupt:
            print("\n[scheduler] 종료 (KeyboardInterrupt)")
            _pid_file_path(project).unlink(missing_ok=True)
            break
        except Exception as e:
            print(f"[scheduler] 예외: {e}")

        if interval_sec > 0:
            print(f"[scheduler] 다음 실행: {args.interval} 후")
            time.sleep(interval_sec)


if __name__ == "__main__":
    main()
