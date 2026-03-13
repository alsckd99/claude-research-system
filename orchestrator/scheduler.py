"""
research-os 스케줄러.
cron 없이 Python만으로 주기 실행. 터미널이 꺼져도 돌아간다.

사용법:
    # 기본: 백그라운드 데몬으로 실행 (터미널 종료해도 계속 실행)
    python orchestrator/scheduler.py --project /path/to/project --mode continuous

    # 매일 새벽 2시 nightly 루프
    python orchestrator/scheduler.py \
        --project /path/to/project \
        --schedule "0 2 * * *" \
        --mode nightly

    # 6시간마다 분석
    python orchestrator/scheduler.py \
        --project /path/to/project \
        --interval 6h \
        --mode analyze-only

    # 포그라운드 (터미널에서 직접 보기)
    python orchestrator/scheduler.py --project . --mode continuous --foreground

    # PID 확인 / 정지
    cat /path/to/project/results/.scheduler.pid
    kill $(cat /path/to/project/results/.scheduler.pid)
"""
import argparse
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


def daemonize(project: Path) -> None:
    """Double-fork to detach from terminal. Process survives terminal close."""
    # first fork
    pid = os.fork()
    if pid > 0:
        # parent exits
        print(f"[scheduler] daemon started (pid={pid})")
        sys.exit(0)

    # new session
    os.setsid()

    # second fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # redirect stdin/stdout/stderr to log file
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

    # write PID file
    pid_file = project / "results" / ".scheduler.pid"
    pid_file.write_text(str(os.getpid()))

    # cleanup on exit
    def _cleanup(signum, frame):
        if pid_file.exists():
            pid_file.unlink()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)


def check_running(project: Path) -> bool:
    """Check if scheduler is already running for this project."""
    pid_file = project / "results" / ".scheduler.pid"
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)  # check if process exists
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        # stale PID file
        pid_file.unlink(missing_ok=True)
        return False


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

    # --status: check if running
    if args.status:
        if check_running(project):
            pid = (project / "results" / ".scheduler.pid").read_text().strip()
            print(f"[scheduler] running (pid={pid})")
            log = project / "results" / "reports" / "scheduler.log"
            if log.exists():
                # show last 10 lines
                lines = log.read_text().splitlines()
                for line in lines[-10:]:
                    print(f"  {line}")
        else:
            print("[scheduler] not running")
        return

    # --stop: kill running scheduler
    if args.stop:
        pid_file = project / "results" / ".scheduler.pid"
        if not pid_file.exists():
            print("[scheduler] not running")
            return
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"[scheduler] stopped (pid={pid})")
            pid_file.unlink(missing_ok=True)
        except (ProcessLookupError, PermissionError):
            print("[scheduler] already stopped (stale pid)")
            pid_file.unlink(missing_ok=True)
        return

    # check if already running
    if check_running(project):
        pid = (project / "results" / ".scheduler.pid").read_text().strip()
        print(f"[scheduler] already running (pid={pid}) — use --stop first")
        sys.exit(1)

    interval_sec = parse_interval(args.interval) if args.interval != "0" else 0

    print(f"[scheduler] 시작: project={project.name}")
    print(f"[scheduler] mode={args.mode}, interval={args.interval}")

    # once mode
    if args.once:
        run_loop(project, args.mode, args.max_experiments)
        return

    # daemonize unless --foreground
    if not args.foreground:
        print(f"[scheduler] daemonizing... log: {project}/results/reports/scheduler.log")
        print(f"[scheduler] stop: python orchestrator/scheduler.py --project {project} --stop")
        daemonize(project)

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
            pid_file = project / "results" / ".scheduler.pid"
            pid_file.unlink(missing_ok=True)
            break
        except Exception as e:
            print(f"[scheduler] 예외: {e}")

        if interval_sec > 0:
            print(f"[scheduler] 다음 실행: {args.interval} 후")
            time.sleep(interval_sec)
        # continuous mode with interval=0 loops immediately


if __name__ == "__main__":
    main()
