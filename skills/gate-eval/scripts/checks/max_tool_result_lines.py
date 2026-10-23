#!/usr/bin/env python3
"""통과 조건: Bash tool_result 중 가장 긴 것이 N줄 이하 (토큰 규율 검사).
사용: python3 max_tool_result_lines.py 80   (RUN_DIR 환경변수 또는 cwd의 stream.jsonl)"""
import json, os, sys
from pathlib import Path

limit = int(sys.argv[1]) if len(sys.argv) > 1 else 80
rd = Path(os.environ.get("RUN_DIR", "."))
events = [json.loads(l) for l in (rd / "stream.jsonl").read_text().splitlines() if l.strip()]
bash_ids = set()
for ev in events:
    if ev.get("type") == "assistant":
        for c in ev["message"].get("content", []):
            if c.get("type") == "tool_use" and c.get("name") == "Bash":
                bash_ids.add(c["id"])
worst, worst_n = None, 0
for ev in events:
    if ev.get("type") != "user":
        continue
    for c in ev["message"].get("content", []):
        if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("tool_use_id") in bash_ids:
            content = c.get("content")
            if isinstance(content, list):
                content = "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
            n = len((content or "").splitlines())
            if n > worst_n:
                worst_n, worst = n, (content or "")[:120].replace("\n", " ")
print(f"max Bash tool_result lines = {worst_n} (limit {limit}); starts: {worst!r}")
sys.exit(0 if worst_n <= limit else 1)
