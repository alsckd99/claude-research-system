"""
configs/*.yaml 파일들의 유효성을 검증한다.
hooks에서 config 수정 시 자동 실행.

최소한의 공통 필드만 검증한다. 프로젝트별 추가 검증은 이 파일을 수정해서 사용.
"""
import sys
from pathlib import Path

import yaml


# 모든 프로젝트에 필요한 최소 필드
REQUIRED_BASE_FIELDS = [
    "project_name",
    "primary_metric",
    "seed",
]


def validate_base_config(config: dict, path: str) -> list:
    errors = []

    for field in REQUIRED_BASE_FIELDS:
        if field not in config:
            errors.append(f"[{path}] 필수 필드 누락: '{field}'")

    if "seed" in config and not isinstance(config["seed"], int):
        errors.append(f"[{path}] seed는 정수여야 합니다")

    return errors


def main():
    config_dir = Path("configs")
    if not config_dir.exists():
        print("[validate] configs/ 디렉토리 없음 — 스킵")
        return 0

    yaml_files = list(config_dir.glob("*.yaml"))
    if not yaml_files:
        print("[validate] yaml 파일 없음 — 스킵")
        return 0

    all_errors = []

    for yaml_path in yaml_files:
        try:
            with open(yaml_path) as f:
                config = yaml.safe_load(f)
            if config is None:
                print(f"[validate] {yaml_path}: 빈 파일 — 스킵")
                continue

            if yaml_path.name == "base.yaml":
                errors = validate_base_config(config, yaml_path.name)
                all_errors.extend(errors)
            else:
                print(f"[validate] {yaml_path.name}: OK (기본 검증)")

        except yaml.YAMLError as e:
            all_errors.append(f"[{yaml_path}] YAML 파싱 오류: {e}")

    if all_errors:
        print("[validate] 검증 실패:")
        for err in all_errors:
            print(f"  {err}")
        return 1
    else:
        print(f"[validate] 모든 config 검증 통과 ({len(yaml_files)}개 파일)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
