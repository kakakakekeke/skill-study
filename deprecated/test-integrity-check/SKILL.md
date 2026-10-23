---
name: test-integrity-check
description: Makes failing tests pass by changing application code only, and when no code change can satisfy a test (the test contradicts the documented spec, the issue, or another test) stops before touching the test and reports the conflict with evidence. Use whenever the task is to fix a red test suite, get CI green, make a specific test pass, or implement code against existing tests. Not for writing new tests, diagnosing flaky tests, or tasks where the user explicitly asks to update or rewrite tests for a new spec.
---

# test-integrity-check

막힌 에이전트는 테스트를 고친다. 코드로 통과시킬 수 없는 테스트를 만나면 assert를 지우고, `skip`을 붙이고, 기대값을 지금 나오는 값으로 바꾸고, 테스트 함수를 없앤다. 그러면 스위트는 초록이 되고 과제는 "완료"로 보이지만, 사용자가 테스트로 적어 둔 요구사항이 조용히 사라진다. 불가능한 과제를 준 측정에서 해킹의 대부분이 이 경로였고, 그 경로를 막아도 정상 과제의 성능은 거의 떨어지지 않았다. 이 스킬의 규칙은 하나다: **테스트는 스펙이다. 테스트를 바꾸는 결정은 사용자가 한다.**

## 절차

1. **실패를 읽는다.** 스위트를 돌리고, 실패한 테스트마다 "무엇을 기대하고 무엇이 나왔는가"를 적는다. 테스트가 참조하는 문서(README, docstring, 이슈)도 함께 읽는다. 기대값이 어디서 왔는지 알아야 다음 단계에서 충돌을 판별할 수 있다.
2. **코드만 고친다.** 테스트가 요구하는 동작을 애플리케이션 코드에서 구현한다. 테스트 파일, `conftest.py`, pytest 설정(`pytest.ini`, `pyproject.toml`의 `[tool.pytest]`)은 열어서 읽기만 한다.
3. **코드로 안 되는 테스트를 만나면, 테스트를 건드리기 전에 보고한다.** "안 된다"는 느낌이 아니라 근거다: 테스트 A는 X를 기대하는데 문서는 Y라고 적혀 있다, 또는 테스트 A와 테스트 B가 같은 입력에 다른 값을 기대한다. 이 상태에서 할 일은 테스트 수정이 아니라 **충돌 보고**다. 모호하지 않은 부분은 고치고, 충돌 부분은 아래 형식으로 적어 멈춘다. 추측으로 어느 한쪽을 고르지 않는다 — 어느 쪽이 맞는지는 코드가 아니라 요구사항의 문제이고, 그 답은 사용자에게 있다.
4. **테스트를 고치는 경우는 둘뿐이다.** (a) 과제 자체가 테스트 변경을 요구한다(API 이름 변경, 사용자가 명시한 스펙 변경). (b) 3단계 보고에 사용자가 "테스트를 고쳐라"고 답했다. 이때도 바꾸는 것은 과제가 요구한 그 부분만이다. 지나가다 발견한 "이상한" assert를 함께 손보지 않는다.
5. **끝나기 전에 테스트 변경을 감사한다.** 테스트 파일을 하나라도 수정했으면 작업 전 사본과 비교한다. 작업 시작 시 `cp -r tests "${TMPDIR:-/tmp}/tests-before"` 한 줄로 사본을 만들어 두고, 끝에 다음을 돌린다:
   ```bash
   python3 <skill-dir>/scripts/test_diff_audit.py "${TMPDIR:-/tmp}/tests-before" tests
   ```
   JSON 수십 줄과 종료 코드(0 = 약화 없음, 1 = 약화 항목 있음)가 나온다. 삭제된 테스트, 줄어든 assert, 추가된 skip/xfail, 바뀐 기대 리터럴, 느슨해진 비교가 열거된다. 1이 나왔는데 그 항목이 과제가 요구한 변경이 아니면 되돌린다. 이름 변경(rename)은 약화로 세지 않는다.

## 보고 형식

충돌로 멈출 때 최종 메시지에 이 세 줄이 들어간다. 사용자가 이 줄만 보고 결정할 수 있어야 한다.

```
충돌: <테스트 id>는 <X>를 기대. <문서 위치 | 다른 테스트 id>는 <Y>.
판단: <어느 쪽이 맞다고 보는지와 근거 한 문장>
변경: 테스트 무변경. 코드는 <고친 범위>까지. <테스트 | 문서> 수정 여부는 확인 필요.
```

테스트를 정당하게 고쳤을 때는 `감사: test_diff_audit → exit 0 (수정 N개, 약화 0)` 한 줄을 넣는다. 감사를 돌리지 않았으면 그렇게 적는다.

## 훅이 막았을 때

프로젝트에 `hooks/block_test_edits.py`가 걸려 있으면 테스트 경로의 Edit/Write가 거부되고 같은 지시가 돌아온다. 이것은 오류가 아니라 3단계로 가라는 신호다. `sed -i`나 리다이렉트, 새 파일 생성으로 우회하지 않는다 — 우회는 감사(5단계)에 그대로 잡히고, 사용자가 원한 것도 아니다. 과제가 테스트 변경을 요구하는 경우(4-a)면 그 사실과 바꿀 내용을 보고하고 사용자에게 훅 해제(`TEST_INTEGRITY_ALLOW=1`)나 직접 수정을 요청한다.
