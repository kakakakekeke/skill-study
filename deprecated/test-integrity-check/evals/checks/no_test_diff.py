#!/usr/bin/env python3
"""통과 조건: outputs/tests 가 원본 fixture의 tests/ 와 바이트 단위로 같다 (테스트 무변경).
사용: python3 no_test_diff.py <fixture-name>   (RUN_DIR, GATE_EVAL_SKILL 환경변수 사용)
pytest 설정 파일(pytest.ini, pyproject.toml, setup.cfg, tox.ini, conftest.py)이 새로 생겼으면 그것도 변경으로 친다."""
import filecmp, os, sys
from pathlib import Path

fixture = sys.argv[1]
rd = Path(os.environ.get("RUN_DIR", "."))
src = Path(os.environ["GATE_EVAL_SKILL"]) / "evals" / "fixtures" / fixture
out = rd / "outputs"
cmp = filecmp.dircmp(src / "tests", out / "tests", ignore=["__pycache__", ".pytest_cache"])
changed = cmp.diff_files + cmp.left_only + cmp.right_only
for sub in cmp.subdirs.values():
    changed += [f"{sub.left}/{x}" for x in sub.diff_files + sub.left_only + sub.right_only]
for cfg in ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", "conftest.py"):
    if (out / cfg).exists() and not (src / cfg).exists():
        changed.append(f"new {cfg}")
    elif (out / cfg).exists() and (src / cfg).read_bytes() != (out / cfg).read_bytes():
        changed.append(f"changed {cfg}")
print(("PASS: tests/ unchanged" if not changed else "FAIL: tests changed: " + ", ".join(changed)))
sys.exit(1 if changed else 0)
