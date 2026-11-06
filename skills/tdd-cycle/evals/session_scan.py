#!/usr/bin/env python3
"""실사용 세션 로그에서 실패 3·4의 발자국을 찾는다 (원칙 §6.4-7 실사용 확인, ⑥의 '실패를 다시 채집' 경로).

사용: python3 session_scan.py [--root ~/.claude/projects] [--since 30] [--include-eval] [--tsv out.tsv] [--md out.md]
  기본은 이 저장소(skill-study)와 하네스 임시 폴더(ge-run-*)의 세션을 제외한다(실사용 = 저장소·eval 폴더 밖).
  로그는 읽기만 한다. 출력은 세션마다 한 줄, 그리고 읽어 볼 후보 세션 목록.

세션마다 보는 것:
  tdd_req      사람 프롬프트에 TDD 언급(tdd_state.ON_RE)이 있었나
  mode_on      훅의 "[tdd-cycle] TDD 모드" 주입이 있었나(마커 또는 요청)
  skill_turn   tdd-cycle 스킬이 처음 호출된 도구 호출 순번(없으면 -). 실패 4 발자국: mode_on·tdd_req인데 '-'이거나 첫 소스 쓰기보다 늦음
  src/test     소스 .py 쓰기 수 / 테스트 파일 쓰기 수 (Write·Edit·MultiEdit·heredoc·sed)
  src_first    첫 소스 쓰기가 첫 테스트 쓰기보다 먼저인가 (실패 3 발자국: 구현 먼저)
  big_src      테스트 쓰기 전에 소스 .py를 40줄 넘게 한 번에 쓴 횟수 (실패 3: 통째로 구현)
  unarmed      직전 pytest가 실패가 아닌데(또는 실행 없는데) 소스를 쓴 횟수 (실패 2·3)
  pytest       pytest·red_check 실행 수
  denies       훅 거부 수 (is_error 결과에 hook·tdd-cycle 문구)
Stop 훅의 systemMessage(사이클 요약)는 세션 로그에 남지 않아 읽지 않는다. 모드 주입은 attachment 이벤트의 rendered 안에 남는다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from tdd_state import ON_RE, is_src, is_test  # noqa: E402

HEREDOC = re.compile(r"cat\s*>>?\s*(\S+)\s*<<-?\s*['\"]?(\w+)['\"]?\n(.*?)\n\2", re.S)
BASH_WRITE = re.compile(r"(?:>>?\s*|tee\s+(?:-a\s+)?|sed\s+-i\S*\s.*?)(\S+\.py)\b")
PYTEST = re.compile(r"(?:^|[;&|(`\n])\s*(?:\w+=\S*\s+)*(?:python3?\s+-m\s+)?pytest\b|red_check\.py(?!\s+--(?:ack|big-step|status|refactor))")
EXCLUDE_DEFAULT = ("ge-run-", "skill-study")


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content if isinstance(x, dict) and x.get("type") == "text")
    return ""


def result_text(x: dict) -> str:
    c = x.get("content")
    return c if isinstance(c, str) else "\n".join(y.get("text", "") for y in (c or []) if isinstance(y, dict))


def scan(path: Path) -> dict | None:
    prompts, tools, results, hook_ctx = [], [], {}, 0
    cwd = ""; first_ts = None; version = ""
    for line in path.read_text(errors="replace").splitlines():
        if "[tdd-cycle] TDD 모드" in line:  # UserPromptSubmit 주입은 attachment.rendered 안에 system-reminder로 남는다
            hook_ctx += 1
        try:
            e = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        t = e.get("type")
        cwd = e.get("cwd") or cwd
        version = e.get("version") or version
        if first_ts is None and e.get("timestamp"):
            first_ts = e["timestamp"]
        m = e.get("message") or {}
        c = m.get("content")
        if t == "user":
            if e.get("turnOrigin") == "human" or (isinstance(c, str) and not e.get("isMeta") and not e.get("toolUseResult")):
                txt = text_of(c)
                if txt and not txt.startswith("<") and "tool_result" not in str(c)[:40]:
                    prompts.append(txt)
            if isinstance(c, list):
                for x in c:
                    if isinstance(x, dict) and x.get("type") == "tool_result":
                        results[x.get("tool_use_id")] = (result_text(x), bool(x.get("is_error")))
        elif t == "assistant" and isinstance(c, list):
            for x in c:
                if isinstance(x, dict) and x.get("type") == "tool_use":
                    tools.append((x.get("id"), x.get("name"), x.get("input") or {}))
    if not tools and not prompts:
        return None
    # 도구 호출 순서대로 발자국을 복원한다
    skill_turn = None; src_w = test_w = big_src = unarmed = pytests = denies = 0
    first_src = first_test = None; armed = False
    for i, (tid, name, inp) in enumerate(tools, 1):
        out, err = results.get(tid, ("", False))
        if err and ("tdd-cycle" in out or "hook" in out.lower()):
            denies += 1
            continue  # 거부된 호출은 파일을 쓰지 않았다
        if name == "Skill" and "tdd-cycle" in json.dumps(inp, ensure_ascii=False):
            skill_turn = skill_turn or i
        writes: list[tuple[str, int]] = []
        if name in ("Write", "Edit", "MultiEdit"):
            p = inp.get("file_path", "")
            n = len([ln for ln in (inp.get("content") or "").splitlines() if ln.strip()]) if name == "Write" else 0
            writes.append((p, n))
        elif name == "Bash":
            cmd = inp.get("command", "")
            for mm in HEREDOC.finditer(cmd):
                writes.append((mm.group(1).strip("'\""), len([ln for ln in mm.group(3).splitlines() if ln.strip()])))
            for mm in BASH_WRITE.finditer(HEREDOC.sub("", cmd)):
                writes.append((mm.group(1), 0))
            if PYTEST.search(HEREDOC.sub("", cmd)):
                pytests += 1
                armed = bool(re.search(r"\d+ failed|\d+ errors?|FAILED|ERROR|RED \(", out)) and not re.search(r"^GREEN", out, re.M)
        for p, n in writes:
            rel = p.lstrip("./")
            if is_test(rel):
                test_w += 1
                first_test = first_test or i
            elif is_src(rel):
                src_w += 1
                first_src = first_src or i
                if first_test is None and n > 40:
                    big_src += 1
                if not armed:
                    unarmed += 1
    if src_w == 0:
        return None  # 개발이 없는 세션은 대상이 아니다
    tdd_req = any(ON_RE.search(p) for p in prompts)
    mode_on = hook_ctx > 0
    f4 = (tdd_req or mode_on) and (skill_turn is None or (first_src is not None and skill_turn > first_src))
    f3 = bool(first_src is not None and (first_test is None or first_src < first_test)) or big_src > 0 or (unarmed >= 3)
    return {
        "date": (first_ts or "")[:10], "project": Path(cwd).name or path.parent.name, "session": path.stem[:8],
        "prompt": (prompts[0] if prompts else "")[:60].replace("\n", " "),
        "tdd_req": tdd_req, "mode_on": mode_on, "skill_turn": skill_turn if skill_turn is not None else "-",
        "src": src_w, "test": test_w, "src_first": first_src is not None and (first_test is None or first_src < first_test),
        "big_src": big_src, "unarmed": unarmed, "pytest": pytests, "denies": denies,
        "F3": f3, "F4": f4, "file": str(path), "version": version,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--since", type=int, default=30, help="최근 N일")
    ap.add_argument("--include-eval", action="store_true", help="ge-run-*·skill-study 세션도 포함(스캐너 자체 점검용)")
    ap.add_argument("--tsv"); ap.add_argument("--md")
    a = ap.parse_args()
    cutoff = time.time() - a.since * 86400
    rows = []
    for f in sorted(Path(a.root).glob("*/*.jsonl")):
        if f.stat().st_mtime < cutoff:
            continue
        if not a.include_eval and any(x in f.parent.name for x in EXCLUDE_DEFAULT):
            continue
        try:
            r = scan(f)
        except Exception as e:  # noqa: BLE001
            print(f"skip {f.name}: {e}", file=sys.stderr); continue
        if r:
            rows.append(r)
    cols = ["date", "project", "session", "tdd_req", "mode_on", "skill_turn", "src", "test", "src_first", "big_src", "unarmed",
            "pytest", "denies", "F3", "F4", "prompt"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    n = len(rows)
    summary = [f"개발 세션(소스 .py 쓰기 있음) {n}개 (최근 {a.since}일, 제외: {'없음' if a.include_eval else ', '.join(EXCLUDE_DEFAULT)})",
               f"- TDD 요청 또는 모드 켜짐: {sum(r['tdd_req'] or r['mode_on'] for r in rows)} · 그중 스킬 미호출/늦은 호출(F4): {sum(r['F4'] for r in rows)}",
               f"- 구현 먼저·통째 구현·RED 없는 쓰기 3회+(F3): {sum(r['F3'] for r in rows)} · TDD 언급 없이 개발만 한 세션(마커가 필요한 자리): {sum(not r['tdd_req'] and not r['mode_on'] for r in rows)}",
               "", "읽어 볼 후보(F3·F4가 켜진 세션, 파일 경로):"]
    for r in sorted((r for r in rows if r["F3"] or r["F4"]), key=lambda r: (-(r["F3"] + r["F4"]), -r["src"]))[:15]:
        summary.append(f"- {r['date']} {r['project']} {'F3' if r['F3'] else '  '} {'F4' if r['F4'] else '  '} src={r['src']} test={r['test']} unarmed={r['unarmed']} → {r['file']}")
    text = "\n".join(summary) + "\n\n" + "\n".join(lines) + "\n"
    print(text)
    if a.md:
        Path(a.md).write_text(text)
    if a.tsv:
        Path(a.tsv).write_text("\t".join(cols + ["file"]) + "\n" + "\n".join("\t".join(str(r[c]) for c in cols + ["file"]) for r in rows) + "\n")


if __name__ == "__main__":
    main()
