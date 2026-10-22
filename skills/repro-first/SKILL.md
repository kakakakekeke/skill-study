---
name: repro-first
description: Fixes a reported bug by first turning the report into one command that fails (a red reproduction), then making the smallest change that turns it green, then stating how the regression is prevented. Use when the user reports a bug, a wrong result, a crash, a traceback, or "X returns Y but should return Z" in code that has a test runner or can be run directly. Not for feature requests, questions about how code works, or one-character typo fixes the user has already pinpointed.
---

# repro-first

버그 수정은 가설 놀이가 되기 쉽다. 코드를 읽고 "아마 이거겠지" 하고 고치면, 맞았는지 알 길이 없고 다음 세션에서 같은 버그가 돌아온다. 이 스킬의 규칙은 하나다: **빨간불을 먼저 만든다.** 지금 실패하는 명령 하나가 없으면 아직 버그를 찾은 게 아니다.

## 절차

1. **재현 명령을 만든다.** 버그 보고를 한 줄 명령으로 바꾼다. 테스트 러너가 있으면 실패하는 테스트를 추가하고 그 테스트만 돌린다(`pytest tests/test_x.py::test_bug -x`, `npx jest -t "name"`). 없으면 `python -c` 나 스크립트로 직접 호출한다. **실행해서 실제로 실패하는 것을 본다.** 실패하지 않으면 보고와 다른 조건이 있다는 뜻이니 조건을 바꿔 다시 시도한다. 코드는 아직 건드리지 않는다.
2. **원인을 좁힌다.** 실패 메시지와 위치에서 시작한다. 재현 명령이 있으니 print나 작은 변형으로 가설을 바로 검증할 수 있다. 재현되지 않는 가설은 버린다.
3. **최소로 고친다.** 보고된 동작을 고치는 데 필요한 변경만. 주변 리팩터링은 하지 않는다. 재현 명령을 다시 돌려 초록불을 확인하고, 그다음 전체 스위트를 돌려 다른 것이 깨지지 않았는지 본다.
4. **재발 방지를 한 줄로 적는다.** 1번에서 추가한 테스트가 곧 방지책이다. 테스트로 못 잡는 종류(설정 누락, 환경)라면 아래 사다리에서 가장 가벼운 칸을 고른다: 기존 테스트 스위트 → 린터·타입 검사 → CI 검사 → (반복될 때만) 훅 → 문서.

## 보고 형식

마지막 메시지에 이 세 줄은 반드시 들어간다. 나중에 커밋 메시지와 회고가 이 줄을 쓴다.

```
재현: <실패했던 명령>
원인: <한 문장>
방지: <추가한 테스트 이름 또는 검사 위치>
```

## 범위를 지킬 것

- 사용자가 "뭐가 문제인지만 봐줘"라고 하면 1~2단계에서 멈추고 보고한다.
- 재현 명령이 30초 넘게 걸리면 더 좁은 명령을 찾는다. 느린 루프는 가설 검증을 게으르게 만든다.
- 외부 서비스가 필요해 재현이 불가능하면 그렇게 말하고, 가능한 가장 가까운 단위 재현(입력을 고정한 함수 호출)을 만든다.
