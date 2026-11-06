# tdd-cycle 1.2.0 후보 "퇴화 사례 우선" 측정 설계 (측정 전 기록, 2026-11-06)

`docs/study/gate-eval-round-3.md` ⑥의 해석에서 나온 후보. 잔여 "RED 없음"은 앞 사이클의 최소 구현이 자연히 만족하는 퇴화 사례(빈 입력·없는 필드)를 뒤에 테스트로 쓴 것이었다. 소스 수정 게이트(기각된 1.2.0-gates)로는 못 잡고, 할 일 목록 **순서**의 문제다.

## 변경

SKILL.md만 바뀐다(훅·스크립트는 1.1.0 그대로). 1번 단계에 "순서는 퇴화 사례부터"(빈 입력·없는 필드·요소 하나 → 일반 → 여러 개·경계·오류, 조합 확인 테스트는 목록에 넣지 않음) 두 문장, 3번 GREEN 분기에 "퇴화 사례가 뒤에 놓인 경우 목록을 다시 본다" 한 문장. description 불변. 본문 44줄.

## 조건

| 조건 | 내용 |
|---|---|
| `prev` | 1.1.0 스킬 + 훅. **⑥ 측정(2026-11-06, CLI 2.1.318)의 `prev` run 42개를 그대로 쓴다.** 훅·하네스·날짜·CLI가 같고 처리와 무관한 조건이라 재실행하지 않는다(비용 절반). 같은 기준선을 두 번째 증분 판정에 쓰는 셈이므로 그 사실을 보고서에 적는다 |
| `both` | 이 커밋의 스킬 + 1.1.0 훅(동일 코드) |

케이스 7개·haiku·sonnet·반복 3·`--max-turns 150`, 채점은 현재 검사기. G1·`without`은 재측정하지 않는다(description·훅 불변).

## 가설과 판정

- 주 지표 `red_behavior`(≥0.8 run 수)가 오른다. prev: haiku 4/21·sonnet 10/21. 메커니즘이 맞다면 "RED 없이 통과" 건수(Stop 요약)가 줄어야 한다(prev: haiku 119·sonnet 78, ⑥ both 기준).
- `cycles`·`accept`·`suite_green`·`coverage`·`dedup`은 변화 없음(회귀 감시).
- 판정(모델마다): `both` vs `prev` 순열 p < 0.05 **그리고** 순Δ ≥ 5%p **그리고** 셀 회귀 0. 두 모델 통과 → 1.2.0 등록. 미달 → 1.1.0 유지, 본문 되돌림(`evals/SKILL-zero-first.md`에 보관).
- 프로즈 지침이라 모델이 따르지 않을 수 있다(§3.2 "지시로 강제는 선택지가 아니다"는 **강제**에 대한 규칙이고, 이건 절차의 순서 지침이다). 따랐는지는 transcript의 할 일 목록 순서로 정성 확인한다.

## 실행

```
OUT=skills/tdd-cycle/evals/results/2026-11-06-zero-first
mkdir -p $OUT/quality && cp -r skills/tdd-cycle/evals/results/2026-11-06/runlog $OUT/
for d in skills/tdd-cycle/evals/results/2026-11-06/quality/*/*/prev; do mkdir -p $OUT/quality/$(echo $d | cut -d/ -f6-7); cp -r $d $OUT/quality/$(echo $d | cut -d/ -f6-7)/; done
echo '{"prev": ["hook", "skill"]}' > $OUT/quality/configs.json
export PYTHONPATH=$PWD/skills/tdd-cycle/evals/checks/runlog PYTEST_PLUGINS=pytest_runlog RUNLOG_DIR=$PWD/$OUT/runlog
python3 skills/gate-eval/scripts/quality_run.py --skill skills/tdd-cycle --out $OUT --models haiku,sonnet --reps 3 --max-turns 150 --timeout 900 --configs both=skill+hook --hook skills/tdd-cycle/evals/hook-settings.json
unset PYTHONPATH PYTEST_PLUGINS
python3 skills/gate-eval/scripts/grade.py --skill skills/tdd-cycle --out $OUT --force
python3 skills/gate-eval/scripts/report.py --skill skills/tdd-cycle --out $OUT --baseline prev
python3 skills/tdd-cycle/evals/checks/tdd_trace.py --evals skills/tdd-cycle/evals/evals.json --results $OUT/quality --tsv $OUT/trace.tsv
```
