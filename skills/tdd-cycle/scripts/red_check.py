#!/usr/bin/env python3
"""pytest를 돌리고 결과를 RED(동작)·RED(잘못된 이유)·GREEN으로 판정한다. 출력은 15줄 이내.

사용: python3 red_check.py <pytest 인자...>   예: python3 red_check.py tests/test_feed.py::test_br_is_space
      python3 red_check.py                   전체 스위트
      python3 red_check.py --refactor        초록 상태에서 리팩터링 창을 연다(동작을 바꾸지 않는 정리만, 다음 실행에서 닫힘)
      python3 red_check.py --status          이 세션의 사이클 요약 한 줄
종료 코드: 0 RED(동작) · 1 GREEN · 2 RED(잘못된 이유: import·이름·속성·시그니처 누락) · 3 테스트 없음/기타
훅(hooks/tdd_gate.py)이 켜져 있으면 같은 상태 파일을 보고 소스 수정을 허용·차단한다.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tdd_state import apply_run, fresh, is_missing, load, marker_on, parse_pytest, project_root, save, summary  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    root = project_root()
    st = load(root) or fresh(None, "project" if marker_on(root) else "off")
    if args == ["--status"]:
        print(summary(st))
        return 0
    if args == ["--refactor"]:
        if st["state"] != "green":
            print(f"리팩터링 창은 초록에서만 연다. 지금 상태: {st['state']}. 먼저 `red_check.py`(전체 스위트)로 초록을 확인한다.")
            return 3
        st["state"] = "refactor"
        st["refactors"] += 1
        st["log"].append({"via": "refactor", "result": "refactor"})
        save(root, st)
        print("리팩터링 창 열림: 동작을 바꾸지 않는 정리만 한다. 새 동작은 테스트부터. 끝나면 `red_check.py`로 전체 스위트가 초록인지 확인한다(창이 닫힌다).")
        return 0
    env = {**os.environ, "COLUMNS": "200"}
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rA", "--tb=line", "-p", "no:cacheprovider", *args],
                       capture_output=True, text=True, env=env)
    out = p.stdout + p.stderr
    parsed = parse_pytest(out)
    s_line = next((ln.strip("= ") for ln in reversed(out.splitlines()) if re.search(r"\d+ (passed|failed|error)|no tests ran", ln)), "")
    if p.returncode == 5 or parsed["result"] is None:
        print(f"테스트 없음/실행 실패: {s_line or ' '.join(out.strip().splitlines()[-1:])}")
        return 3
    notes = apply_run(st, parsed, "red_check", root)
    save(root, st)
    if parsed["result"] == "green":
        print(f"GREEN: {s_line}")
        for n in notes:
            print(n)
        if not notes:
            print("RED 단계에서 이게 나왔다면 이 테스트는 새 동작을 요구하지 않는다. 기대값이 명세와 맞는지, 구현이 앞서 나가지 않았는지 본다.")
        return 1
    failed = [(n, r) for n, r in parsed["failed"].items()]
    if parsed["result"] == "red":
        print(f"RED (동작): {s_line}")
        for n, r in [(n, r) for n, r in failed if r and not is_missing(r)][:5]:
            print(f"  FAILED {n} - {r[:160]}")
        for n in notes:
            print(n)
        print("다음: 이 실패만 없애는 가장 작은 코드를 쓴다. 상수 반환이나 분기 하나로 통과되면 그렇게 한다.")
        return 0
    print(f"RED (잘못된 이유): {s_line}")
    shown = [f"  FAILED {n} - {r[:160]}" for n, r in failed if r] + [f"  ERROR {e[:160]}" for e in parsed["errors"]]
    e_lines = [ln.strip() for ln in out.splitlines() if ln.startswith("E ")]
    for ln in (shown or e_lines)[:4]:
        print(ln)
    print("아직 동작을 검사하지 못했다. 없는 모듈·함수·인자를 스텁으로 만든다(시그니처만, pass 또는 빈 값 반환).")
    print("그다음 다시 돌려 assertion으로 실패하는지 본다. 동작은 아직 구현하지 않는다.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
