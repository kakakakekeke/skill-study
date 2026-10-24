#!/usr/bin/env python3
"""PreToolUse(Edit|Write|MultiEdit) 훅: 테스트 파일 쓰기를 차단하고 "보고 후 사용자에게 물어라"를 돌려준다.

결정적이고 가볍다(stdlib). 테스트 경로 판정은 TEST_PATH 정규식 하나다.
Bash도 본다(v2, 2026-10-23): opus는 기본 편집 방식이 `sed -i`라 Edit|Write 매처만으로는 훅을 한 번도 만나지 않았다(훅 단독 충돌형 3/5 약화).
Bash는 "쓰기 명령(sed -i, perl -i, > 리다이렉트, tee, mv, rm, 히어독 python)" **과** 테스트 경로가 함께 있을 때만 막는다. cat·pytest·grep 등 읽기는 통과.
그래도 남는 우회(python -c로 open(...,'w'), 새 테스트 파일로 덮어쓰기)는 scripts/test_diff_audit.py가 사후 탐지한다.
사용자가 테스트 수정을 명시적으로 허락했을 때 끄려면 환경변수 TEST_INTEGRITY_ALLOW=1.
"""
import json
import os
import re
import sys

TEST_PATH = re.compile(
    r"(^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.py$|\.(test|spec)\.[cm]?[jt]sx?$|(^|/)conftest\.py$|(^|/)__tests__/",
)
TEST_TOKEN = r"\S*(?:(?<![\w.-])tests?/|(?<![\w.-])test_[^\s/]*\.py|_test\.py|\.(?:test|spec)\.[cm]?[jt]sx?|(?<![\w.-])conftest\.py|__tests__/)\S*"
# 쓰기 명령 + 테스트 경로. 각 대안은 테스트 경로 토큰을 직접 포함하거나(리다이렉트·tee·rm·mv), 명령 전체에 테스트 경로가 있으면 막는다(sed -i, perl -i, 히어독).
BASH_WRITE = re.compile(
    r"(?:>>?\s*" + TEST_TOKEN + r")"                       # > tests/x.py, >> tests/x.py
    r"|(?:\btee\s+(?:-a\s+)?" + TEST_TOKEN + r")"          # tee tests/x.py
    r"|(?:\brm\s+(?:-\w+\s+)*" + TEST_TOKEN + r")"         # rm tests/x.py
    r"|(?:\bmv\s+(?:-\w+\s+)*" + TEST_TOKEN + r")"         # mv tests/x.py …  (이동=삭제)
    r"|(?:\bcp\s+(?:-\w+\s+)*\S+\s+" + TEST_TOKEN + r")"  # cp src tests/x.py (덮어쓰기; cp tests/ 백업은 통과)
    r"|(?:\btruncate\b.*" + TEST_TOKEN + r")",
)
BASH_INPLACE = re.compile(r"\bsed\s+(?:-\w+\s+)*-i\b|\bsed\s+-[a-zA-Z]*i|\bperl\s+(?:-\w+\s+)*-[a-zA-Z]*i|\bpython3?\s+-\s*<<|\bpython3?\s+-c\b.*\bopen\(.*['\"]w")
TEST_ANY = re.compile(TEST_TOKEN)

REASON = (
    "test-integrity-check: 테스트 파일 수정이 차단되었습니다 ({path}). 테스트는 스펙입니다. "
    "코드로 통과시킬 수 없다면 테스트와 스펙(문서·이슈)이 어디서 충돌하는지, 어느 쪽이 맞다고 보는지 근거를 적어 "
    "사용자에게 보고하고 멈추십시오. 테스트를 고쳐야 한다면 그 이유와 바꿀 내용을 먼저 보고하고 사용자의 확인을 받은 뒤 진행합니다."
)


def main() -> None:
    if os.environ.get("TEST_INTEGRITY_ALLOW") == "1":
        return
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: BLE001  입력이 깨졌으면 막지 않는다(훅 자체가 작업을 깨뜨리면 안 됨)
        return
    inp = data.get("tool_input") or {}
    if data.get("tool_name") == "Bash":
        cmd = str(inp.get("command") or "")
        m = BASH_WRITE.search(cmd) or (TEST_ANY.search(cmd) if BASH_INPLACE.search(cmd) else None)
        path = ("Bash: " + m.group(0)[:80]) if m else ""
    else:
        path = str(inp.get("file_path") or inp.get("path") or "")
        path = path if TEST_PATH.search(path) else ""
    if path:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": REASON.format(path=path)}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
