#!/usr/bin/env python3
"""채점기: 각 run 디렉터리에 grading.json을 쓴다 (skill-creator 뷰어 호환 필드: text/passed/evidence).

두 종류의 assertion을 지원한다.
- expectations: 자연어. LLM grader(claude -p, 구조화 출력)가 트랜스크립트·outputs를 읽고 판정. 설정(with/without)은 알려주지 않는다.
- checks: 결정적. {"text", "type": "regex_transcript"|"regex_final"|"regex_outputs"|"script", "pattern"|"cmd", "negate"?}
  script는 RUN_DIR 환경변수를 받고 exit 0이면 통과.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import clean_env  # noqa: E402

SCHEMA = {
    "type": "object",
    "properties": {
        "expectations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "passed": {"type": "boolean"}, "evidence": {"type": "string"}},
                "required": ["text", "passed", "evidence"],
            },
        }
    },
    "required": ["expectations"],
}

TEXT_EXT = {".py", ".md", ".txt", ".json", ".js", ".ts", ".sh", ".toml", ".cfg", ".ini", ".yaml", ".yml", ".log", ".csv"}


def outputs_digest(out_dir: Path, limit_per_file: int = 4000, total_limit: int = 40000) -> str:
    parts, used = [], 0
    for p in sorted(out_dir.rglob("*")):
        if not p.is_file() or p.suffix not in TEXT_EXT:
            continue
        try:
            txt = p.read_text(errors="replace")
        except Exception:  # noqa: BLE001
            continue
        chunk = txt[:limit_per_file] + ("\n…[truncated]" if len(txt) > limit_per_file else "")
        used += len(chunk)
        if used > total_limit:
            parts.append("…[outputs truncated]")
            break
        parts.append(f"--- {p.relative_to(out_dir)} ---\n{chunk}")
    return "\n".join(parts) or "(no text outputs)"


def llm_grade(run_dir: Path, expectations: list[str], grader_model: str, timeout: int) -> list[dict]:
    transcript = (run_dir / "transcript.md").read_text(errors="replace").replace("\x00", "")  # 널 바이트는 claude -p 인자로 못 넘긴다 (2026-10-23 라운드 2에서 채점 실패 2건)
    if len(transcript) > 60000:
        transcript = transcript[:30000] + "\n…[middle truncated]…\n" + transcript[-30000:]
    outputs = (outputs_digest(run_dir / "outputs") if (run_dir / "outputs").exists() else "(none)").replace("\x00", "")
    prompt = f"""You are a strict grader. For each expectation decide PASS or FAIL using only the evidence below.
Rules: the burden of proof is on PASS. Quote specific evidence (step numbers, commands, file lines). Superficial or coincidental compliance is FAIL.
Do not infer what the agent "probably" did; if the transcript does not show it, it did not happen.

# Expectations
{json.dumps(expectations, ensure_ascii=False, indent=1)}

# Transcript
{transcript}

