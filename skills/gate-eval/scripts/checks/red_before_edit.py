#!/usr/bin/env python3
"""통과 조건: 소스 파일(패턴)에 대한 첫 Edit/Write/MultiEdit 이전에, 실패로 끝난 Bash 실행이 있다 (루프 우선).
사용: python3 red_before_edit.py '<source path regex>'   예: 'slugger/'
실패 판정: tool_result.is_error 또는 결과 텍스트에 FAILED|Error|Traceback|AssertionError|exit code [1-9]."""
import json, os, re, sys
from pathlib import Path

src_pat = re.compile(sys.argv[1] if len(sys.argv) > 1 else r"src/")
fail_pat = re.compile(r"FAILED|Error|Traceback|AssertionError|exit code [1-9]|failed", re.I)
rd = Path(os.environ.get("RUN_DIR", "."))
events = [json.loads(l) for l in (rd / "stream.jsonl").read_text().splitlines() if l.strip()]
tool_by_id = {}
order = []  # (kind, id, detail)
for ev in events:
    if ev.get("type") == "assistant":
        for c in ev["message"].get("content", []):
            if c.get("type") == "tool_use":
                tool_by_id[c["id"]] = c
                order.append(("use", c["id"]))
    elif ev.get("type") == "user":
        for c in ev["message"].get("content", []):
            if isinstance(c, dict) and c.get("type") == "tool_result":
                order.append(("result", c["tool_use_id"], c))
red_seen = None
for item in order:
    if item[0] == "use":
        c = tool_by_id[item[1]]
        if c["name"] in ("Edit", "Write", "MultiEdit") and src_pat.search(str(c["input"].get("file_path", ""))):
            if red_seen:
                print(f"PASS: failing command before first source edit: {red_seen}")
                sys.exit(0)
            print(f"FAIL: first source edit ({c['input'].get('file_path')}) happened before any failing command")
            sys.exit(1)
    else:
        c = item[2]
        use = tool_by_id.get(item[1])
        if not use or use["name"] != "Bash":
            continue
        content = c.get("content")
        if isinstance(content, list):
            content = "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
        if c.get("is_error") or fail_pat.search(content or ""):
            red_seen = red_seen or use["input"].get("command", "")[:120]
print("FAIL: no source edit found" if not red_seen else "PASS (no source edit, but a failing command was run)")
sys.exit(1 if not red_seen else 0)
