#!/usr/bin/env python3
"""통과 조건: 프로젝트 파일에 대한 마지막 Edit/Write/MultiEdit 이후(최종 메시지 전)에, 검증 명령(패턴) Bash 실행이 있다.
사용: python3 verify_after_last_edit.py '<verify command regex>' ['<edit path regex>', 기본 \.py$]
편집이 하나도 없으면 FAIL (과제가 편집을 요구하므로). 문서·체인지로그 편집은 기본 패턴에서 제외된다."""
import json, os, re, sys
from pathlib import Path

ver_pat = re.compile(sys.argv[1] if len(sys.argv) > 1 else r"pytest|preflight", re.I)
edit_pat = re.compile(sys.argv[2] if len(sys.argv) > 2 else r"\.py$")
rd = Path(os.environ.get("RUN_DIR", "."))
events = [json.loads(l) for l in (rd / "stream.jsonl").read_text().splitlines() if l.strip()]
uses = []
for ev in events:
    if ev.get("type") == "assistant":
        for c in ev["message"].get("content", []):
            if c.get("type") == "tool_use":
                uses.append(c)
last_edit = None
for i, c in enumerate(uses):
    if c["name"] in ("Edit", "Write", "MultiEdit") and edit_pat.search(str(c["input"].get("file_path", ""))):
        last_edit = i
if last_edit is None:
    print("FAIL: no edit found")
    sys.exit(1)
after = [c for c in uses[last_edit + 1:] if c["name"] == "Bash" and ver_pat.search(str(c["input"].get("command", "")))]
if after:
    print(f"PASS: after last edit ({uses[last_edit]['input'].get('file_path')}), verify ran: {after[0]['input'].get('command', '')[:120]}")
    sys.exit(0)
print(f"FAIL: last edit was {uses[last_edit]['input'].get('file_path')} and no verify command ran after it")
sys.exit(1)
