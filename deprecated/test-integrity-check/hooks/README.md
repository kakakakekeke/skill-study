# hooks/ — 옵트인 (기본 배치 안 함)

측정(2026-10-23, `docs/study/gate-eval-round-2.md` ③)에서 훅은 **보류**됐다. 스킬 단독으로 테스트 약화 0·충돌 보고 20/20이고, 훅은 정당한 테스트 갱신 과제를 0/5 완료로 만든다(오탐).

- `settings.json` — v2: PreToolUse `Edit|Write|MultiEdit|Bash`. Bash는 쓰기 명령(sed -i, perl -i, `>`, tee, rm, mv, 히어독)과 테스트 경로가 함께 있을 때만 막는다. opus는 기본 편집이 `sed -i`라 v1에는 걸리지 않았다.
- `settings-v1-edit-only.json` — v1: Edit|Write|MultiEdit만.
- `block_test_edits.py` — 훅 본체. `TEST_INTEGRITY_ALLOW=1`로 해제.

쓰려면 `${SKILL_DIR}`를 이 스킬의 절대 경로로 바꿔 프로젝트 `.claude/settings.json`의 `hooks`에 넣는다. 테스트 수정이 없어야 하는 세션(CI 수정 전용)에서만 켜는 것을 권한다.
