"""tdd-cycle 상태 모듈. red_check.py(모델이 돌림)와 hooks/tdd_gate.py(Claude Code 훅)가 함께 쓴다.

프로젝트 루트(git toplevel, 없으면 cwd)마다 JSON 하나를 ~/.cache/tdd-cycle/<해시>.json에 둔다.
상태(state): none(아직 실행 없음) · red(동작 이유로 실패) · red_missing(import·이름·시그니처 누락으로만 실패) ·
green(마지막 실행이 초록) · refactor(초록에서 리팩터링 창을 연 상태, 다음 실행에서 닫힘) ·
unknown(pytest를 돌렸는데 출력을 읽지 못함 — 파이프로 잘림 등. 다음 실행까지 소스 수정 차단) (1.2.0)
1.2.0 게이트: no_red_pending(이 세션에서 쓴 테스트가 실패한 적 없이 통과 → --ack 전까지 소스 수정 차단),
src_counts_at_red(red 진입 시 소스 파일별 줄 수. 이번 사이클 증가가 SRC_GROWTH_LIMIT을 넘는 수정은 --big-step 선언 전까지 차단)
모드(mode): project(마커 파일·TDD_MODE=1) · prompt(요청에 TDD 언급) · off · off_user(요청으로 끔)
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

MISSING = re.compile(r"ModuleNotFoundError|ImportError|cannot import name|NameError|has no attribute|"
                     r"not callable|unexpected keyword argument|positional argument|takes no arguments")
STATE_DIR = Path(os.environ.get("TDD_CYCLE_STATE_DIR") or Path.home() / ".cache" / "tdd-cycle")
# \b는 한글 앞뒤에서 경계가 아니다("TDD로"). 영문자 경계만 본다.
ON_RE = re.compile(r"(?<![a-z])tdd(?![a-z])|test[- ]?(first|driven)|red[- ]?green|테스트\s*(먼저|부터|주도)|실패하는 테스트(를|부터)\s*먼저", re.I)
OFF_RE = re.compile(r"tdd\s*(없이|끄|해제|그만|off\b|끝|말고|말자|안 ?해)|without tdd|no tdd|skip (the )?tdd|not tdd", re.I)


# ---- 경로·상태 파일 --------------------------------------------------------

def project_root(cwd: str | os.PathLike | None = None) -> Path:
    cwd = Path(cwd or os.getcwd()).resolve()
    try:
        p = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        if p.returncode == 0 and p.stdout.strip():
            return Path(p.stdout.strip()).resolve()
    except Exception:  # noqa: BLE001
        pass
    return cwd


def state_path(root: Path) -> Path:
    return STATE_DIR / (hashlib.sha1(str(root).encode()).hexdigest()[:16] + ".json")


def fresh(session_id: str | None, mode: str) -> dict:
    return {"session_id": session_id, "mode": mode, "state": "none", "failing": {}, "passed_once": [], "seen_red": [],
            "premature": [], "runs": 0, "cycles": 0, "missing_to_green": 0, "refactors": 0, "blocks": 0, "log": [],
            # 1.2.0
            "touched_tests": [], "test_files": {}, "no_red_pending": [], "acks": 0,
            "src_counts_at_red": None, "big_step": None, "big_steps": 0, "unknown_runs": 0, "shell_unseen": 0,
            "skill_seen": False,
            "created": time.time()}


def load(root: Path) -> dict | None:
    p = state_path(root)
    try:
        st = json.loads(p.read_text()) if p.exists() else None
    except Exception:  # noqa: BLE001
        return None
    if st is not None:  # 이전 버전(1.1.0)의 상태 파일에 없는 키를 채운다
        for k, v in fresh(None, "off").items():
            st.setdefault(k, v)
    return st


def save(root: Path, st: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    st["log"] = st.get("log", [])[-200:]
    state_path(root).write_text(json.dumps(st, ensure_ascii=False))


def marker_on(root: Path) -> bool | None:
    """TDD_MODE 환경변수(1/0)가 있으면 그것, 없으면 .claude/tdd-mode 파일 유무. 둘 다 없으면 None."""
    env = os.environ.get("TDD_MODE", "").strip().lower()
    if env in ("0", "false", "off", "no"):
        return False
    if env in ("1", "true", "on", "yes"):
        return True
    return True if (root / ".claude" / "tdd-mode").exists() else None


def mode_on(st: dict | None, root: Path) -> bool:
    if st and st.get("mode") in ("project", "prompt"):
        return True
    if st and st.get("mode") == "off_user":
        return False
    return marker_on(root) is True


# ---- 파일 분류 --------------------------------------------------------------

def rel_to(root: Path, path: str) -> str | None:
    """root 아래의 상대 경로. 밖이면 None."""
    p = Path(path)
    p = (root / p) if not p.is_absolute() else p
    try:
        return str(p.resolve().relative_to(root))
    except ValueError:
        return None


def is_test(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return rel.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"
                                    or rel.startswith("tests/") or "/tests/" in rel)


def is_src(rel: str) -> bool:
    return rel.endswith(".py") and not is_test(rel)


# ---- pytest 출력 해석 --------------------------------------------------------

def func_name(nodeid: str) -> str:
    parts = re.sub(r"\[.*$", "", nodeid).split("::")
    return ".".join(parts[1:]) if len(parts) > 1 else parts[0]


def parse_pytest(text: str) -> dict:
    """-rA 출력(PASSED/FAILED/ERROR 줄)과 기본 출력(FAILED/ERROR 줄 + 요약) 둘 다 읽는다.
    result: green · red(동작 이유 실패 있음) · red_missing(누락 이유뿐) · None(결과를 읽지 못함)."""
    failed: dict[str, str] = {}
    passed: list[str] = []
    errors: list[str] = []
    files: dict[str, str] = {}  # 테스트 이름 → 파일(nodeid 앞부분). 1.2.0: 이 세션에서 쓴 테스트인지 가르는 데 쓴다
    for m in re.finditer(r"^\s*(PASSED|FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$", text, re.M):
        kind, nid, reason = m.group(1), m.group(2), (m.group(3) or "").strip()
        if "::" in nid:
            files.setdefault(func_name(nid), nid.split("::", 1)[0])
        if kind == "PASSED":
            passed.append(func_name(nid))
        elif kind == "FAILED":
            name = func_name(nid)
            if not (name in failed and failed[name] and not reason):
                failed[name] = reason
        else:
            errors.append(reason or nid)
    passed = [n for n in dict.fromkeys(passed) if n not in failed]
    counts: dict[str, int] = {}
    for n, k in re.findall(r"(\d+) (passed|failed|errors?|skipped|xfailed|xpassed)", text):
        counts[k.rstrip("s") if k.startswith("error") else k] = int(n)
    e_lines = re.findall(r"^E\s+(.*)$", text, re.M)
    n_failed = counts.get("failed", 0) or len(failed)
    n_error = counts.get("error", 0) or len(errors)
    no_tests = bool(re.search(r"no tests ran|no tests collected|collected 0 items", text))
    if n_failed == 0 and n_error == 0:
        result = "green" if counts.get("passed", 0) > 0 or passed else None
    else:
        behavior = [n for n, r in failed.items() if r and not MISSING.search(r)]
        unknown = [n for n, r in failed.items() if not r]
        missing_e = any(MISSING.search(e) for e in e_lines)
        if behavior or ((unknown or (n_failed and not failed)) and not missing_e):
            result = "red"
        else:
            result = "red_missing"
    return {"result": result, "failed": failed, "passed": passed, "errors": errors, "counts": counts, "files": files,
            "no_tests": no_tests and result is None}


# 명령 위치(줄 처음, ; && || | ( 뒤, 환경변수 접두 뒤, python -m / uv run / poetry run 뒤)의 pytest만 "확실한 실행"으로 본다.
# `echo pytest`·`grep pytest pyproject.toml`처럼 인자 자리의 pytest는 실행이 아니다.
PYTEST_RUN = re.compile(r"(?:^|[;&|(`\n])\s*(?:\w+=\S*\s+)*(?:timeout\s+\S+\s+)?"
                        r"(?:python3?\s+-m\s+|uv\s+run\s+(?:-m\s+)?|poetry\s+run\s+|pipenv\s+run\s+)?pytest(?=\s|$|[;&|)])")
PYTEST_NOT_RUN = re.compile(r"--version|--help|--collect-only|(?<!\S)--co(?!\S)|--fixtures|--markers")
HEREDOC_BODY = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?\n.*?\n\1", re.S)


def runs_pytest(cmd: str) -> bool:
    """명령이 pytest를 확실히 실행하는가. heredoc 본문('import pytest')·인자 자리의 pytest·--version 류는 아니다.
    확실한 실행인데 출력을 읽지 못하면 상태가 unknown이 된다. 확실하지 않은 언급은 읽히면 반영하고 아니면 무시한다(1.1.0과 같음)."""
    stripped = HEREDOC_BODY.sub("", cmd)
    return bool(PYTEST_RUN.search(stripped)) and not PYTEST_NOT_RUN.search(stripped)


SRC_GROWTH_LIMIT = 15  # 한 사이클에 늘어난 소스 줄 수가 이보다 크면 "테스트 하나가 요구한 것보다 많이 썼다"는 신호 [잠정]


SKIP_DIRS = ("node_modules", "build", "dist", "__pycache__")


def nonblank(text: str | None) -> int:
    """비어 있지 않고 주석만이 아닌 줄 수. (docstring은 센다 — 토큰화 없이 가르기 어렵고, 큰 docstring도 '많이 쓴 것'이다)"""
    return sum(1 for ln in (text or "").splitlines() if ln.strip() and not ln.strip().startswith("#")) if text else 0


def src_counts(root: Path) -> dict[str, int]:
    """root 아래 소스 .py(테스트·숨김·가상환경·빌드 산출물 제외)의 파일별 비어 있지 않은 줄 수."""
    out: dict[str, int] = {}
    for p in root.rglob("*.py"):
        rel = str(p.relative_to(root))
        top = rel.split("/")[0]
        if rel.startswith(".") or "/." in rel or "venv" in top or top in SKIP_DIRS or not is_src(rel):
            continue
        try:
            out[rel] = nonblank(p.read_text())
        except Exception:  # noqa: BLE001
            pass
    return out


def src_lines(root: Path) -> int:
    return sum(src_counts(root).values())


def growth_if_applied(root: Path, snapshot: dict[str, int] | None, rel: str, new: str | None) -> int | None:
    """red 진입 스냅숏 대비, rel을 new로 바꾸면 이번 사이클 소스가 몇 줄 늘어나는가. 스냅숏·내용이 없으면 None."""
    if snapshot is None or new is None:
        return None
    now = src_counts(root)
    now[rel] = nonblank(new)
    return sum(now.values()) - sum(snapshot.values())


def apply_run(st: dict, parsed: dict, via: str, root: Path | None = None) -> list[str]:
    """pytest 실행 결과를 상태에 반영하고 모델에게 보일 메모를 돌려준다."""
    res = parsed["result"]
    if res is None:
        # 1.2.0: pytest를 돌렸는데 결과를 읽지 못했다(파이프·리다이렉트로 잘림 등). 앞 상태를 믿을 수 없으니 unknown으로 둔다.
        # "no tests ran"은 읽은 것이다(테스트가 없음) — 상태를 바꾸지 않는다.
        if via == "bash" and not parsed.get("no_tests"):
            st["state"] = "unknown"
            st["unknown_runs"] += 1
            st["log"].append({"t": round(time.time()), "via": via, "result": "unknown"})
            return ["pytest 출력을 읽지 못했다(파이프·리다이렉트로 잘렸거나 요약 줄이 없다). 결과를 확인할 때까지 소스 수정이 막힌다. "
                    "`red_check.py <테스트>`로 다시 돌린다. 출력을 tail·grep으로 자르지 않는다."]
        return []
    prev = st["state"]
    first_run = st["runs"] == 0
    st["runs"] += 1
    notes: list[str] = []
    counts_now = src_counts(root) if root else None
    lines_now = sum(counts_now.values()) if counts_now is not None else None
    passed_once, seen_red = set(st["passed_once"]), set(st["seen_red"])
    st["test_files"] = {**st.get("test_files", {}), **parsed.get("files", {})}
    # 1.2.0: 동작 RED를 본 테스트는 "RED 없음" 미확인 목록에서 빠진다(기대값을 고쳐 RED를 본 경우)
    behavior_now = {n for n, r in parsed["failed"].items() if r and not MISSING.search(r)}
    st["no_red_pending"] = [n for n in st.get("no_red_pending", []) if n not in behavior_now]
    if res == "green":
        if prev == "red":
            st["cycles"] += 1
            snap = st.get("src_counts_at_red")
            grew = (lines_now - sum(snap.values())) if lines_now is not None and snap else None
            notes.append(f"사이클 {st['cycles']} GREEN." + (f" 소스 +{grew}줄." if grew is not None else "")
                         + (f" (큰 걸음 선언: {st['big_step']})" if st.get("big_step") else ""))
            if grew is not None and grew > SRC_GROWTH_LIMIT and not st.get("big_step"):
                notes.append(f"테스트 하나를 통과시키는 데 {grew}줄은 많다. 다음 테스트가 RED 없이 통과하면 이 사이클이 앞서 나간 근거다. "
                             "가장 작은 코드로 줄일 수 있으면 지금 줄인다.")
        elif prev == "red_missing":
            st["missing_to_green"] += 1
            notes.append("import 오류 RED에서 바로 GREEN이 됐다. 어떤 테스트도 동작 때문에 실패하는 것을 보지 못했다. "
                         "다음 사이클부터는 스텁만 만들고 다시 돌려 RED (동작)을 본 뒤 구현한다.")
        elif prev == "refactor":
            notes.append("리팩터링 창 닫힘(초록).")
        fresh_pass = [n for n in parsed["passed"] if n not in passed_once and n not in seen_red]
        if fresh_pass and not first_run:  # 세션 첫 실행에서 통과한 테스트는 기존 테스트로 본다
            st["premature"] = list(dict.fromkeys(st["premature"] + fresh_pass))
            # 1.2.0: 이 세션에서 쓴 테스트 파일의 것만 게이트(미확인 목록)에 넣는다. 기존 테스트를 처음 돌린 경우는 메모만.
            mine = [n for n in fresh_pass if written_here(st, n)]
            if mine:
                st["no_red_pending"] = list(dict.fromkeys(st["no_red_pending"] + mine))
            notes.append("RED 없음: " + ", ".join(fresh_pass[:5]) + (" …" if len(fresh_pass) > 5 else "")
                         + ". 실패한 적 없이 통과했다. 기대값이 명세와 맞는지 보고, 맞으면 앞 사이클 구현이 이 동작을 먼저 넣은 것이다. "
                           "사이클 표에 'RED 없음'으로 적는다."
                         + (" 이 중 이 세션에서 쓴 테스트(" + ", ".join(mine[:5]) + ")는 `red_check.py --ack <이름>`으로 기록하거나 "
                            "기대값을 고쳐 RED를 보기 전까지 소스 수정이 막힌다." if mine else ""))
        st["failing"] = {}
        st["big_step"] = None
    else:
        new_behavior = [n for n, r in parsed["failed"].items() if r and not MISSING.search(r) and n not in passed_once]
        seen_red |= set(new_behavior)
        st["failing"] = parsed["failed"]
        if res == "red" and prev != "red":
            st["src_counts_at_red"] = counts_now
            st["big_step"] = None
        if res == "red" and len(new_behavior) > 3:
            notes.append(f"새 테스트 {len(new_behavior)}개가 한꺼번에 실패했다. 사이클당 하나(경계값이면 셋까지)만 남기고 "
                         "나머지는 지우거나 skip 표시한 뒤 다시 RED를 확인한다.")
    st["state"] = res
    st["passed_once"] = sorted(passed_once | set(parsed["passed"]))
    st["seen_red"] = sorted(seen_red)
    st["log"].append({"t": round(time.time()), "via": via, "result": res, "failed": list(parsed["failed"])[:5],
                      "passed": parsed["counts"].get("passed", len(parsed["passed"]))})
    return notes


def written_here(st: dict, test_name: str) -> bool:
    """이 테스트의 파일이 이 세션에서 쓰인(Write·Edit·heredoc 등) 테스트 파일인가. 파일을 모르면 False(게이트를 걸지 않는다)."""
    f = st.get("test_files", {}).get(test_name)
    if not f:
        return False
    f = f.lstrip("./")
    return any(t == f or t.endswith("/" + f) or f.endswith("/" + t) for t in st.get("touched_tests", []))


def summary(st: dict) -> str:
    extra = ""
    if any(st.get(k) for k in ("acks", "big_steps", "unknown_runs", "shell_unseen")):
        extra = (f" · RED 없음 기록(ack) {st.get('acks', 0)} · 큰 걸음 선언 {st.get('big_steps', 0)}"
                 f" · 결과 못 읽은 pytest {st.get('unknown_runs', 0)} · 내용 못 본 셸 수정 {st.get('shell_unseen', 0)}")
    return (f"tdd-cycle: 사이클 {st['cycles']} · 동작 RED를 거친 테스트 {len(st['seen_red'])} · RED 없이 통과 {len(st['premature'])}"
            f" · import RED→GREEN 직행 {st['missing_to_green']} · 리팩터링 창 {st['refactors']} · 훅 차단 {st['blocks']}"
            f" · pytest 실행 {st['runs']}" + extra)


# ---- 스텁 검사 (red_missing 상태에서 허용되는 소스 변경) ------------------------------

def _stub_return(v: ast.expr | None) -> bool:
    if v is None or isinstance(v, ast.Constant):
        return True
    if isinstance(v, ast.Name) and v.id == "None":
        return True
    if isinstance(v, (ast.List, ast.Tuple, ast.Set)) and not v.elts:
        return True
    return isinstance(v, ast.Dict) and not v.keys


def is_stub_body(body: list[ast.stmt]) -> bool:
    stmts = list(body)
    if stmts and isinstance(stmts[0], ast.Expr) and isinstance(stmts[0].value, ast.Constant) and isinstance(stmts[0].value.value, str):
        stmts = stmts[1:]
    for s in stmts:
        if isinstance(s, ast.Pass):
            continue
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is ...:
            continue
        if isinstance(s, ast.Return) and _stub_return(s.value):
            continue
        if isinstance(s, ast.Raise) and s.exc is not None and "NotImplementedError" in ast.unparse(s.exc):
            continue
        if isinstance(s, ast.Assign) and isinstance(s.value, (ast.Name, ast.Constant)) and all(
                isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self" for t in s.targets):
            continue  # self.x = x 같은 저장만 허용
        return False
    return True


def _funcs(tree: ast.AST) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    out = []

    def walk(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append((prefix + child.name, child))
                walk(child, prefix + child.name + ".")
            elif isinstance(child, ast.ClassDef):
                walk(child, prefix + child.name + ".")
            else:
                walk(child, prefix)
    walk(tree, "")
    return out


def nonstub_defs(old: str | None, new: str) -> list[str]:
    """new에서 본문이 바뀌었거나 새로 생긴 함수 중 스텁이 아닌 것의 이름. 구문 오류면 판정하지 않는다(빈 목록)."""
    try:
        new_tree = ast.parse(new)
    except SyntaxError:
        return []
    old_bodies: dict[str, str] = {}
    if old:
        try:
            old_bodies = {q: ast.unparse(ast.Module(body=n.body, type_ignores=[])) for q, n in _funcs(ast.parse(old))}
        except SyntaxError:
            pass
    bad = []
    for q, node in _funcs(new_tree):
        body = ast.unparse(ast.Module(body=node.body, type_ignores=[]))
        if old_bodies.get(q) == body:
            continue
        if not is_stub_body(node.body):
            bad.append(q)
    return bad
