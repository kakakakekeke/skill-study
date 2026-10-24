#!/usr/bin/env python3
"""pytest를 돌리고 결과를 RED(동작)·RED(잘못된 이유)·GREEN으로 판정한다. 출력은 15줄 이내.

사용: python3 red_check.py <pytest 인자...>   예: python3 red_check.py tests/test_feed.py::test_br_is_space
종료 코드: 0 RED(동작) · 1 GREEN · 2 RED(잘못된 이유: import·이름·속성·시그니처 누락) · 3 테스트 없음/기타
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

MISSING = re.compile(r"ModuleNotFoundError|ImportError|cannot import name|NameError|has no attribute|"
                     r"not callable|unexpected keyword argument|positional argument|takes no arguments")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip().splitlines()[2])
        return 3
    env = {**os.environ, "COLUMNS": "200"}
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rfE", "--tb=line", "-p", "no:cacheprovider", *args],
                       capture_output=True, text=True, env=env)
    out = p.stdout + p.stderr
    summary = next((ln.strip("= ") for ln in reversed(out.splitlines()) if re.search(r"\d+ (passed|failed|error)|no tests ran", ln)), "")
    failed = re.findall(r"^(FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$", out, re.M)
    e_lines = [ln.strip() for ln in out.splitlines() if ln.startswith("E ") or re.match(r"^\S+:\d+: \w+(Error|Exception)", ln)]
    if p.returncode == 0:
        print(f"GREEN: {summary}")
        print("RED 단계에서 이게 나왔다면 이 테스트는 새 동작을 요구하지 않는다. 기대값이 명세와 맞는지, 구현이 앞서 나가지 않았는지 본다.")
        return 1
    if p.returncode == 5 or not (failed or e_lines):
        print(f"테스트 없음/실행 실패: {summary or out.strip().splitlines()[-1:]}")
        return 3
    reasons = [r or "" for _, _, r in failed] + e_lines
    missing = [r for r in reasons if MISSING.search(r)]
    behavior = [(k, n, r) for k, n, r in failed if k == "FAILED" and r and not MISSING.search(r)]
    if behavior:
        print(f"RED (동작): {summary}")
        for _, n, r in behavior[:5]:
            print(f"  {n} - {r[:160]}")
        print("다음: 이 실패만 없애는 가장 작은 코드를 쓴다.")
        return 0
    print(f"RED (잘못된 이유): {summary}")
    for r in (missing or reasons)[:4]:
        print(f"  {r[:160]}")
    print("아직 동작을 검사하지 못했다. 없는 모듈·함수·인자를 스텁으로 만든다(시그니처만, 빈 값 반환).")
    print("그다음 다시 돌려 assertion으로 실패하는지 본다. 동작은 아직 구현하지 않는다.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
