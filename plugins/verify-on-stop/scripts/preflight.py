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

JS/TS 경로(package.json이 있을 때): 연관 테스트(vitest 또는 jest; 상대 import·re-export 그래프), tsc --noEmit, eslint -f json.
도구는 프로젝트의 node_modules/.bin에 있을 때만 쓴다(npx로 내려받지 않는다). 바뀐 파일이 JS/TS뿐이면 Python 단계는 건너뛴다.
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
import tempfile
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
def walk(exts: tuple[str, ...]) -> list[Path]:
    """SKIP_DIRS(node_modules 등)는 내려가지 않는다. rglob은 node_modules 전체를 훑어 느리다."""
    out = []
    for d, dirs, names in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        out += [Path(d) / n for n in names if n.endswith(exts)]
    return out


def py_files() -> list[Path]:
    return walk((".py",))


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


# ---------- JS/TS ----------
JS_EXTS = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
JS_TEST = re.compile(r"(\.(test|spec)\.[cm]?[jt]sx?$)|(^|/)__tests__/")
JS_SPEC = re.compile(r"""(?:\bfrom\s*|\bimport\s*\(\s*|\brequire\s*\(\s*|^\s*import\s+)['"](\.{1,2}/[^'"]+)['"]""", re.M)
ESLINT_CONFIGS = ("eslint.config.js", "eslint.config.mjs", "eslint.config.cjs", "eslint.config.ts",
                  ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json", ".eslintrc.yml", ".eslintrc.yaml")


def node_bin(name: str) -> str | None:
    p = ROOT / "node_modules" / ".bin" / name
    return str(p) if p.exists() else None


def js_files() -> list[Path]:
    return [p for p in walk(JS_EXTS) if not p.name.endswith(".d.ts")]


def resolve_spec(src: Path, spec: str) -> Path | None:
    base = (src.parent / spec).resolve()
    stem = base.with_suffix("") if base.suffix in (".js", ".jsx", ".mjs", ".cjs") else base  # NodeNext: './x.js' → x.ts
    for cand in [base, *(stem.with_name(stem.name + e) for e in JS_EXTS), *(base / f"index{e}" for e in JS_EXTS)]:
        if cand.is_file():
            return cand
    return None


def select_js_tests(changed: list[str]) -> tuple[list[str], str]:
    files = js_files()
    changed_js = {(ROOT / c).resolve() for c in changed if c.endswith(JS_EXTS) and (ROOT / c).exists()}
    if not changed_js:
        return [], "no changed JS/TS files"
    importers: dict[Path, set[Path]] = {}
    for f in files:
        for spec in JS_SPEC.findall(f.read_text(errors="replace")):
            t = resolve_spec(f, spec)
            if t:
                importers.setdefault(t, set()).add(f.resolve())
    affected, frontier = set(changed_js), set(changed_js)
    while frontier:
        nxt = set().union(*(importers.get(t, set()) for t in frontier)) - affected
        affected |= nxt
        frontier = nxt
    tests = sorted(str(p.relative_to(ROOT.resolve())) for p in affected if JS_TEST.search(str(p.relative_to(ROOT.resolve()))))
    return tests, f"{len(changed_js)} changed JS/TS → {len(affected)} affected files"


def run_js_tests(targets: list[str], timeout: int) -> dict:
    out_file = Path(tempfile.gettempdir()) / f"preflight-{os.getpid()}-tests.json"
    if exe := node_bin("vitest"):
        runner, cmd = "vitest", [exe, "run", "--reporter=json", f"--outputFile={out_file}", *targets]
    elif exe := node_bin("jest"):
        runner, cmd = "jest", [exe, "--json", f"--outputFile={out_file}", *(["--runTestsByPath", *targets] if targets else [])]
    else:
        return {"status": "skipped", "reason": "no vitest/jest in node_modules/.bin"}
    out_file.unlink(missing_ok=True)
    rc, out = sh(cmd, timeout)
    try:
        r = json.loads(out_file.read_text())
    except (OSError, json.JSONDecodeError):
        return {"status": "fail" if rc else "zero_tests", "runner": runner, "exit": rc, "passed": 0, "failed": 0,
                "tail": [l for l in out.strip().splitlines() if l.strip()][-3:]}
    finally:
        out_file.unlink(missing_ok=True)
    passed, failed = r.get("numPassedTests", 0), r.get("numFailedTests", 0)
    suite_err = [s for s in r.get("testResults", []) if s.get("status") == "failed" and not any(
        a.get("status") == "failed" for a in s.get("assertionResults", []))]
    fails = [f"{Path(s.get('name', '')).relative_to(ROOT.resolve()) if s.get('name', '').startswith(str(ROOT.resolve())) else s.get('name')} > {a.get('fullName')}"
             for s in r.get("testResults", []) for a in s.get("assertionResults", []) if a.get("status") == "failed"]
    fails += [f"{s.get('name', '').replace(str(ROOT.resolve()) + '/', '')}: {(s.get('message') or '').strip().splitlines()[0][:120] if s.get('message') else 'suite failed'}" for s in suite_err]
    status = "fail" if (failed or suite_err) else ("zero_tests" if not passed else ("pass" if rc == 0 else "fail"))
    return {"status": status, "runner": runner, "exit": rc, "passed": passed, "failed": failed, "errors": len(suite_err),
            "first_failures": fails[:5]}


def run_tsc(timeout: int) -> dict:
    exe = node_bin("tsc")
    if not exe or not (ROOT / "tsconfig.json").exists():
        return {"status": "skipped", "reason": "no tsconfig.json or tsc in node_modules/.bin"}
    rc, out = sh([exe, "--noEmit", "--pretty", "false", "-p", "tsconfig.json"], timeout)
    errs = [l for l in out.splitlines() if re.search(r"error TS\d+", l)]
    if rc != 0 and not errs:  # tsc 자체 오류(설정 파싱 실패 등): 타입 오류가 아니므로 막지 않는다
        return {"status": "error", "exit": rc, "count": 0, "tail": [l for l in out.strip().splitlines() if l.strip()][:2]}
    return {"status": "pass" if rc == 0 else "fail", "exit": rc, "count": len(errs), "first": errs[:3]}


def run_eslint(targets: list[str], timeout: int) -> dict:
    exe = node_bin("eslint")
    if not exe or not any((ROOT / c).exists() for c in ESLINT_CONFIGS):
        return {"status": "skipped", "reason": "no eslint config or eslint in node_modules/.bin"}
    rc, out = sh([exe, "-f", "json", *(targets or ["."])], timeout)
    try:
        items = json.loads(out[out.index("["):])
    except (ValueError, json.JSONDecodeError):
        # exit 2 = 설정 오류·크래시. 린트 위반이 아니므로 막지 않고 "검사 못 함"으로 보고한다
        return {"status": "error" if rc else "pass", "exit": rc, "count": None, "tail": [l for l in out.strip().splitlines() if l.strip()][:2]}
    first = [f"{i['filePath'].replace(str(ROOT.resolve()) + '/', '')}:{m.get('line')} {m.get('ruleId')} {m.get('message')}"
             for i in items for m in i.get("messages", []) if m.get("severity") == 2]
    count = sum(i.get("errorCount", 0) for i in items)
    return {"status": "pass" if count == 0 else "fail", "exit": rc, "count": count, "first": first[:3]}


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
    changed_py = [c for c in changed if c.endswith(".py") and (ROOT / c).exists()]
    changed_js = [c for c in changed if c.endswith(JS_EXTS) and (ROOT / c).exists()]
    js_project = (ROOT / "package.json").exists()
    # JS/TS 프로젝트에서 바뀐 소스가 JS/TS뿐이면 Python 단계는 건너뛴다 (pytest 0개 → exit 2로 떨어지지 않게)
    run_py = not (js_project and changed_js and not changed_py) and not (js_project and not py_files())
    run_js = js_project and (bool(changed_js) or a.all or not changed_py)

    report: dict = {"changed_files": changed[:8]}
    if run_py:
        tests, why = ([], "--all") if a.all else select_tests(changed)
        fallback = not a.all and not tests
        if fallback:
            why += " → falling back to full suite"
        report.update({"selected_tests": tests[:8] if not fallback else "ALL", "selection": why})
        report["pytest"] = run_pytest([] if (a.all or fallback) else tests, a.timeout)
        src = changed_py or ["."]
        if not a.no_lint:
            report["ruff"] = run_ruff(src, a.timeout)
        if not a.no_types:
            report["mypy"] = run_mypy(src, a.timeout)
    if run_js:
        jtests, jwhy = ([], "--all") if a.all else select_js_tests(changed)
        jfallback = not a.all and not jtests
        if jfallback:
            jwhy += " → falling back to full suite"
        report.update({"js_selected_tests": jtests[:8] if not jfallback else "ALL", "js_selection": jwhy})
        report["js_tests"] = run_js_tests([] if (a.all or jfallback) else jtests, a.timeout)
        if not a.no_types:
            report["tsc"] = run_tsc(a.timeout)
        if not a.no_lint:
            report["eslint"] = run_eslint(changed_js, a.timeout)

    statuses = [v["status"] for k, v in report.items() if isinstance(v, dict) and "status" in v]
    test_steps = [report[k]["status"] for k in ("pytest", "js_tests") if k in report]
    if not test_steps or all(s in ("zero_tests", "skipped") for s in test_steps):
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
