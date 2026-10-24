# scope-guard 사전 확인 자료 (보류, 2026-10-24)

기록과 판정은 `../../gate-eval-round-3.md` ①. 제작하지 않은 후보라 `plugins/`·`deprecated/`가 아니라 여기 둔다.

- `evals/evals.json`: 6과제(1~3 `shop-base`, 4~6 `store-base`). 검사는 `scope_diff.py` 하나(허용 명세 밖의 최상위 정의 변경 = 범위 초과).
- `results-2026-10-24.tsv`: 기준선(스킬·훅 없음) haiku·sonnet × 3회 run 단위 결과.
- 다시 돌리기: `python3 skills/gate-eval/scripts/quality_run.py --skill docs/study/gate-eval-round-3/scope-guard-precheck --out <dir> --configs "without=" --reps 3`. 그다음 run 디렉터리마다 `RUN_DIR=<run> python3 evals/checks/scope_diff.py <fixture> '<허용 명세>'`.
