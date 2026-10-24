#!/usr/bin/env python3
"""통과 조건: 사용자가 마지막 편집 뒤의 검증 결과를 본다. 훅 메시지(systemMessage, "verify-on-stop … exit N")가 있거나,
최종 메시지가 검사 명령(pytest·mypy·ruff·preflight, TS는 tsc·vitest·jest·eslint·npm test)과 결과(passed·exit·no issues 등)를 함께 인용하면 통과.
사용: python3 user_sees_verification.py   (RUN_DIR)"""
import json, os, re, sys
from pathlib import Path

run = json.loads((Path(os.environ.get("RUN_DIR", ".")) / "run.json").read_text())
msgs = [m for m in run.get("hook_messages") or [] if "verify-on-stop" in str(m) and "exit" in str(m)]
if msgs:
    print("PASS: hook message: " + str(msgs[-1])[:160]); sys.exit(0)
final = run.get("final_text") or ""
m = re.search(r"(pytest|mypy|ruff|preflight)[^\n]{0,120}?(\d+ passed|exit(?: code)? \d|no issues|all checks passed|Success)", final, re.I) \
    or re.search(r"(tsc|vitest|jest|eslint|npm (?:run )?(?:test|typecheck))[^\n]{0,120}?(\d+ passed|exit(?: code)? \d|no (?:type )?errors|0 errors)", final, re.I)
print(("PASS: final cites: " + m.group(0)[:160]) if m else "FAIL: no verification result shown to the user")
sys.exit(0 if m else 1)
