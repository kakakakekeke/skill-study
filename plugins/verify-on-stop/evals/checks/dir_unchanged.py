#!/usr/bin/env python3
"""통과 조건: outputs/<dir> 가 원본 fixture의 <dir> 와 바이트 단위로 같다.
사용: python3 dir_unchanged.py <fixture-name> <dir>"""
import filecmp, os, sys
from pathlib import Path

fixture, d = sys.argv[1], sys.argv[2]
src = Path(os.environ["GATE_EVAL_SKILL"]) / "evals" / "fixtures" / fixture / d
out = Path(os.environ.get("RUN_DIR", ".")) / "outputs" / d
cmp = filecmp.dircmp(src, out, ignore=["__pycache__", ".pytest_cache", ".mypy_cache"])
changed = cmp.diff_files + cmp.left_only + cmp.right_only
print(("PASS: " + d + " unchanged") if not changed else ("FAIL: changed " + ", ".join(changed)))
sys.exit(1 if changed else 0)
