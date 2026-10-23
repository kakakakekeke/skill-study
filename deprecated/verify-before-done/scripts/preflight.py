#!/usr/bin/env python3
"""preflight: 완료 선언 전에 돌리는 결정적 검사. 출력은 JSON 30줄 이내, 종료 코드는 종합 결과.

사용:
  python3 preflight.py                 # git diff(작업 트리 + staged)로 변경 파일 → 연관 테스트만 + ruff + mypy
  python3 preflight.py --all           # 전체 테스트
  python3 preflight.py --since HEAD~1  # 비교 기준 커밋
  python3 preflight.py --no-lint --no-types
  python3 preflight.py --files a.py b.py   # git 없이 변경 파일 직접 지정

판정:
  exit 0  모든 단계 통과 (테스트 1개 이상 실행됨)
  exit 1  테스트 실패 / 수집 오류 / 린트·타입 오류
  exit 2  테스트가 0개 실행됨 (선택 결과가 비었거나 수집 실패) — "통과"가 아니다
연관 테스트 선택: 변경된 모듈을 (간접으로) import하는 테스트 파일. 테스트 파일 자체가 바뀌면 그 파일.
선택이 비면(변경 파일이 .py가 아니거나 매핑 실패) 전체 스위트로 떨어진다.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist", ".claude"}


def sh(cmd: list[str], timeout: int) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return -1, f"not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, f"timeout after {timeout}s"


# ---------- 변경 파일 ----------
def changed_files(since: str | None) -> list[str]:
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        return []
    files: set[str] = set()
    cmds = [["git", "diff", "--name-only", since] if since else ["git", "diff", "--name-only", "HEAD"],
            ["git", "ls-files", "--others", "--exclude-standard"]]
    for c in cmds:
        rc, out = sh(c, 30)
        if rc == 0:
            files.update(l.strip() for l in out.splitlines() if l.strip())
    return sorted(files)


# ---------- import 그래프 ----------
def py_files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        out.append(p)
    return out


def module_names(p: Path) -> set[str]:
    """파일이 어떤 모듈 이름들로 import될 수 있는지 (pkg.mod, pkg, mod)."""
    rel = p.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    names = set()
    for i in range(len(parts)):
        names.add(".".join(parts[i:]))
    return names


def imports_of(p: Path) -> set[str]:
    try:
        tree = ast.parse(p.read_text(errors="replace"))
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            for a in node.names:
                names.add(f"{node.module}.{a.name}")
    return names


def is_test_file(p: Path) -> bool:
    n = p.name
    return (n.startswith("test_") or n.endswith("_test.py")) and n.endswith(".py")


def select_tests(changed: list[str]) -> tuple[list[str], str]:
    files = py_files()
    changed_py = [ROOT / c for c in changed if c.endswith(".py") and (ROOT / c).exists()]
    if not changed_py:
        return [], "no changed .py files"
    mod_of: dict[Path, set[str]] = {p: module_names(p) for p in files}
    imp_of: dict[Path, set[str]] = {p: imports_of(p) for p in files}

    def importers(target: Path) -> set[Path]:
        tn = mod_of[target]
        return {p for p in files if p != target and (imp_of[p] & tn or any(i.startswith(t + ".") for i in imp_of[p] for t in tn))}

    affected: set[Path] = set(changed_py)
    frontier = set(changed_py)
    while frontier:
        nxt: set[Path] = set()
        for t in frontier:
            if t in mod_of:
                nxt |= importers(t) - affected
        affected |= nxt
        frontier = nxt
    tests = sorted(str(p.relative_to(ROOT)) for p in affected if is_test_file(p))
    return tests, f"{len(changed_py)} changed .py → {len(affected)} affected files"


# ---------- 단계 ----------
def run_pytest(targets: list[str], timeout: int) -> dict:
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header", "-rfE", *targets]
    rc, out = sh(cmd, timeout)
    m = re.search(r"(\d+) passed", out)
    passed = int(m.group(1)) if m else 0
    m = re.search(r"(\d+) failed", out)
    failed = int(m.group(1)) if m else 0
    m = re.search(r"(\d+) error", out)
    errors = int(m.group(1)) if m else 0
    fails = re.findall(r"^(?:FAILED|ERROR) (\S+)", out, re.M)
    collect_err = "ImportError" in out or "collected 0 items" in out or "no tests ran" in out
    status = "pass" if rc == 0 and passed > 0 else ("zero_tests" if passed == 0 and failed == 0 else "fail")
    if rc == -1:
        status = "skipped"
    return {"status": status, "exit": rc, "passed": passed, "failed": failed, "errors": errors,
            "first_failures": fails[:5], "collection_error": collect_err,
            "tail": [l for l in out.strip().splitlines() if l.strip()][-3:]}


def run_ruff(targets: list[str], timeout: int) -> dict:
    exe = shutil.which("ruff")
    cmd = [exe, "check", "--output-format", "json", *targets] if exe else [sys.executable, "-m", "ruff", "check", "--output-format", "json", *targets]
    rc, out = sh(cmd, timeout)
    if rc < 0 or "No module named" in out:
        return {"status": "skipped", "reason": "ruff not installed"}
    try:
        items = json.loads(out[out.index("["):])
    except (ValueError, json.JSONDecodeError):
        return {"status": "fail" if rc else "pass", "exit": rc, "count": None, "tail": out.strip().splitlines()[-2:]}
    first = [f"{i['filename'].replace(str(ROOT)+'/', '')}:{i['location']['row']} {i['code']} {i['message']}" for i in items[:3]]
    return {"status": "pass" if not items else "fail", "exit": rc, "count": len(items), "first": first}


def run_mypy(targets: list[str], timeout: int) -> dict:
    exe = shutil.which("mypy")
    base = [exe] if exe else [sys.executable, "-m", "mypy"]
    cmd = [*base, "--no-error-summary", "--hide-error-context", "--no-color-output", "--ignore-missing-imports", *targets]
    rc, out = sh(cmd, timeout)
    if rc < 0 or "No module named" in out:
        return {"status": "skipped", "reason": "mypy not installed"}
    errs = [l for l in out.splitlines() if ": error:" in l]
    return {"status": "pass" if rc == 0 else "fail", "exit": rc, "count": len(errs), "first": errs[:3]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="전체 테스트")
    ap.add_argument("--since", default=None, help="git 비교 기준")
    ap.add_argument("--files", nargs="*", default=None, help="변경 파일 직접 지정")
    ap.add_argument("--no-lint", action="store_true")
    ap.add_argument("--no-types", action="store_true")
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    changed = a.files if a.files is not None else changed_files(a.since)
    tests, why = ([], "--all") if a.all else select_tests(changed)
    fallback = not a.all and not tests
    targets = [] if (a.all or fallback) else tests
    if fallback:
        why += " → falling back to full suite"

    report: dict = {"changed_files": changed[:8], "selected_tests": tests[:8] if not fallback else "ALL", "selection": why}
    report["pytest"] = run_pytest(targets, a.timeout)
    src = [c for c in changed if c.endswith(".py") and (ROOT / c).exists()] or ["."]
    if not a.no_lint:
        report["ruff"] = run_ruff(src, a.timeout)
    if not a.no_types:
        report["mypy"] = run_mypy(src, a.timeout)

    statuses = [v["status"] for k, v in report.items() if isinstance(v, dict) and "status" in v]
    if report["pytest"]["status"] == "zero_tests":
        verdict, code = "ZERO_TESTS_RAN", 2
    elif any(s == "fail" for s in statuses):
        verdict, code = "FAIL", 1
    else:
        verdict, code = "PASS", 0
    report["verdict"] = verdict
    report["exit_code"] = code
    # 요약은 30줄 안에: 최상위 키마다 한 줄
    for k, v in report.items():
        print(f'"{k}": {json.dumps(v, ensure_ascii=False)}')
    print(f"[preflight] verdict={verdict} exit={code}")
    sys.exit(code)


if __name__ == "__main__":
    main()