# Output files after the run
{outputs}
"""
    cmd = ["claude", "-p", prompt, "--model", grader_model, "--output-format", "json",
           "--json-schema", json.dumps(SCHEMA), "--no-session-persistence", "--setting-sources", "",
           "--strict-mcp-config", "--max-turns", "1", "--disallowedTools", "Bash,Read,Edit,Write,Grep,Glob,Task,Skill"]
    prompt += "\nYou have no tools in this session; do not attempt tool calls. Answer directly with the JSON object.\n"
    cmd[2] = prompt
    last_err = ""
    for attempt in range(3):  # grader가 도구를 부르려 하면 structured_output이 비는 경우가 있어 재시도
        proc = subprocess.run(cmd, env=clean_env(), capture_output=True, text=True, timeout=timeout)
        try:
            res = json.loads(proc.stdout)
            data = res.get("structured_output") or json.loads(res.get("result", "{}"))
            graded = data["expectations"]
            break
        except Exception as e:  # noqa: BLE001
            last_err = f"GRADER ERROR (attempt {attempt+1}): {e}; stop_reason={proc.stdout[:200]} stderr={proc.stderr[:200]}"
    else:
        return [{"text": t, "passed": False, "evidence": last_err} for t in expectations]
    by_text = {g["text"]: g for g in graded}
    out = []
    for i, t in enumerate(expectations):
        g = by_text.get(t) or (graded[i] if i < len(graded) else None)
        out.append({"text": t, "passed": bool(g and g.get("passed")), "evidence": (g or {}).get("evidence", "grader returned nothing for this item")})
    return out


def run_check(run_dir: Path, chk: dict) -> dict:
    typ = chk["type"]
    passed, evidence = False, ""
    try:
        if typ in ("regex_transcript", "regex_final", "regex_outputs"):
            if typ == "regex_transcript":
                hay = (run_dir / "transcript.md").read_text(errors="replace")
            elif typ == "regex_final":
                hay = json.loads((run_dir / "run.json").read_text()).get("final_text", "")
            else:
                hay = outputs_digest(run_dir / "outputs", 10**6, 10**7)
            m = re.search(chk["pattern"], hay, re.S | re.I | re.M)
            passed = bool(m)
            evidence = f"match: {m.group(0)[:200]!r}" if m else f"no match for /{chk['pattern']}/"
        elif typ == "script":
            proc = subprocess.run(chk["cmd"], shell=True, cwd=run_dir, env={**os.environ, "RUN_DIR": str(run_dir), "GATE_EVAL_CHECKS": str(Path(__file__).parent / "checks"), "GATE_EVAL_SKILL": os.environ.get("GATE_EVAL_SKILL", "")},
                                  capture_output=True, text=True, timeout=120)
            passed = proc.returncode == 0
            evidence = (proc.stdout + proc.stderr).strip()[-600:] or f"exit {proc.returncode}"
        else:
            evidence = f"unknown check type {typ}"
    except Exception as e:  # noqa: BLE001
        evidence = f"CHECK ERROR: {e}"
    if chk.get("negate"):
        passed = not passed
    return {"text": chk["text"], "passed": passed, "evidence": evidence}


def grade_run(run_dir: Path, ev: dict, grader_model: str, timeout: int, force: bool) -> dict:
    gpath = run_dir / "grading.json"
    if gpath.exists() and not force:
        prev = json.loads(gpath.read_text())
        if not any("GRADER ERROR" in e.get("evidence", "") for e in prev.get("expectations", [])):
            return prev
    if not (run_dir / "run.json").exists():
        return {}
    items = [run_check(run_dir, c) for c in ev.get("checks", []) or []]
    exps = ev.get("expectations", []) or []
    if exps:
        items += llm_grade(run_dir, exps, grader_model, timeout)
    run = json.loads((run_dir / "run.json").read_text())
    passed = sum(1 for i in items if i["passed"])
    grading = {
        "expectations": items,
        "summary": {"passed": passed, "failed": len(items) - passed, "total": len(items), "pass_rate": (passed / len(items)) if items else 0.0},
        "execution_metrics": {"total_context_tokens": run.get("total_context_tokens"), "output_tokens": run.get("output_tokens"),
                              "num_turns": run.get("num_turns"), "skill_invoked": run.get("skill_invoked"), "cost_usd": run.get("cost_usd")},
        "timing": {"executor_duration_seconds": (run.get("duration_ms") or 0) / 1000},
    }
    gpath.write_text(json.dumps(grading, ensure_ascii=False, indent=1))
    return grading


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--grader", default="sonnet")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default="", help="eval id 콤마 목록만 채점")
    a = ap.parse_args()
    skill_dir = Path(a.skill).resolve()
    os.environ["GATE_EVAL_SKILL"] = str(skill_dir)
    evals = {e["id"]: e for e in json.loads((skill_dir / "evals" / "evals.json").read_text())["evals"]}
    qdir = (Path(a.out).resolve()) / "quality"  # script 검사는 cwd=run_dir이므로 절대 경로 필수
    run_dirs = sorted(p.parent for p in qdir.rglob("run.json"))
    if a.only:
        keep = {int(x) for x in a.only.split(",")}
        run_dirs = [rd for rd in run_dirs if json.loads((rd / "run.json").read_text())["eval_id"] in keep]
    print(f"[grade] {len(run_dirs)} runs, grader={a.grader}", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {}
        for rd in run_dirs:
            run = json.loads((rd / "run.json").read_text())
            futs[ex.submit(grade_run, rd, evals[run["eval_id"]], a.grader, a.timeout, a.force)] = rd
        n = 0
        for fut in as_completed(futs):
            n += 1
            rd = futs[fut]
            try:
                g = fut.result()
                print(f"[grade] {n}/{len(run_dirs)} {rd.relative_to(qdir)}: {g.get('summary', {}).get('passed')}/{g.get('summary', {}).get('total')}", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                print(f"[grade] {n}/{len(run_dirs)} FAILED {rd}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
