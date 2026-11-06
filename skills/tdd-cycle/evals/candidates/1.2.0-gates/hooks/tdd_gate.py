#!/usr/bin/env python3
"""tdd-cycle 행동 검사 훅 (원칙 §2 보완 ②). 네 이벤트를 한 스크립트가 받는다.

UserPromptSubmit  모드 판정: 새 세션이면 상태 초기화(마커 .claude/tdd-mode 또는 TDD_MODE=1이면 project 모드),
                  요청에 TDD 언급이 있으면 prompt 모드, "TDD 없이" 류면 끔. 켜져 있으면 안내 한 줄을 주입한다.
PreToolUse        Edit·Write·MultiEdit·Bash가 소스 .py(테스트 제외)를 고치려 할 때, 순서대로:
                  unknown(마지막 pytest 결과를 못 읽음) → 거부 / no_red_pending(이 세션에서 쓴 테스트가 RED 없이 통과, --ack 전) → 거부 /
                  red → 이번 사이클 소스 증가가 한도를 넘으면 거부(--big-step 선언 시 허용) / refactor → 허용 /
                  red_missing → 스텁만 허용(AST) / none·green → 거부.
                  세션의 첫 거부에는 SKILL.md 본문을 덧붙인다(스킬을 호출하지 않았어도 절차가 전달되도록, 1.2.0).
                  Skill 도구로 tdd-cycle을 호출하면 본문을 덧붙이지 않는다.
PostToolUse       Bash로 pytest를 직접 돌린 출력을 읽어 상태를 갱신한다(red_check.py는 스스로 기록하므로 건너뜀).
                  출력을 읽지 못하면 unknown(1.2.0).
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
from tdd_state import (OFF_RE, ON_RE, SRC_GROWTH_LIMIT, apply_run, fresh, growth_if_applied, is_src, is_test, load,  # noqa: E402
                       marker_on, mode_on, nonstub_defs, parse_pytest, project_root, rel_to, runs_pytest, save, summary)

RED_CHECK = HERE.parent / "scripts" / "red_check.py"
SKILL_MD = HERE.parent / "SKILL.md"
HEREDOC = re.compile(r"cat\s*>>?\s*(\S+)\s*<<-?\s*['\"]?(\w+)['\"]?\n(.*?)\n\2", re.S)
BASH_WRITE = re.compile(r"(?:>>?\s*|tee\s+(?:-a\s+)?|sed\s+-i\S*\s.*?|cp\s+\S+\s+|mv\s+\S+\s+)(\S+\.py)\b")

NEED_RED = ("tdd-cycle: 소스를 고치기 전에 동작 이유로 실패하는 테스트가 있어야 한다(지금 상태: {state}). "
            "① 다음 동작 하나를 검사하는 테스트를 쓴다 ② `python3 {rc} <테스트>`로 RED (동작)을 확인한다 ③ 그다음 이 수정을 한다. "
            "동작을 바꾸지 않는 정리라면 먼저 `python3 {rc}`로 전체 스위트가 초록임을 확인한 뒤 `python3 {rc} --refactor`로 선언하고 고친다.")
STUB_ONLY = ("tdd-cycle: 지금은 RED (잘못된 이유) 상태라 없는 이름을 스텁으로만 만든다(시그니처, pass 또는 빈 값 반환). "
             "동작이 들어간 함수: {names}. 본문을 스텁으로 줄여 다시 쓰고, `python3 {rc} <테스트>`로 RED (동작)을 본 뒤 구현한다.")
SHELL_EDIT = ("tdd-cycle: RED (잘못된 이유) 상태에서는 셸로 소스를 고치지 않는다(내용을 검사할 수 없다). Write·Edit 도구로 스텁만 만든다.")
UNKNOWN_RUN = ("tdd-cycle: 마지막 pytest 실행의 결과를 읽지 못했다(출력이 파이프·리다이렉트로 잘렸거나 요약 줄이 없다). "
               "지금이 RED인지 GREEN인지 알 수 없어 소스 수정을 막는다. `python3 {rc} <테스트>`로 다시 돌려 확인한다. "
               "pytest 출력은 tail·grep·head로 자르지 않는다.")
NO_RED_ACK = ("tdd-cycle: RED 없음 — {names}가 실패한 적 없이 통과했다. 소스를 더 고치기 전에 둘 중 하나를 한다. "
              "(a) 기대값이 명세와 다르면 테스트를 고치고 `python3 {rc} <테스트>`로 RED (동작)을 본다. "
              "(b) 기대값이 맞으면 앞 사이클 구현이 이 동작을 미리 넣은 것이다. `python3 {rc} --ack {first}`로 기록하고 "
              "사이클 표에 'RED 없음'으로 적는다. 테스트를 지우거나 skip 표시해서 넘어가지 않는다.")
TOO_BIG = ("tdd-cycle: 이 수정으로 이번 사이클 소스가 +{n}줄이 된다(한도 {limit}). 테스트 하나가 요구한 것보다 많이 쓰고 있다. "
           "지금 실패 메시지를 없애는 최소 코드만 쓴다(상수 반환·분기 하나). 나머지 동작은 다음 테스트가 강제할 때 넣는다. "
           "한 걸음이 정말 커야 하면(예: 클래스 골격, 자료구조 하나) `python3 {rc} --big-step <이유>`로 선언한 뒤 고친다. 선언은 기록되고 요약에 나온다.")
CONTEXT = ("[tdd-cycle] TDD 모드({why}). 소스 .py(테스트 제외) 수정은 동작 이유로 실패하는 테스트가 먼저 있어야 허용된다(훅이 막는다). "
           "개발 절차는 tdd-cycle 스킬을 Skill 도구로 호출해 따른다. RED 확인: `python3 {rc} <테스트>`.")


def out(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False))


def skill_body() -> str:
    """SKILL.md 본문(frontmatter 제외). 스킬 디렉터리 자리표시자는 실제 경로로 바꾼다."""
    try:
        text = SKILL_MD.read_text()
    except Exception:  # noqa: BLE001
        return ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) == 3 else text
    return text.strip().replace("<이 스킬 디렉터리>", str(HERE.parent))


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


def deny(st: dict, root: Path, rel: str, reason: str) -> None:
    st["blocks"] += 1
    st["log"].append({"via": "block", "file": rel, "state": st["state"]})
    if not st.get("skill_seen"):
        # 1.2.0: 세션의 첫 거부에 절차 전체를 붙인다. 스킬이 호출됐는지와 무관하게 절차가 전달된다(실패 4).
        body = skill_body()
        if body:
            reason += "\n\n--- tdd-cycle 절차 (SKILL.md) ---\n" + body
        st["skill_seen"] = True
    save(root, st)
    out({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}})


def on_pre(data: dict, root: Path, st: dict | None) -> None:
    if not mode_on(st, root):
        return
    st = st or fresh(data.get("session_id"), "project")
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    if tool == "Skill":
        if "tdd-cycle" in json.dumps(inp, ensure_ascii=False) and not st.get("skill_seen"):
            st["skill_seen"] = True
            save(root, st)
        return
    state = st["state"]
    touched = False
    for rel, old, new in targets_of(tool, inp, root):
        if is_test(rel):
            if rel not in st["touched_tests"]:
                st["touched_tests"].append(rel)
                touched = True
            continue
        if not is_src(rel):
            continue
        if state == "unknown":
            return deny(st, root, rel, UNKNOWN_RUN.format(rc=RED_CHECK))
        pending = st.get("no_red_pending") or []
        if pending:
            return deny(st, root, rel, NO_RED_ACK.format(names=", ".join(pending[:4]), first=pending[0], rc=RED_CHECK))
        if state == "refactor":
            continue
        if state == "red":
            if new is None:
                st["shell_unseen"] += 1  # 내용을 볼 수 없는 셸 수정. 막지 않고 센다(요약에 나온다)
                st["log"].append({"via": "shell_unseen", "file": rel})
                touched = True
                continue
            if st.get("big_step"):
                continue
            grew = growth_if_applied(root, st.get("src_counts_at_red"), rel, new)
            if grew is not None and grew > SRC_GROWTH_LIMIT:
                return deny(st, root, rel, TOO_BIG.format(n=grew, limit=SRC_GROWTH_LIMIT, rc=RED_CHECK))
            continue
        if state == "red_missing":
            if new is None:
                return deny(st, root, rel, SHELL_EDIT)
            bad = nonstub_defs(old, new)
            if bad:
                return deny(st, root, rel, STUB_ONLY.format(names=", ".join(bad[:4]), rc=RED_CHECK))
            continue
        return deny(st, root, rel, NEED_RED.format(state=state, rc=RED_CHECK))
    if touched:
        save(root, st)


def on_post(data: dict, root: Path, st: dict | None) -> None:
    if not mode_on(st, root) or data.get("tool_name") != "Bash":
        return
    cmd = (data.get("tool_input") or {}).get("command", "")
    if "red_check" in cmd or "pytest" not in cmd:
        return
    resp = data.get("tool_response")
    text = resp if isinstance(resp, str) else ((resp or {}).get("stdout") or "") + "\n" + ((resp or {}).get("stderr") or "")
    parsed = parse_pytest(text)
    if parsed["result"] is None and not runs_pytest(cmd):
        return  # pytest를 언급만 한 명령(grep·heredoc 등)이고 읽을 결과도 없다 → 1.1.0처럼 무시
    st = st or fresh(data.get("session_id"), "project")
    notes = apply_run(st, parsed, "bash", root)
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
