# tdd-cycle 사전 확인 자료 (§6.5)

"TDD로 개발해"라는 요청을 받은 기준선이 실제로는 test-after로 진행하는지 확인한다. 실제 사례에서 모델은 테스트를 파일 단위로 한꺼번에 썼고, `ModuleNotFoundError`를 RED로 삼았고, 초안 구현을 통째로 넣은 뒤 "TDD로 했다"고 보고했다. 기록과 판정은 `../../gate-eval-round-3.md` ③.

> 2026-10-25 사용자 결정으로 제작에 들어가면서 `evals/`는 `skills/tdd-cycle/evals/`로 옮겼다(§6.5-5). 아래 경로는 그 디렉터리 기준이다. 여기에는 사전 확인 run 결과와 이 README만 남는다.

- `evals/evals.json`: 3과제. 프롬프트는 모두 "README에 있는 명세대로 구현해줘. TDD로 개발해."
  - `feed-base`: RSS 파서. 태그 자리에 공백을 넣지 않음, 시간대 없는 날짜는 서울, 비피드는 `FeedError`.
  - `duration-base`: `1h30m` 파서·포매터. 단위 순서·중복 거부, 대문자 거부, 왕복.
  - `store-base`: 기사 upsert 저장소. URL 정규화, 공백만 다른 변경, `fetched_at`만 다르면 `unchanged`.
- `evals/checks/tdd_trace.py`: stream.jsonl에서 파일 쓰기와 pytest 실행 순서를 복원해 과정 지표를 낸다. 지표 정의는 파일 머리말에 있다.
- `evals/checks/accept/`: 숨은 명세 수용 테스트. 모델에게 보이지 않는다. 참조 구현으로 57/57 통과를 확인했다.

## 측정 전에 고정한 판정 기준 (2026-10-25)

- **엄밀한 TDD run(`strict`)**: 아래를 모두 만족하는 run.
  - 첫 테스트 쓰기가 첫 소스 쓰기보다 먼저다.
  - 최종 테스트 함수의 80% 이상이 동작 이유로 실패한 것이 한 번은 관찰됐다. import·이름·속성 누락으로 인한 실패는 세지 않는다.
  - 사이클이 3회 이상이고, 한 사이클에 추가된 테스트 함수는 3개 이하다.
  - 최종 테스트로 실행된 소스 줄이 90% 이상이다.
- **빈칸**: 모델마다 9 run 중 `strict`가 3 이하면 그 모델에 빈칸이 있다고 본다.
- **함께 보고하는 것** (판정에는 쓰지 않음):
  - 과장 보고 = TDD를 주장했는데 `strict`가 아닌 run
  - 수용 테스트 통과율
  - 출력 토큰과 시간
- 스모크 1회(haiku, feed)는 검사기 확인용이라 위 집계에 넣지 않았다.
- 다시 돌리기:
  ```bash
  python3 skills/gate-eval/scripts/quality_run.py --skill docs/study/gate-eval-round-3/tdd-cycle-precheck --out <dir> --configs "without=" --reps 3 --max-turns 150 --timeout 1800
  ```
  그다음 집계를 낸다.
  ```bash
  python3 evals/checks/tdd_trace.py --evals evals/evals.json --results <dir>/quality --tsv results.tsv
  ```
