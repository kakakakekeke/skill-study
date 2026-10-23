---
name: verify-before-done
description: Carries out a change to application code in a repo with tests, a type checker, or a linter and finishes it with a fresh run of tests, type check, and lint and a read of the exit code, via a deterministic preflight script (changed-file test selection, ruff/mypy, short JSON). Use for any such change (a flag, a rename, a refactor), and when the user asks if a change is ready, what else broke, or to make sure CI passes. Not for writing new tests, configuring linters or CI, summarizing a failing log, measuring a flaky test, or explaining tests.
---

# verify-before-done

"테스트는 통과할 겁니다"는 검증이 아니다. 편집이 끝난 뒤 머릿속으로 결과를 추정하면 거짓 완료가 생긴다: 다른 모듈의 호출부가 깨지고, 테스트는 통과하는데 타입체크가 실패하고, import 오류로 테스트가 0개 실행됐는데 "통과"로 읽는다. 에이전트 PR 거절 사유 1위가 CI 실패다. 이 스킬의 규칙은 하나다: **마지막 편집 뒤에 새로 실행하고, exit code를 읽은 다음에만 완료라고 말한다.**

## 절차

1. 코드 변경을 끝낸다. 편집 중간에 돌린 결과는 마지막 편집 이후엔 무효다.
2. 실행한다. 스크립트는 이 스킬 디렉터리의 `scripts/preflight.py`다.
   ```bash
   python3 <skill-dir>/scripts/preflight.py            # git diff로 변경 파일 → 연관 테스트 + ruff + mypy
   python3 <skill-dir>/scripts/preflight.py --all      # 연관 선택이 못 미더우면 전체
   ```
   git이 없거나 변경 파일이 .py가 아니면 전체 스위트로 떨어진다. 출력은 JSON 수십 줄과 마지막 줄 `[preflight] verdict=… exit=…`. ruff·mypy가 설치돼 있지 않으면 `skipped`로 표시된다(통과가 아니다).
3. exit code를 읽는다.
   - `0` PASS: 테스트 1개 이상 통과, 린트·타입 깨끗.
   - `1` FAIL: 실패한 테스트나 린트·타입 오류가 있다. `first_failures`·`first`가 가리키는 것부터 고치고 1번으로 돌아간다.
   - `2` ZERO_TESTS_RAN: 테스트가 하나도 실행되지 않았다(수집 오류, import 실패, 빈 선택). 이것은 통과가 아니라 **실행 실패**다. `tail`의 ImportError를 먼저 고친다.
4. 그 다음에만 완료를 말한다. 최종 메시지에 마지막 실행을 그대로 인용한다:
   ```
   검증: python3 …/preflight.py → exit 0 (pytest 8 passed, ruff 0, mypy 0)
   ```
   실패 상태로 끝내야 하면 exit code와 남은 실패를 그대로 적는다. 고치지 못한 것을 숨기는 것보다 낫다.

## 실행하지 않았으면 그렇게 쓴다

"should pass", "probably works", "tests should be green now" 같은 추정 표현은 쓰지 않는다. 실행하지 못한 이유가 있으면(의존성 없음, 외부 서비스) "실행하지 않았다"와 이유를 적는다. 추정을 확인처럼 적는 것이 이 스킬이 막으려는 실패 그 자체다.

## preflight가 안 맞는 스택

JS/TS 등 Python이 아니면 해당 러너를 직접 돌리고 같은 규칙을 적용한다. 출력은 `| tail -30`으로 줄이고, 종료 코드는 `; echo "exit=$?"`로 읽는다.

```bash
npx vitest run 2>&1 | tail -30; echo "exit=${PIPESTATUS[0]}"
npx tsc --noEmit 2>&1 | tail -20; echo "exit=${PIPESTATUS[0]}"
```
