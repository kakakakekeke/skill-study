#!/usr/bin/env python3
"""TDD 과정 검사: run의 stream.jsonl에서 파일 쓰기·pytest 실행 순서를 복원해 지표를 낸다.

사용:
  python3 tdd_trace.py --evals ../evals.json --results <out>/quality [--tsv out.tsv]
  RUN_DIR=<run> python3 tdd_trace.py --one <fixture 이름>   (run 하나, JSON 한 줄)

지표 (run마다):
  test_first      첫 테스트 파일 쓰기가 첫 소스 쓰기보다 먼저인가
  cycles          새 테스트가 추가된 뒤 소스를 쓴 횟수(= RED→GREEN 사이클 근사)
  max_burst       한 사이클에서 소스 쓰기 전에 추가된 테스트 함수 수의 최댓값
  tail            마지막 소스 쓰기 뒤에 추가된 테스트 함수 수(test-after 몫)
  red_behavior    최종 테스트 함수 중, 어떤 pytest 출력에서 동작 이유(assertion 등)로 FAILED가 찍힌 비율
  red_runs_missing_only  실패가 모두 import·이름·속성 누락이었던 pytest 실행 수
  coverage        최종 테스트로 실행된 소스 줄 비율(표준 라이브러리 settrace)
  accept          숨은 명세 수용 테스트 통과 수/전체
  claims_tdd      최종 메시지가 TDD·RED·GREEN을 주장하는가
  strict          test_first ∧ red_behavior ≥ 0.8 ∧ cycles ≥ 3 ∧ max_burst ≤ 3 ∧ coverage ≥ 0.9 (측정 전 고정)
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPT = {"feed-base": "feed_accept.py", "duration-base": "duration_accept.py", "store-base": "store_accept.py"}
CLAIM = re.compile(r"\bTDD\b|\bRED\b|\bGREEN\b|레드|그린|실패하는 테스트|테스트를 먼저|테스트 먼저|test-first", re.I)
MISSING = re.compile(r"ModuleNotFoundError|ImportError|cannot import name|NameError|has no attribute|"
                     r"not callable|unexpected keyword argument|positional argument|takes no arguments")
HEREDOC = re.compile(r"cat\s*>\s*(\S+)\s*<<-?\s*['\"]?(\w+)['\"]?\n(.*?)\n\2", re.S)
BASH_WRITE = re.compile(r"(?:>\s*|tee\s+|sed\s+-i\S*\s.*?|cp\s+\S+\s+|mv\s+\S+\s+)(\S+\.py)\b")


def rel(path: str) -> str:
    m = re.search(r"ge-run-[^/]+/(.*)$", path)
    return m.group(1) if m else path.lstrip("./")


def is_test(p: str) -> bool:
    name = p.rsplit("/", 1)[-1]
    return p.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"
                                  or p.startswith("tests/") or "/tests/" in p)


def is_src(p: str) -> bool:
    return p.endswith(".py") and not is_test(p)


def test_names(src: str) -> set[str]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set(re.findall(r"^\s*def (test_\w+)", src, re.M))
    out = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            out.add(node.name)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            out |= {f"{node.name}.{n.name}" for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")}
    return out


def count_tests(files: dict[str, str]) -> int:
    return sum(len(test_names(c)) for p, c in files.items() if is_test(p) and p.rsplit("/", 1)[-1] != "conftest.py")


def result_text(c: dict) -> str:
    body = c.get("content")
    if isinstance(body, list):
        body = "\n".join(x.get("text", "") for x in body if isinstance(x, dict))
    return body or ""


def parse_pytest(out: str) -> dict:
    """FAILED 테스트 이름과 이유 분류, 수집 오류 여부."""
    failed: dict[str, str] = {}
    for m in re.finditer(r"^FAILED\s+(\S+)(?:\s+-\s+(.*))?$", out, re.M):
        parts = m.group(1).split("::")
        name = re.sub(r"\[.*$", "", parts[-1])
        if len(parts) >= 3:
            name = f"{parts[-2]}.{name}"
        reason = m.group(2) or ""
        failed[name] = "missing" if MISSING.search(reason) else "stub" if "NotImplementedError" in reason else \
            "behavior" if reason else "unknown"
    for m in re.finditer(r"^\S+::(\S+?)(?:\[\S*\])?\s+FAILED\b", out, re.M):
        name = m.group(1).replace("::", ".")
        failed.setdefault(name, "unknown")
    if "RED (동작)" in out:  # 스킬의 red_check.py 출력: "  <nodeid> - <이유>"
        for m in re.finditer(r"^\s+(\S+?::\S+) - (.*)$", out, re.M):
            parts = m.group(1).split("::")
            name = re.sub(r"\[.*$", "", parts[-1])
            if len(parts) >= 3:
                name = f"{parts[-2]}.{name}"
            failed.setdefault(name, "missing" if MISSING.search(m.group(2)) else "behavior")
    collect_err = bool(re.search(r"ERROR collecting|errors? during collection|^ERROR\s+\S+\.py\s*$|RED \(잘못된 이유\)", out, re.M))
    return {"failed": failed, "collect_err": collect_err,
            "passed": int(m.group(1)) if (m := re.search(r"(\d+) passed", out)) else 0}


def load_events(run_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (run_dir / "stream.jsonl").read_text().splitlines() if line.strip()]


def timeline(events: list[dict], fixture_dir: Path) -> list[tuple]:
    """('write', rel, kind, n_tests) / ('pytest', parsed) 순서 목록."""
    files = {str(p.relative_to(fixture_dir)): p.read_text() for p in fixture_dir.rglob("*") if p.is_file()}
    results = {}
    for ev in events:
        if ev.get("type") == "user" and isinstance(ev.get("message", {}).get("content"), list):
            for c in ev["message"]["content"]:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    results[c.get("tool_use_id")] = result_text(c)
    tl, unknown_writes = [], 0

    def wrote(p: str) -> None:
        kind = "test" if is_test(p) else "src" if is_src(p) else "other"
        tl.append(("write", p, kind, count_tests(files)))

    for ev in events:
        if ev.get("type") != "assistant":
            continue
        for c in ev.get("message", {}).get("content", []):
            if c.get("type") != "tool_use":
                continue
            name, inp = c.get("name"), c.get("input") or {}
            if name == "Write":
                p = rel(inp.get("file_path", ""))
                files[p] = inp.get("content", "")
                wrote(p)
            elif name in ("Edit", "MultiEdit"):
                p = rel(inp.get("file_path", ""))
                edits = inp.get("edits") or [inp]
                if p in files:
                    for e in edits:
                        old, new = e.get("old_string", ""), e.get("new_string", "")
                        files[p] = files[p].replace(old, new) if e.get("replace_all") else files[p].replace(old, new, 1)
                else:
                    unknown_writes += 1
                wrote(p)
            elif name == "Bash":
                cmd = inp.get("command", "")
                for m in HEREDOC.finditer(cmd):
                    p = rel(m.group(1))
                    files[p] = m.group(3) + "\n"
                    wrote(p)
                rest = HEREDOC.sub("", cmd)
                for m in BASH_WRITE.finditer(rest):
                    unknown_writes += 1
                    p = rel(m.group(1))
                    files.setdefault(p, "")
                    wrote(p)
                if "pytest" in cmd or "red_check" in cmd:
                    tl.append(("pytest", parse_pytest(results.get(c.get("id"), ""))))
    tl.append(("unknown_writes", unknown_writes))
    return tl


COVER_RUNNER = r'''
import json, os, sys, threading
root = sys.argv[1]
sys.dont_write_bytecode = True
sys.path.insert(0, root)
def is_test(p):
    n = os.path.basename(p)
    r = os.path.relpath(p, root)
    return n.startswith("test_") or n.endswith("_test.py") or n == "conftest.py" or r.startswith("tests" + os.sep)
src = set()
for d, _, fs in os.walk(root):
    for f in fs:
        p = os.path.join(d, f)
        if f.endswith(".py") and not is_test(p):
            src.add(os.path.realpath(p))
hits = {p: set() for p in src}
def local(frame, event, arg):
    if event == "line":
        hits[frame.f_code.co_filename].add(frame.f_lineno)
    return local
def glob(frame, event, arg):
    f = frame.f_code.co_filename
    if f in hits:
        hits[f].add(frame.f_lineno)
        return local
    return None
import pytest
sys.settrace(glob); threading.settrace(glob)
code = pytest.main([root, "-q", "-p", "no:cacheprovider", "--rootdir", root])
sys.settrace(None)
def lines(co):
    out = {l for _, _, l in co.co_lines() if l}
    for k in co.co_consts:
        if hasattr(k, "co_lines"):
            out |= lines(k)
    return out
total = covered = 0
missing = {}
for p in sorted(src):
    try:
        ex = lines(compile(open(p).read(), p, "exec"))
    except SyntaxError:
        continue
    total += len(ex); covered += len(ex & hits[p])
    miss = sorted(ex - hits[p])
    if miss:
        missing[os.path.relpath(p, root)] = miss
print("@@COVER@@" + json.dumps({"exit": int(code), "total": total, "covered": covered, "missing": missing}))
'''


def clean_env(**extra: str) -> dict:
    """측정용 runlog 플러그인이 검사기 자신의 pytest 실행을 기록하지 않게 뺀다."""
    env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_PLUGINS", "RUNLOG_DIR", "PYTHONPATH")}
    return {**env, "PYTHONDONTWRITEBYTECODE": "1", **extra}


def coverage(outputs: Path) -> dict:
    with tempfile.TemporaryDirectory() as td:
        runner = Path(td) / "cover_runner.py"
        runner.write_text(COVER_RUNNER)
        env = clean_env()
        p = subprocess.run([sys.executable, str(runner), str(outputs.resolve())], cwd=outputs, env=env,
                           capture_output=True, text=True, timeout=300)
    m = re.search(r"@@COVER@@(.*)", p.stdout)
    if not m:
        return {"exit": -1, "total": 0, "covered": 0, "missing": {}}
    return json.loads(m.group(1))


def accept(outputs: Path, fixture: str) -> tuple[int, int]:
    test = HERE / "accept" / ACCEPT[fixture]
    with tempfile.TemporaryDirectory() as td:
        ini = Path(td) / "pytest.ini"
        ini.write_text("[pytest]\n")
        env = clean_env(PYTHONPATH=str(outputs.resolve()))
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-c", str(ini),
                            "--rootdir", td, str(test)], cwd=td, env=env, capture_output=True, text=True, timeout=300)
    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", p.stdout)) else 0
    failed = sum(int(x) for x in re.findall(r"(\d+) (?:failed|error)", p.stdout))
    total = passed + failed
    if total == 0:  # 수집 단계에서 import 실패
        total = len(re.findall(r"^def test_", test.read_text(), re.M))
    return passed, total


def func_name(nodeid: str) -> str:
    parts = re.sub(r"\[.*$", "", nodeid).split("::")
    return ".".join(parts[1:]) if len(parts) > 1 else parts[0]


def runlog_metrics(run_dir: Path, events: list[dict]) -> dict | None:
    """runlog 플러그인 기록(pytest 실행마다 테스트별 결과)으로 사이클을 센다. 기록이 없으면 None.
    사이클 = 처음으로 통과한 테스트 함수가 생긴 pytest 실행. 그 실행에서 처음 통과한 함수 수가 burst다.
    동작 RED = 처음 통과하기 전에 import·이름 누락이 아닌 이유로 실패한 것이 기록됨."""
    cwd = next((e.get("cwd") for e in events if e.get("type") == "system" and e.get("cwd")), "")
    log_dir = Path(os.environ.get("RUNLOG_DIR") or run_dir.parents[4] / "runlog")
    f = log_dir / (Path(cwd).name + ".jsonl")
    if not cwd or not f.exists():
        return None
    sessions = sorted((json.loads(x) for x in f.read_text().splitlines() if x.strip()), key=lambda r: r["t"])
    passed_once: set[str] = set()
    red_ok: set[str] = set()
    bursts, missing_only = [], 0
    for s in sessions:
        agg: dict[str, tuple[str, str]] = {}  # 파라미터화 함수: 하나라도 실패면 실패
        for nid, r in s["tests"].items():
            n = func_name(nid)
            if n not in agg or (r["outcome"] == "failed" and agg[n][0] != "failed"):
                agg[n] = (r["outcome"], r["msg"])
        fails = [(n, m) for n, (o, m) in agg.items() if o == "failed"]
        if (s["collect_errors"] or fails) and all(MISSING.search(m) for _, m in fails) and \
                all(MISSING.search(c["msg"]) for c in s["collect_errors"]):
            missing_only += 1
        for n, m in fails:
            if n not in passed_once and not MISSING.search(m):
                red_ok.add(n)
        new = [n for n, (o, _) in agg.items() if o == "passed" and n not in passed_once]
        passed_once |= set(new)
        if new:
            bursts.append(len(new))
    return {"sessions": len(sessions), "bursts": bursts, "red_ok": red_ok, "missing_only": missing_only}


def analyze(run_dir: Path, fixture: str) -> dict:
    fixture_dir = HERE.parent / "fixtures" / fixture
    outputs = run_dir / "outputs"
    events = load_events(run_dir)
    tl = timeline(events, fixture_dir)
    writes = [t for t in tl if t[0] == "write"]
    first_test = next((i for i, t in enumerate(writes) if t[2] == "test"), None)
    first_src = next((i for i, t in enumerate(writes) if t[2] == "src"), None)
    bursts, last = [], 0
    for t in writes:
        if t[2] == "src":
            if t[3] - last > 0:
                bursts.append(t[3] - last)
            last = t[3]
    final_files = {str(p.relative_to(outputs)): p.read_text() for p in outputs.rglob("*.py")}
    final_tests: set[str] = set()
    for p, c in final_files.items():
        if is_test(p) and not p.endswith("conftest.py"):
            final_tests |= test_names(c)
    tail = max(0, len(final_tests) - last)
    runs = [t[1] for t in tl if t[0] == "pytest"]
    seen: dict[str, set[str]] = {}
    missing_only = 0
    for r in runs:
        for n, why in r["failed"].items():
            seen.setdefault(n, set()).add(why)
        kinds = set(r["failed"].values())
        if (r["collect_err"] or kinds) and kinds <= {"missing"}:
            missing_only += 1
    behav = {n for n, w in seen.items() if w & {"behavior", "stub", "unknown"}}
    source = "parse"
    rl = runlog_metrics(run_dir, events)
    if rl is not None:  # 출력 파싱·파일 복원보다 정확하므로 있으면 이것을 쓴다
        source, bursts, behav = "runlog", rl["bursts"], rl["red_ok"]
        missing_only, runs = rl["missing_only"], [None] * rl["sessions"]
        tail = 0
    red_behavior = len(final_tests & behav) / len(final_tests) if final_tests else 0.0
    cov = coverage(outputs)
    cov_ratio = cov["covered"] / cov["total"] if cov["total"] else 0.0
    acc_p, acc_t = accept(outputs, fixture)
    info = json.loads((run_dir / "run.json").read_text()) if (run_dir / "run.json").exists() else {}
    final_text = info.get("final_text", "")
    test_first = first_test is not None and (first_src is None or first_test < first_src)
    strict = (test_first and red_behavior >= 0.8 and len(bursts) >= 3 and max(bursts or [0]) <= 3
              and cov_ratio >= 0.9)
    return {
        "source": source, "test_first": test_first, "cycles": len(bursts), "bursts": bursts,
        "max_burst": max(bursts or [0]), "tail": tail, "n_tests": len(final_tests),
        "pytest_runs": len(runs), "red_runs_missing_only": missing_only,
        "red_behavior": round(red_behavior, 2), "coverage": round(cov_ratio, 2),
        "uncovered": {k: v for k, v in cov["missing"].items()}, "suite_exit": cov["exit"],
        "accept": f"{acc_p}/{acc_t}", "claims_tdd": bool(CLAIM.search(final_text)),
        "strict": strict, "unknown_writes": next(t[1] for t in tl if t[0] == "unknown_writes"),
        "turns": info.get("num_turns"), "output_tokens": info.get("output_tokens"),
        "duration_s": round((info.get("duration_ms") or 0) / 1000),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--one", help="fixture 이름 (RUN_DIR 환경변수의 run 하나)")
    ap.add_argument("--evals")
    ap.add_argument("--results")
    ap.add_argument("--tsv")
    a = ap.parse_args()
    if a.one:
        print(json.dumps(analyze(Path(os.environ["RUN_DIR"]), a.one), ensure_ascii=False))
        return
    evals = json.loads(Path(a.evals).read_text())["evals"]
    fixture_of = {re.sub(r"[^a-z0-9-_]", "-", (e.get("name") or "").lower()): Path(e["fixture"]).name for e in evals}
    cols = ["eval", "model", "rep", "strict", "test_first", "cycles", "max_burst", "tail", "n_tests",
            "red_behavior", "red_runs_missing_only", "pytest_runs", "coverage", "accept", "claims_tdd",
            "suite_exit", "unknown_writes", "turns", "output_tokens", "duration_s", "bursts", "uncovered"]
    rows = []
    for run in sorted(Path(a.results).glob("*/*/*/rep-*")):
        if not (run / "stream.jsonl").exists():
            continue
        ename, model, rep = run.parts[-4], run.parts[-3], run.parts[-1].split("-")[1]
        r = analyze(run, fixture_of[ename])
        rows.append([ename, model, rep] + [json.dumps(r[c], ensure_ascii=False) if isinstance(r[c], (list, dict)) else str(r[c])
                                            for c in cols[3:]])
        print("\t".join(rows[-1][:16]), file=sys.stderr)
    text = "\t".join(cols) + "\n" + "\n".join("\t".join(r) for r in rows) + "\n"
    if a.tsv:
        Path(a.tsv).write_text(text)
    else:
        print(text)


if __name__ == "__main__":
    main()
