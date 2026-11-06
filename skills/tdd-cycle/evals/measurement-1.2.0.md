# tdd-cycle 1.2.0 측정 설계 (측정 전 기록, 2026-11-06)

원칙 §2 "층을 쌓을 때": 훅 층의 변경은 **바로 아래 구성 대비 증분**으로 잰다. 1.2.0의 아래 구성은 1.1.0(스킬+훅)이다.

## 조건

| 조건 | 내용 | 스킬 디렉터리 |
|---|---|---|
| `prev` | 1.1.0 스킬 + 1.1.0 훅 | `git archive 2f6d6d3 skills/tdd-cycle`로 복원한 사본(`evals/results/<날짜>/prev-1.1.0/skills/tdd-cycle`, gitignore) |
| `both` | 1.2.0 스킬 + 1.2.0 훅 | `skills/tdd-cycle` (이 커밋) |

- `without`·`with`(스킬만)는 다시 돌리지 않는다. 같은 날(11-06) 1.1.0 측정에서 두 모델 품질형 통과했고(`docs/study/gate-eval-round-3.md` ⑤), 1.2.0은 스킬 본문의 절차를 바꾸지 않았다(훅 규칙 설명과 두 명령 추가). 스킬 게이트 판정은 그 결과를 쓴다.
- G1은 재측정하지 않는다. description이 그대로다.
- 케이스 7개(evals.json)·fixture·수용 테스트는 1.1.0과 동일(`git diff 2f6d6d3 -- evals/` 빈 출력). 채점은 두 조건 모두 1.2.0 검사기(`checks/`)로 한다. 검사기 변경은 지표 추가(acks·big_steps·hook_blocks)와 `--ack/--big-step/--status`를 pytest 실행으로 세지 않는 것뿐이고, 기존 지표의 정의는 바뀌지 않았다.
- 모델 haiku·sonnet, 반복 3, `--max-turns 150 --timeout 900`, workers 6 (1.1.0과 같음). runlog 플러그인(`checks/runlog`)을 환경변수로 켠다.

## 가설과 판정

1.2.0이 겨냥하는 지표와 예상:

| 지표(assertion) | 겨냥 | 예상 |
|---|---|---|
| `red_behavior` ≥ 0.8 | 실패 3 | 오름 (1.1.0 both: haiku 5/18·sonnet 7/18 run만 통과) |
| `gated` (RED 없이 소스 쓰기 0) | 실패 2 + 빈틈(출력 못 읽음) | 오름 (1.1.0 both: 15/18·15/18) |
| `cycles`·`small_batch`·`honest` | — | 변화 없음 |
| `accept`·`suite_green`·`coverage` | 회귀 감시 | 변화 없음 (1.1.0: 전부 만점) |
| `dedup`(refactor-base) | 오탐 fixture | 변화 없음 (9/9) |

판정(모델마다): `both` vs `prev` 층화 순열 p < 0.05 **그리고** 순Δ ≥ 5%p **그리고** 셀 회귀 0 → 1.2.0 등록(version 1.2.0). 하나라도 실패 → 1.2.0을 버리고 1.1.0 유지(§6.4-2). 두 모델 모두 통과해야 한다.

참고로 보고하는 것(판정에 쓰지 않음): `acks`·`big_steps`(게이트가 선언으로 풀린 횟수. 매 사이클 선언하면 게이트는 방지턱이다), `hook_blocks`, 증분 비용(출력 토큰·시간; 1.1.0 증분은 +41%/+18%였다), trace의 `src_unarmed` 잔여가 검사기 잡음인지 진짜 빈틈인지 정성 검토.

## 한도 15줄과 오탐

`SRC_GROWTH_LIMIT = 15`는 [잠정]이다. 1.1.0 trace에 사이클당 소스 증가 열이 없어 보정 근거가 없다. 이 측정의 fixture는 함수 몇 개짜리라 한도에 잘 걸리지 않을 것이고, "정당하게 큰 첫 걸음"(클래스 골격) fixture는 없다. 그래서 이 측정은 한도가 **정당한 작업을 막아 결과를 나쁘게 하는가**를 refactor-base와 `accept`로만 간접 확인한다. `big_steps`가 사이클 수에 가까우면 한도가 낮다는 신호다.

## 실행

```
OUT=skills/tdd-cycle/evals/results/2026-11-06
mkdir -p $OUT/prev-1.1.0 && git archive 2f6d6d3 skills/tdd-cycle | tar -x -C $OUT/prev-1.1.0
export PYTHONPATH=$PWD/skills/tdd-cycle/evals/checks/runlog PYTEST_PLUGINS=pytest_runlog RUNLOG_DIR=$PWD/$OUT/runlog
python3 skills/gate-eval/scripts/quality_run.py --skill $OUT/prev-1.1.0/skills/tdd-cycle --out $OUT --models haiku,sonnet --reps 3 \
  --max-turns 150 --timeout 900 --configs prev=skill+hook --hook $OUT/prev-1.1.0/skills/tdd-cycle/evals/hook-settings.json
python3 skills/gate-eval/scripts/quality_run.py --skill skills/tdd-cycle --out $OUT --models haiku,sonnet --reps 3 \
  --max-turns 150 --timeout 900 --configs both=skill+hook --hook skills/tdd-cycle/evals/hook-settings.json
unset PYTHONPATH PYTEST_PLUGINS RUNLOG_DIR
python3 skills/gate-eval/scripts/grade.py --skill skills/tdd-cycle --out $OUT
python3 skills/gate-eval/scripts/report.py --skill skills/tdd-cycle --out $OUT --baseline prev
python3 skills/tdd-cycle/evals/checks/tdd_trace.py --evals skills/tdd-cycle/evals/evals.json --results $OUT/quality --tsv $OUT/trace.tsv
```
