---
name: test-digest
description: Condenses long test, build, type-check, or CI log output (pytest, jest/vitest, go test, cargo, tsc, GitHub Actions logs) into a failure summary of a few dozen lines using a deterministic script. Use whenever running a test suite or build, or reading a saved CI log, when the output could run past ~80 lines and the question is "what failed and why". Not for a single targeted test whose output is already short.
---

# test-digest

테스트·빌드 출력은 그대로 컨텍스트에 들어온다. 300줄짜리 트레이스백 더미는 토큰을 먹고, 원인 두 줄을 묻어 버린다. 이 스킬은 **출력을 결정적 스크립트로 먼저 압축**하고, 모델은 압축본만 읽는다. 파서 역할을 LLM에게 맡기지 않는다.

## 사용

출력을 파이프로 넘기거나 로그 파일을 준다. 스크립트 경로는 이 스킬 디렉터리의 `scripts/digest.py`다.

```bash
pytest -q 2>&1 | python3 <skill-dir>/scripts/digest.py
npm test 2>&1 | python3 <skill-dir>/scripts/digest.py
python3 <skill-dir>/scripts/digest.py ci.log
gh run view <id> --log-failed | python3 <skill-dir>/scripts/digest.py
```

형식(pytest/jest/go/cargo/tsc)은 자동 감지되고, 모르는 형식은 error·fail·traceback 줄과 끝부분만 남긴다. `--format`으로 강제할 수 있다. 종료 코드는 실패가 있으면 1이다.

출력 첫 줄 `[digest] N lines in -> M out, format=…`에서 N을 보면 원본이 얼마였는지 알 수 있다.

## 압축본으로 부족할 때

압축본에 원인이 안 보이면 **전체를 다시 찍지 말고 범위를 좁힌다.**

- 실패한 테스트 하나만 다시: `pytest path/test_x.py::test_name -x 2>&1 | tail -60`
- 특정 블록이 더 필요하면: `--lines 120`
- 파일이면 `grep -n` 으로 해당 테스트 이름 주변만.

좁힌 출력이 80줄 안이면 그때는 압축 없이 봐도 된다. 압축은 긴 출력을 위한 것이다.

## 보고

사용자에게는 실패한 테스트 이름, 원인(assertion·예외와 위치), 수정 방향을 말한다. 압축본을 그대로 붙이지 않는다. 경고(warnings)는 실패 원인이 아니면 한 줄로만.
