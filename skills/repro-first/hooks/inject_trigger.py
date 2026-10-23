#!/usr/bin/env python3
"""UserPromptSubmit 훅(옵트인): 요청이 버그 신고로 보이면 repro-first를 쓰라는 한 줄을 주입한다.

원칙 §2 "수행 중 호출률과 보완"의 ③. 형제 스킬이 함께 설치되면 모델이 repro-first를 덜 고른다
(수행 중 호출 haiku 11%·sonnet 56%). 결정적 패턴 하나로 판정하고, 맞지 않으면 아무것도 출력하지 않는다.
판정: (증상 신호: 틀린 결과·크래시·traceback·"should be" 등, 또는 "fix/고쳐" 계열 단어) AND NOT 제외 신호
(테스트·문서 작성, 설명, 리뷰, 분류, 기능 추가, 명령형 리팩터링, 정확한 수정 지시). 버그 신고는 "고쳐 달라"를 생략하는 일이 많다. 끄기: REPRO_FIRST_INJECT=0.
"""
import json
import os
import re
import sys

SYMPTOM = re.compile(
    r"returns?\s+\S.{0,60}\b(should|instead)\b|should (be|return|default)|instead of|\bwrong\b|off by (one|\d)|"
    r"\bcrash(es|ed|ing)?\b|traceback|File \"[^\"]+\", line \d+|\b[A-Z]\w*(Error|Exception)\b|\bbug\b|broken|"
    r"\bdrops?\b|one fewer|doesn'?t work|does not work|isn'?t working|still (returns|a bug|there)|"
    r"안 ?돼|안 ?된다|안 ?됨|끊겨|오류|에러|버그|이상해|잘못|틀려",
    re.I)
FIX_WORD = re.compile(r"\bfix\b|sort it out|고쳐|해결해", re.I)
EXCLUDE = re.compile(
    r"\b(add|write)\b.{0,30}\b(tests?|changelog|root-cause|postmortem|docs?|readme|flag|option)\b|"
    r"\bsummari[sz]e|\bexplain|\breview\b|\btriage|close ticket|just change|just fix that|\btypo\b|"
    r"\bsupport\b.{0,30}\b(also|not just)|\bimplement\b|^\s*refactor\b|\brefactor (the|this)\b|\bflaky\b|how often|"
    r"which of our|already fixed on main|설명해|리팩터링",
    re.I)

MESSAGE = ("repro-first: 이 요청은 버그 신고로 보입니다. repro-first 스킬을 사용해 실패하는 재현 명령부터 만들고, "
           "최소 수정으로 통과시킨 뒤 재발 방지 위치를 적으십시오.")


def classify(prompt: str) -> bool:
    if EXCLUDE.search(prompt):
        return False
    return bool(SYMPTOM.search(prompt) or FIX_WORD.search(prompt))


def main() -> None:
    if os.environ.get("REPRO_FIRST_INJECT") == "0":
        return
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return
    if classify(str(data.get("prompt") or "")):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": MESSAGE}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
