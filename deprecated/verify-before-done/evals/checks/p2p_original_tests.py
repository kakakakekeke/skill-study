#!/usr/bin/env python3
"""P2P 회귀 검사: 과제가 건드릴 이유가 없는 원본 fixture 테스트 파일을 outputs/에 그대로 복사해 돌린다.
사용: python3 p2p_original_tests.py <fixture-name> <test-file> [<test-file>...]
"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path

fixture, files = sys.argv[1], sys.argv[2:]
rd = Path(os.environ.get("RUN_DIR", "."))
src = Path(os.environ["GATE_EVAL_SKILL"]) / "evals" / "fixtures" / fixture
work = Path(tempfile.mkdtemp(prefix="p2p-"))
shutil.copytree(rd / "outputs", work, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".mypy_cache"))
for f in files:
    shutil.copy2(src / f, work / f)
p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *files], cwd=work, capture_output=True, text=True, timeout=300)
tail = [l for l in (p.stdout + p.stderr).splitlines() if l.strip()][-2:]
print(("PASS: " if p.returncode == 0 else "FAIL: ") + " | ".join(tail))
shutil.rmtree(work, ignore_errors=True)
sys.exit(0 if p.returncode == 0 else 1)
