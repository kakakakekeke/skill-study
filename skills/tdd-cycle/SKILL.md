---
name: tdd-cycle
description: Runs test-driven development one behavior at a time — one new test, a red run that fails on the missing behavior itself (not an ImportError), the smallest code that turns it green, then the next behavior — and ends with a cycle log instead of a bare "done with TDD". Use whenever the user asks to build, implement, or develop something with TDD, test-first, or red-green-refactor ("TDD로 개발해", "테스트 먼저 쓰고 구현해", "do this test-driven"), even if TDD is mentioned only in passing. Not for adding tests to code that already exists, fixing a reported bug (repro-first covers that), or explaining what TDD is.
---

# tdd-cycle

"TDD로 해 줘"라는 요청은 쉽게 형식만 남는다. 명세 전체를 테스트 파일 하나로 옮기고, 모듈이 없어서 난 `ModuleNotFoundError`를 RED로 치고, 구현 전체를 한 번에 써서 GREEN을 만든 뒤 "TDD로 했다"고 보고한다. 이러면 어떤 테스트도 자기 동작 때문에 실패하는 모습을 보이지 않았다. 그래서 테스트가 그 동작을 정말 검사하는지 아무도 모른다. 설계도 테스트가 아니라 미리 머릿속에 그린 구현이 정한다. 사용자가 TDD를 요청했다면 원하는 것은 이 순서 자체다.

## 사이클

1. **할 일 목록을 만든다.** 명세나 요청을 작은 동작 목록으로 쪼갠다(한 줄에 하나, 예: "태그 자리에 공백을 넣지 않는다"). 테스트는 아직 쓰지 않는다. 목록은 응답이나 TodoWrite에 둔다.
2. **테스트 하나를 쓴다.** 목록의 다음 동작 하나만 검사한다. 기대값은 명세에서 가져온다. "구현이 아마 이렇게 낼 것"에서 가져오면 테스트가 구현의 버릇을 굳힌다.
3. **RED를 확인한다.** 그 테스트만 돌린다.
   `python3 <이 스킬 디렉터리>/scripts/red_check.py tests/test_x.py::test_name`
   - `RED (동작)`이면 4로 간다.
   - `RED (잘못된 이유)`면 아직 아무것도 검사하지 못했다는 뜻이다. 없는 모듈·함수·인자를 스텁(시그니처만, 빈 값 반환)으로 만들고 다시 돌린다. 동작은 아직 넣지 않는다.
   - `GREEN`이면 이 테스트는 새 동작을 요구하지 않는다. 앞 단계 구현이 앞서 나갔거나 기대값이 틀렸다는 신호다. 기대값을 다시 본다. 경계 확인용으로 남길 때는 보고에 "RED 없음"으로 적는다.
4. **GREEN으로 만든다.** 이 테스트를 통과시키는 가장 작은 코드만 쓴다. 다음 동작을 미리 넣지 않는다. 미리 써 둔 구현을 복사해 넣지 않는다. 그 테스트를 다시 돌린 뒤 전체 스위트도 돌린다.
5. **정리한다.** 초록인 상태에서만 중복을 걷어 낸다. 정리한 뒤에도 스위트가 초록이어야 한다.
6. 목록이 빌 때까지 2로 돌아간다. 하다가 새 동작이 떠오르면 목록에 더한다.

pytest가 아닌 러너(jest, go test 등)는 스크립트 대신 실패 메시지를 직접 읽는다. 판정 기준은 같다. 실패 이유가 "그 동작이 아직 없음"이어야 RED다.

## 범위

- 명세 항목이 많아도 사이클당 테스트는 하나, 많아야 밀접한 경계값 두세 개다. 한 번에 여러 개를 쓰면 RED가 어느 동작 때문인지 가려진다.
- 파라미터화 테스트는 같은 동작의 경계값을 모을 때만 쓴다. 서로 다른 동작을 한 표에 넣지 않는다.
- 사용자가 순서를 바꾸라고 하면(예: "테스트는 나중에") 그 말을 따르고, 보고에 그렇게 적는다.

## 보고

마지막 메시지에 사이클 기록을 넣는다. 사용자가 실제로 TDD로 진행됐는지 판단할 근거다.

```
| # | 동작 | 테스트 | RED 이유 | GREEN |
| 1 | 태그 자리에 공백 없음 | test_inline_tag_no_space | assert 'A 새 모델 을' == ... | ✓ |
```

사이클을 건너뛰거나 묶은 곳이 있으면 그 사실을 그대로 적는다. 묶었는데 "TDD로 했다"고만 쓰지 않는다.
