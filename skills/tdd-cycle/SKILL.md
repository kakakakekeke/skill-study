---
name: tdd-cycle
description: Runs test-driven development one behavior at a time — one new test, a red run that fails on the missing behavior itself (not an ImportError), the smallest code that turns it green, then the next behavior — and ends with a cycle log instead of a bare "done with TDD". Use whenever the user asks to build, implement, or develop something with TDD, test-first, or red-green-refactor ("TDD로 개발해", "테스트 먼저 쓰고 구현해", "do this test-driven"), even if TDD is mentioned only in passing. Not for adding tests to code that already exists, fixing a reported bug (repro-first covers that), or explaining what TDD is.
---

# tdd-cycle

"TDD로 해 줘"라는 요청은 쉽게 형식만 남는다. 명세 전체를 테스트 파일 하나로 옮기고, 모듈이 없어서 난 `ModuleNotFoundError`를 RED로 치고, 머릿속에 미리 그린 구현을 한 번에 써서 GREEN을 만든 뒤 "TDD로 했다"고 보고한다. 이러면 어떤 테스트도 자기 동작 때문에 실패하는 모습을 보이지 않았고, 설계는 테스트가 아니라 미리 그린 구현이 정했다. 사용자가 TDD를 요청했다면 원하는 것은 이 순서 자체다.

## 언제 이 절차로 들어오는가

- 요청에 TDD·테스트 먼저가 있을 때. 그리고 **프로젝트가 TDD 모드일 때**(`.claude/tdd-mode` 파일 또는 `TDD_MODE=1`)는 요청에 TDD라는 말이 없어도 모든 소스 변경이 이 절차를 따른다.
- 이미 작업 중이라도 **소스 `.py`(테스트 제외)를 고치기 직전**이 이 절차의 입구다. 설명·조사를 하다가 구현이 필요해졌어도, 앞 사이클의 코드를 "조금 손보는" 것이어도 같다. 버그 수정이냐 개발이냐를 가르지 않는다. 변경이 동작을 바꾸면 그 동작의 테스트가 먼저다.
- 훅(`hooks/tdd_gate.py`)이 켜져 있으면 이 규칙을 직접 검사한다. 동작 이유로 실패하는 테스트가 없는 상태에서 소스를 고치려 하면 막고 이유를 돌려준다. 막혔다면 우회하지 말고 그 자리에서 2번부터 시작한다. pytest 출력은 `tail`·`grep`으로 자르지 않는다. 훅이 결과를 읽지 못하면 `red_check.py`로 다시 돌릴 때까지 소스 수정이 막힌다.

## 사이클

1. **할 일 목록을 만든다.** 명세나 요청을 작은 동작 목록으로 쪼갠다(한 줄에 하나, 예: "태그 자리에 공백을 넣지 않는다"). 테스트는 아직 쓰지 않는다. 구현도 아직 그리지 않는다. 목록은 응답이나 TodoWrite에 둔다.
2. **테스트 하나를 쓴다.** 목록의 다음 동작 하나만 검사한다. 기대값은 명세에서 가져온다. "구현이 아마 이렇게 낼 것"에서 가져오면 테스트가 구현의 버릇을 굳힌다.
3. **RED를 확인한다.** 그 테스트만 돌린다.
   `python3 <이 스킬 디렉터리>/scripts/red_check.py tests/test_x.py::test_name`
   - `RED (동작)`이면 4로 간다.
   - `RED (잘못된 이유)`면 아직 아무것도 검사하지 못했다는 뜻이다. 없는 모듈·함수·인자를 **스텁**(시그니처만, `pass` 또는 빈 값 반환)으로 만들고 다시 돌린다. 이 상태에서는 스텁 말고는 소스에 아무것도 넣지 않는다. 훅이 켜져 있으면 본문이 있는 함수는 거부된다.
   - `GREEN`이면 이 테스트는 새 동작을 요구하지 않는다. 기대값을 다시 본다. 기대값이 맞다면 앞 사이클의 구현이 테스트가 요구하지 않은 동작을 먼저 넣은 것이다. 보고에 "RED 없음"으로 적는다.
4. **GREEN으로 만든다.** 이 테스트를 통과시키는 가장 작은 코드만 쓴다. 상수 반환이나 분기 하나로 통과되면 그렇게 하고, 일반화는 다음 테스트가 강제할 때 한다(삼각측량). 다음 동작을 미리 넣지 않는다. 미리 써 둔 구현을 복사해 넣지 않는다. 한 사이클에 소스가 15줄 넘게 늘면 테스트 하나가 요구한 것보다 많이 쓴 것이다(`red_check.py`가 GREEN에서 줄 수를 알려 준다). 그 테스트를 다시 돌린 뒤 전체 스위트도 돌린다(`red_check.py` 인자 없이).
5. **정리한다.** 초록인 상태에서만 중복을 걷어 낸다. 훅이 켜져 있으면 `red_check.py --refactor`로 창을 연 뒤 고치고, 끝나면 전체 스위트로 초록을 확인한다(창이 닫힌다). 동작이 바뀌는 변경은 정리가 아니다. 2로 간다.
6. 목록이 빌 때까지 2로 돌아간다. 하다가 새 동작이 떠오르면 목록에 더한다.

pytest가 아닌 러너(jest, go test 등)는 스크립트 대신 실패 메시지를 직접 읽는다. 판정 기준은 같다. 실패 이유가 "그 동작이 아직 없음"이어야 RED다. 훅은 `.py` 소스만 본다.

## 범위

- 명세 항목이 많아도 사이클당 테스트는 하나, 많아야 밀접한 경계값 두세 개다. 한 번에 여러 개를 쓰면 RED가 어느 동작 때문인지 가려진다.
- 파라미터화 테스트는 같은 동작의 경계값을 모을 때만 쓴다. 서로 다른 동작을 한 표에 넣지 않는다.
- 사용자가 순서를 바꾸라고 하면(예: "테스트는 나중에", "TDD 없이") 그 말을 따르고, 보고에 그렇게 적는다. "TDD 없이"는 훅의 모드도 끈다.

## 보고

마지막 메시지에 사이클 기록을 넣는다. 사용자가 실제로 TDD로 진행됐는지 판단할 근거다. 훅이 켜져 있으면 `red_check.py --status`의 요약 한 줄을 표 아래에 그대로 붙인다.

```
| # | 동작 | 테스트 | RED 이유 | GREEN |
| 1 | 태그 자리에 공백 없음 | test_inline_tag_no_space | assert 'A 새 모델 을' == ... | ✓ |
| 2 | 빈 제목은 ValueError | test_empty_title | RED 없음 | ✓ |
```

사이클을 건너뛰거나 묶은 곳, 리팩터링 창을 연 곳이 있으면 그 사실을 그대로 적는다. 묶었는데 "TDD로 했다"고만 쓰지 않는다.
