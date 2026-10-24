#!/usr/bin/env python3
"""Stop 훅: 이번 요청에서 코드를 고쳤는데 그 뒤로 preflight가 돌지 않았으면, 끝내기 전에 훅이 직접 돌린다.

- 끼어드는 조건: 마지막 사용자 요청 이후 소스 파일 편집(Edit/Write/MultiEdit/NotebookEdit, 또는 Bash 쓰기 명령)이 있고,
  마지막 편집 뒤에 preflight 실행이 없다. pytest만 돌린 경우는 검사로 치지 않는다(mypy 누락이 실제 실패 양상이었다).
- preflight exit 0 → 막지 않고 systemMessage로 결과 한 줄을 사용자에게 보여 준다.
- exit 1 → 한 번만 막고 실패 요약을 reason으로 돌려준다. stop_hook_active(이미 한 번 막음)면 다시 막지 않고 결과만 보여 준다.
- exit 2(테스트 0개)·시간 초과·도구 없음 → 막지 않고 "검증 못 함"만 보여 준다.
- 끄기: 환경변수 VERIFY_ON_STOP=0. 입력이 깨졌거나 예외가 나면 아무것도 하지 않는다(훅이 작업을 깨뜨리면 안 된다).
근거: docs/study/gate-eval-round-2.md ① 재측정(모델은 과제 시작 때만 스킬을 고르므로 끝-시점 검사는 결정적 장치로).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_EXT = r"\.(?:py|pyi|ts|tsx|js|jsx|mjs|cjs|go|rs|java|kt|rb)"
SRC_PATH = re.compile(SRC_EXT + r"$")
SRC_TOKEN = re.compile(r"[^\s'\"<>|;&]+" + SRC_EXT + r"\b")
# Bash 쓰기: 소스 경로로의 리다이렉트·tee·cp·mv, 또는 제자리 편집 명령과 소스 경로가 함께 있을 때
BASH_WRITE = re.compile(r"(?:>>?|\btee\s+(?:-a\s+)?|\bcp\s+(?:-\w+\s+)*\S+\s+|\bmv\s+(?:-\w+\s+)*\S+\s+)\s*[^\s'\"<>|;&]+" + SRC_EXT + r"\b")
BASH_INPLACE = re.compile(r"\bsed\s+(?:-\w+\s+)*-[a-zA-Z]*i|\bperl\s+(?:-\w+\s+)*-[a-zA-Z]*i|\bpython3?\s+-\s*<<|\bpython3?\s+-c\b.*\bopen\("
                          r"|\bgit\s+apply\b|\bpatch\b")
STEP_TIMEOUT = 60
TOTAL_TIMEOUT = 200

BLOCK_REASON = (
    "verify-on-stop: 마지막 편집 뒤 CI 검사(preflight: 연관 테스트·린트·타입 검사)가 실패했습니다.\n{summary}\n"
    "이번 변경 때문이면 고친 뒤 끝내십시오. 이번 변경과 무관한 기존 실패이거나, 의도된 실패(먼저 쓴 실패 테스트, "
    "테스트와 스펙의 충돌 보고 등)이거나, 고칠 수 없으면 코드를 더 바꾸지 말고 그 사실을 그대로 보고하고 멈추십시오. "
    "테스트를 약화시켜 통과시키지 마십시오."
)


def entries(path: str) -> list[dict]:
    out = []
    try:
        for line in Path(path).read_text().splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        pass
    return out


def is_prompt(ev: dict) -> bool:
    """도구 결과나 훅 피드백이 아닌 진짜 사용자 요청인가."""
    if ev.get("type") != "user":
        return False
    content = (ev.get("message") or {}).get("content")
    if isinstance(content, str):
        return not content.startswith("Stop hook feedback")
    if isinstance(content, list):
        texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        has_result = any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content)
        return bool(texts) and not has_result and not texts[0].startswith("Stop hook feedback")
    return False


def tool_uses_since_prompt(evs: list[dict]) -> list[dict]:
    start = max((i for i, ev in enumerate(evs) if is_prompt(ev)), default=-1)
    uses = []
    for ev in evs[start + 1:]:
        if ev.get("type") != "assistant":
            continue
        for c in (ev.get("message") or {}).get("content", []) or []:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                uses.append(c)
    return uses


def edit_of(use: dict) -> tuple[bool, str | None]:
    """(소스 편집인가, 알 수 있으면 경로)."""
    name, inp = use.get("name"), use.get("input") or {}
    if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        p = str(inp.get("file_path") or inp.get("notebook_path") or "")
        return (bool(SRC_PATH.search(p)), p or None)
    if name == "Bash":
        cmd = str(inp.get("command") or "")
        m = BASH_WRITE.search(cmd)
        if m:
            tok = SRC_TOKEN.search(m.group(0))
            return True, tok.group(0) if tok else None
        if BASH_INPLACE.search(cmd) and SRC_TOKEN.search(cmd):
            return True, None  # 경로를 확정할 수 없다 → 전체 검사
    return False, None


def preflight_args(cwd: Path, paths: list[str | None]) -> list[str]:
    if (cwd / ".git").exists():
        return []  # git diff가 Bash 편집까지 잡는다
    if any(p is None for p in paths):
        return ["--all"]
    rel = []
    for p in paths:
        try:
            rel.append(str(Path(p).resolve().relative_to(cwd.resolve())))
        except ValueError:
            rel.append(str(p))
    return ["--files", *sorted(set(rel))]


def summarize(report: dict) -> str:
    parts = []
    for k in ("pytest", "js_tests"):
        pt = report.get(k)
        if not pt:
            continue
        if pt.get("status") == "skipped":
            parts.append(f"{k} 없음")
            continue
        name = pt.get("runner") or k
        parts.append(f"{name} {pt.get('passed', 0)} passed" + (f", {pt['failed']} failed" if pt.get("failed") else "")
                     + (f", {pt['errors']} errors" if pt.get("errors") else ""))
    for k in ("ruff", "mypy", "tsc", "eslint"):
        v = report.get(k)
        if not v:
            continue
        if v.get("status") == "pass":
            parts.append(f"{k} ok")
        elif v.get("status") == "fail":
            parts.append(f"{k} {v.get('count')} errors")
        elif v.get("status") == "skipped":
            parts.append(f"{k} 없음")
        elif v.get("status") == "error":
            parts.append(f"{k} 실행 오류(검사 못 함)")
    return ", ".join(parts) or "검사 없음"


def details(report: dict) -> str:
    lines = []
    for k in ("pytest", "js_tests"):
        pt = report.get(k) or {}
        for f in pt.get("first_failures") or []:
            lines.append(f"- FAILED {f}")
        if pt.get("collection_error") or (pt.get("status") == "fail" and not pt.get("first_failures")):
            lines += [f"- {t}" for t in pt.get("tail") or []]
    for k in ("ruff", "mypy", "tsc", "eslint"):
        for f in (report.get(k) or {}).get("first") or []:
            lines.append(f"- {k}: {f}")
    return "\n".join(lines[:12])


def run_preflight(cwd: Path, args: list[str]) -> tuple[int | None, dict]:
    cmd = [sys.executable, str(HERE / "preflight.py"), "--timeout", str(STEP_TIMEOUT), *args]
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TOTAL_TIMEOUT)
    except subprocess.TimeoutExpired:
        return None, {}
    report = {}
    for line in p.stdout.splitlines():
        if line.startswith('"'):
            try:
                report.update(json.loads("{" + line + "}"))
            except json.JSONDecodeError:
                continue
    return p.returncode, report


def main() -> None:
    if os.environ.get("VERIFY_ON_STOP") == "0":
        return
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return
    cwd = Path(data.get("cwd") or os.getcwd())
    uses = tool_uses_since_prompt(entries(str(data.get("transcript_path") or "")))
    last_edit, paths = None, []
    for i, u in enumerate(uses):
        is_edit, path = edit_of(u)
        if is_edit:
            last_edit = i
            paths.append(path)
    if last_edit is None:
        return
    if any(u.get("name") == "Bash" and "preflight" in str((u.get("input") or {}).get("command", "")) for u in uses[last_edit + 1:]):
        return
    code, report = run_preflight(cwd, preflight_args(cwd, paths))
    tag = "재검사 " if data.get("stop_hook_active") else ""
    if code is None:
        out = {"systemMessage": f"verify-on-stop: 검증 못 함 — preflight 시간 초과({TOTAL_TIMEOUT}s)"}
    elif code == 0:
        out = {"systemMessage": f"verify-on-stop: {tag}preflight → exit 0 ({summarize(report)})"}
    elif code == 2:
        out = {"systemMessage": f"verify-on-stop: 검증 못 함 — 테스트가 0개 실행됨 (exit 2; {summarize(report)})"}
    elif data.get("stop_hook_active"):
        out = {"systemMessage": f"verify-on-stop: {tag}preflight → exit {code} ({summarize(report)}) — 실패가 남아 있음"}
    else:
        out = {"decision": "block", "reason": BLOCK_REASON.format(summary=f"결과: exit {code} ({summarize(report)})\n{details(report)}")}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001  훅 오류로 세션을 막지 않는다
        pass
