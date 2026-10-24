# verify-on-stop

Stop 훅. 이번 요청에서 소스 파일을 고쳤는데 그 뒤로 CI 검사가 돌지 않았으면, Claude가 끝내기 전에 `scripts/preflight.py`를 직접 돌린다. Python은 바뀐 파일과 연관된 테스트·ruff·mypy, JS/TS(package.json이 있을 때)는 연관 테스트(vitest 또는 jest)·`tsc --noEmit`·eslint다.

| preflight | 동작 |
|---|---|
| exit 0 | 막지 않음. `verify-on-stop: preflight → exit 0 (…)` 한 줄을 사용자에게 보여 준다 |
| exit 1 | 한 번만 막고 실패 요약을 돌려준다: "고치거나, 의도된·무관한 실패면 보고하고 멈춰라". 두 번째 종료는 막지 않고 결과만 보여 준다 |
| exit 2·시간 초과 | 막지 않음. "검증 못 함"만 보여 준다 |

- 개입하지 않는 경우: 코드 편집이 없을 때(설명, 문서만 수정), 마지막 편집 뒤에 preflight가 이미 돌았을 때. pytest만 돌린 경우는 검사로 치지 않는다(mypy 누락이 실제로 흔한 실패였다).
- 편집 탐지: Edit/Write/MultiEdit/NotebookEdit와 Bash 쓰기 명령(`sed -i`, 리다이렉트, 히어독 등). git 저장소면 `git diff`로 변경 파일을 잡는다.
- 끄기: `VERIFY_ON_STOP=0`. 요구 사항: python3. pytest·ruff·mypy는 있으면 쓰고, 없으면 건너뛴다. JS/TS 도구는 프로젝트의 `node_modules/.bin`에 있을 때만 쓴다(npx로 내려받지 않음). tsc·eslint가 설정 오류로 크래시하면 막지 않고 "실행 오류"로만 보인다.
- JS/TS 연관 테스트: 상대 import·re-export를 따라 바뀐 파일을 (간접으로) 쓰는 `*.test.*`·`*.spec.*`·`__tests__/`. tsconfig `paths` 별칭은 따라가지 않아 그 경로로만 쓰는 테스트는 선택에서 빠진다(선택이 비면 전체 스위트로 떨어지고, tsc는 프로젝트 전체를 보므로 타입 오류는 잡는다).
- 측정: `evals/`(Python 이득 3 + 오탐 4, TS 이득 3 + 오탐 1 fixture), 결과는 `docs/study/gate-eval-round-2.md` ④·⑩. TS fixture는 `npm ci --offline`으로 설치하므로 npm 캐시에 lockfile의 패키지가 있어야 한다.
