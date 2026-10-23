#!/usr/bin/env python3
"""TDD red 과제 검사: outputs/tests/test_inventory.py에 ValueError를 기대하는 새 테스트가 있고, 그 파일을 돌리면
새 테스트만 실패하고 원래 두 테스트는 통과한다(앱 코드 미수정 상태의 red)."""
import os, re, subprocess, sys
from pathlib import Path

out = Path(os.environ.get("RUN_DIR", ".")) / "outputs"
src = (out / "tests" / "test_inventory.py").read_text()
if "ValueError" not in src:
    print("FAIL: no ValueError expectation in tests/test_inventory.py"); sys.exit(1)
p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_inventory.py"], cwd=out, capture_output=True, text=True, timeout=120)
tail = (p.stdout + p.stderr).strip().splitlines()[-1:]
failed = int((re.search(r"(\d+) failed", p.stdout) or [0, 0])[1])
passed = int((re.search(r"(\d+) passed", p.stdout) or [0, 0])[1])
ok = failed >= 1 and passed >= 2
print(("PASS: " if ok else "FAIL: ") + " | ".join(tail))
sys.exit(0 if ok else 1)
