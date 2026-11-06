# 1.2.0 후보 (기각, 2026-11-06)

1.1.0에 세 게이트(결과 못 읽은 pytest → unknown, RED 없음 `--ack`, 사이클 15줄 `--big-step`)와 첫 거부 시 SKILL.md 주입을 더한 변경안.
`prev`(1.1.0) 대비 증분 순Δ −0.6%p(두 모델), 셀 회귀 0, 동작 RED 비율 변화 없음 → 기각. 기록: `docs/study/gate-eval-round-3.md` ⑥, 설계: `../../measurement-1.2.0.md`.

- `hooks/tdd_gate.py`, `hooks/hooks.json`, `scripts/tdd_state.py`, `scripts/red_check.py`, `SKILL.md`: 1.2.0 전체.
- `tests/test_tdd_gate.py`: 훅을 stdin JSON으로 구동하는 단위 테스트 33개. `python3 -m pytest skills/tdd-cycle/evals/candidates/1.2.0-gates/tests -q`
- 부활하려면 `skills/tdd-cycle/{hooks,scripts,SKILL.md}`로 되돌리고 hook-settings·hooks.json의 PreToolUse 매처에 `Skill`을 더한 뒤 세 게이트를 다시 잰다.
