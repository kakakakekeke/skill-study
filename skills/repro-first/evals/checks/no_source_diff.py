#!/usr/bin/env python3
"""통과 조건: outputs/<pkg> 가 원본 fixture의 <pkg> 와 바이트 단위로 같다 (정답 중단: 이미 수정된 코드를 건드리지 않음).
사용: python3 no_source_diff.py <fixture-name> <pkg-dir>   예: slug-fixed slugger
negate 없이 쓰면 "변경 없음"이 통과. 부분 수정 fixture에서는 negate=true로 "변경 있음"을 검사한다."""
import filecmp, os, sys
from pathlib import Path

fixture, pkg = sys.argv[1], sys.argv[2]
rd = Path(os.environ.get("RUN_DIR", "."))
src = Path(os.environ["GATE_EVAL_SKILL"]) / "evals" / "fixtures" / fixture / pkg
out = rd / "outputs" / pkg
cmp = filecmp.dircmp(src, out, ignore=["__pycache__"])
changed = cmp.diff_files + cmp.left_only + cmp.right_only
print(("PASS: no change in " if not changed else "FAIL: changed in ") + pkg + (": " + ", ".join(changed) if changed else ""))
sys.exit(1 if changed else 0)
