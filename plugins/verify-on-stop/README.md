# verify-on-stop

Stop 훅. 이번 요청에서 소스 파일을 고쳤는데 그 뒤로 CI 검사가 돌지 않았으면, Claude가 끝내기 전에 `scripts/preflight.py`(바뀐 파일과 연관된 테스트, ruff, mypy)를 직접 돌린다.

| preflight | 동작 |
|---|---|
| exit 0 | 막지 않음. `verify-on-stop: preflight → exit 0 (…)` 한 줄을 사용자에게 보여 준다 |
| exit 1 | 한 번만 막고 실패 요약을 돌려준다: "고치거나, 의도된·무관한 실패면 보고하고 멈춰라". 두 번째 종료는 막지 않고 결과만 보여 준다 |
| exit 2·시간 초과 | 막지 않음. "검증 못 함"만 보여 준다 |

- 개입하지 않는 경우: 코드 편집이 없을 때(설명, 문서만 수정), 마지막 편집 뒤에 preflight가 이미 돌았을 때. pytest만 돌린 경우는 검사로 치지 않는다(mypy 누락이 실제로 흔한 실패였다).
- 편집 탐지: Edit/Write/MultiEdit/NotebookEdit와 Bash 쓰기 명령(`sed -i`, 리다이렉트, 히어독 등). git 저장소면 `git diff`로 변경 파일을 잡는다.
- 끄기: `VERIFY_ON_STOP=0`. 요구 사항: python3. pytest·ruff·mypy는 있으면 쓰고, 없으면 건너뛴다.
- 측정: `evals/`(이득 3 + 오탐 4 fixture), 결과는 `docs/study/gate-eval-round-2.md` ④.
