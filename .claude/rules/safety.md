---
paths:
  - "**"
---

# Server & Git Safety

- 다른 사용자의 프로세스를 kill하지 않는다
- 다른 사용자가 사용 중인 GPU는 자동 회피 (`find_free_gpus(avoid_other_users=True)`)
- 사용 중인 포트에 바인딩하지 않는다 — `find_free_port()` 사용
- `git push --force`, `git reset --hard`, `rm -rf`, `git clean -f` 금지
- git add는 변경한 파일만 — `git add -A` 금지
