#!/usr/bin/env python3
"""tdd-cycle 행동 검사 훅 (원칙 §2 보완 ②). 네 이벤트를 한 스크립트가 받는다.

UserPromptSubmit  모드 판정: 새 세션이면 상태 초기화(마커 .claude/tdd-mode 또는 TDD_MODE=1이면 project 모드),
                  요청에 TDD 언급이 있으면 prompt 모드, "TDD 없이" 류면 끔. 켜져 있으면 안내 한 줄을 주입한다.
PreToolUse        Edit·Write·MultiEdit·Bash가 소스 .py(테스트 제외)를 고치려 할 때:
                  red(동작 RED)·refactor → 허용 / red_missing → 스텁만 허용(AST) / none·green → 거부.
PostToolUse       Bash로 pytest를 직접 돌린 출력을 읽어 상태를 갱신한다(red_check.py는 스스로 기록하므로 건너뜀).
Stop              이 세션의 사이클 요약을 systemMessage로 보인다. 막지 않는다.
끄기: TDD_MODE=0. 디버그: TDD_GATE_DEBUG=<파일>에 입력을 덧붙인다.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from tdd_state import (OFF_RE, ON_RE, apply_run, fresh, is_src, load, marker_on, mode_on, nonstub_defs,  # noqa: E402
                       parse_pytest, project_root, rel_to, save, summary)

RED_CHECK = HERE.parent / "scripts" / "red_check.py"
HEREDOC = re.compile(r"cat\s*>>?\s*(\S+)\s*<<-?\s*['\"]?(\w+)['\"]?\n(.*?)\n\2", re.S)
BASH_WRITE = re.compile(r"(?:>>?\s*|tee\s+(?:-a\s+)?|sed\s+-i\S*\s.*?|cp\s+\S+\s+|mv\s+\S+\s+)(\S+\.py)\b")

NEED_RED = ("tdd-cycle: 소스를 고치기 전에 동작 이유로 실패하는 테스트가 있어야 한다(지금 상태: {state}). "
            "① 다음 동작 하나를 검사하는 테스트를 쓴다 ② `python3 {rc} <테스트>`로 RED (동작)을 확인한다 ③ 그다음 이 수정을 한다. "
            "동작을 바꾸지 않는 정리라면 먼저 `python3 {rc}`로 전체 스위트가 초록임을 확인한 뒤 `python3 {rc} --refactor`로 선언하고 고친다. "
            "절차 전체는 tdd-cycle 스킬(Skill 도구로 호출)에 있다.")
STUB_ONLY = ("tdd-cycle: 지금은 RED (잘못된 이유) 상태라 없는 이름을 스텁으로만 만든다(시그니처, pass 또는 빈 값 반환). "
             "동작이 들어간 함수: {names}. 본문을 스텁으로 줄여 다시 쓰고, `python3 {rc} <테스트>`로 RED (동작)을 본 뒤 구현한다.")
SHELL_EDIT = ("tdd-cycle: RED (잘못된 이유) 상태에서는 셸로 소스를 고치지 않는다(내용을 검사할 수 없다). Write·Edit 도구로 스텁만 만든다.")
CONTEXT = ("[tdd-cycle] TDD 모드({why}). 소스 .py(테스트 제외) 수정은 동작 이유로 실패하는 테스트가 먼저 있어야 허용된다(훅이 막는다). "
           "개발 절차는 tdd-cycle 스킬을 Skill 도구로 호출해 따른다. RED 확인: `python3 {rc} <테스트>`.")


def out(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False))


def on_prompt(data: dict, root: Path, st: dict | None) -> None:
    sid = data.get("session_id")
    if st is None or st.get("session_id") != sid:
        st = fresh(sid, "project" if marker_on(root) else "off")
    prompt = str(data.get("prompt") or "")
    if OFF_RE.search(prompt):
        st["mode"] = "off_user"
    elif ON_RE.search(prompt) and st["mode"] != "project":
        st["mode"] = "prompt"
    if marker_on(root) is False:
        st["mode"] = "off"
    save(root, st)
    if mode_on(st, root):
        why = "프로젝트 설정" if st["mode"] == "project" else "요청에 TDD 언급"
        out({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": CONTEXT.format(why=why, rc=RED_CHECK)}})


def targets_of(tool: str, inp: dict, root: Path) -> list[tuple[str, str | None, str | None]]:
    """(상대 경로, 기존 내용, 새 내용). 새 내용을 알 수 없으면 None."""
    def disk(rel: str) -> str | None:
        p = root / rel
        return p.read_text() if p.exists() else None

    res = []
    if tool in ("Write", "Edit", "MultiEdit"):
        rel = rel_to(root, inp.get("file_path", ""))
        if not rel:
            return []
        old = disk(rel)
        if tool == "Write":
            new = inp.get("content", "")
        else:
            new = old or ""
            for e in (inp.get("edits") or [inp]):
                o, n = e.get("old_string", ""), e.get("new_string", "")
                new = new.replace(o, n) if e.get("replace_all") else new.replace(o, n, 1)
        res.append((rel, old, new))
    elif tool == "Bash":
        cmd = inp.get("command", "")
        for m in HEREDOC.finditer(cmd):
            rel = rel_to(root, m.group(1).strip("'\""))
            if rel:
                res.append((rel, disk(rel), m.group(3) + "\n"))
        for m in BASH_WRITE.finditer(HEREDOC.sub("", cmd)):
            rel = rel_to(root, m.group(1).strip("'\""))
            if rel:
                res.append((rel, disk(rel), None))
    return res


def on_pre(data: dict, root: Path, st: dict | None) -> None:
    if not mode_on(st, root):
        return
    st = st or fresh(data.get("session_id"), "project")
    state = st["state"]
    for rel, old, new in targets_of(data.get("tool_name", ""), data.get("tool_input") or {}, root):
        if not is_src(rel):
            continue
        reason = None
        if state in ("red", "refactor"):
            continue
        if state == "red_missing":
            if new is None:
                reason = SHELL_EDIT
            else:
                bad = nonstub_defs(old, new)
                if bad:
                    reason = STUB_ONLY.format(names=", ".join(bad[:4]), rc=RED_CHECK)
        else:
            reason = NEED_RED.format(state=state, rc=RED_CHECK)
        if reason:
            st["blocks"] += 1
            st["log"].append({"via": "block", "file": rel, "state": state})
            save(root, st)
            out({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                        "permissionDecisionReason": reason}})
            return


def on_post(data: dict, root: Path, st: dict | None) -> None:
    if not mode_on(st, root) or data.get("tool_name") != "Bash":
        return
    cmd = (data.get("tool_input") or {}).get("command", "")
    if "red_check" in cmd or "pytest" not in cmd:
        return
    resp = data.get("tool_response")
    text = resp if isinstance(resp, str) else ((resp or {}).get("stdout") or "") + "\n" + ((resp or {}).get("stderr") or "")
    st = st or fresh(data.get("session_id"), "project")
    notes = apply_run(st, parse_pytest(text), "bash", root)
    save(root, st)
    if notes:
        out({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "tdd-cycle: " + " ".join(notes)}})


def on_stop(data: dict, root: Path, st: dict | None) -> None:
    if st and mode_on(st, root) and (st["runs"] or st["blocks"]):
        out({"systemMessage": summary(st)})


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return
    dbg = os.environ.get("TDD_GATE_DEBUG")
    if dbg:
        with open(dbg, "a") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    root = project_root(data.get("cwd"))
    st = load(root)
    ev = data.get("hook_event_name")
    try:
        {"UserPromptSubmit": on_prompt, "PreToolUse": on_pre, "PostToolUse": on_post, "Stop": on_stop}.get(ev, lambda *_: None)(data, root, st)
    except Exception as e:  # noqa: BLE001  훅 오류가 작업을 깨면 안 된다
        print(f"tdd_gate: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
