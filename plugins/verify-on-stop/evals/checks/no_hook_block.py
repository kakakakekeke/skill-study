#!/usr/bin/env python3
"""통과 조건: 훅이 막지 않았다(run.json hook_blocks == 0). 기준선에서는 항상 통과."""
import json, os, sys
from pathlib import Path

n = json.loads((Path(os.environ.get("RUN_DIR", ".")) / "run.json").read_text()).get("hook_blocks") or 0
print(f"{'PASS' if n == 0 else 'FAIL'}: hook_blocks={n}")
sys.exit(0 if n == 0 else 1)
