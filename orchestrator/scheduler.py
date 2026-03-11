"""
research-os 스케줄러.
cron 없이 Python만으로 주기 실행. 또는 GitHub Actions 트리거 대체용.

사용법:
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

    # 백그라운드 실행
    nohup python orchestrator/scheduler.py --project . --interval 6h &
"""
import argparse
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
         "--max-experiments", str(max_experiments)],
        capture_output=False
    )
    return result.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".", help="프로젝트 경로")
    parser.add_argument("--mode", choices=["analyze-only", "nightly", "full-loop"], default="nightly")
    parser.add_argument("--interval", default="24h", help="실행 주기 (예: 6h, 30m, 1d)")
    parser.add_argument("--max-experiments", type=int, default=1)
    parser.add_argument("--once", action="store_true", help="한 번만 실행")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    interval_sec = parse_interval(args.interval)

    print(f"[scheduler] 시작: project={project.name}")
    print(f"[scheduler] mode={args.mode}, interval={args.interval}")

    if args.once:
        run_loop(project, args.mode, args.max_experiments)
        return

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[scheduler] {now} — 루프 시작")

        try:
            returncode = run_loop(project, args.mode, args.max_experiments)
            if returncode != 0:
                print(f"[scheduler] 루프 실패 (code={returncode}) — 다음 주기에 재시도")
        except KeyboardInterrupt:
            print("\n[scheduler] 종료 (KeyboardInterrupt)")
            break
        except Exception as e:
            print(f"[scheduler] 예외: {e}")

        print(f"[scheduler] 다음 실행: {args.interval} 후")
        time.sleep(interval_sec)


if __name__ == "__main__":
    main()
