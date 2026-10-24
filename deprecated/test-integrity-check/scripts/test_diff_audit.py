#!/usr/bin/env python3
"""테스트 약화(test weakening) 감지기.

BEFORE/AFTER 두 디렉터리의 파이썬 테스트 파일을 AST로 비교해 테스트를 약화시키는 변경
(테스트 삭제·assert 제거·skip 추가·기대값 변경·비교 완화·테스트를 침묵시키는 설정 변경)을
열거한다. 결정적이며 표준 라이브러리만 사용한다. `audit(before, after)`로 임포트해 쓸 수 있다.

사용: python3 test_diff_audit.py <before_dir> <after_dir> [--tests-glob G ...] [--json] [--quiet]
종료 코드: 0 약화 없음 / 1 약화 발견 / 2 사용법 오류.
"""
from __future__ import annotations

import argparse
import ast
import copy
import difflib
import fnmatch
import json
import re
import sys
from collections import Counter
from pathlib import Path

CONFIG_FILES = {"pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"}
SILENCING_RE = re.compile(
    r"\baddopts\b|(?<![\w-])-k(?![\w-])|--deselect|--ignore|\bmarkers\b|\btestpaths\b|\bnorecursedirs\b"
)
SKIP_RE = re.compile(r"\b(skip|skipif|skipIf|skipUnless|xfail|importorskip|SkipTest)\b")
STRONG_UNITTEST = {"assertEqual", "assertEquals", "assertListEqual", "assertDictEqual", "assertIs"}
LOOSE_OPS = {ast.NotEq: "!=", ast.In: "in", ast.IsNot: "is not", ast.LtE: "<=", ast.GtE: ">="}
WEAKENING = (
    "deleted_test_files", "deleted_tests", "removed_asserts", "added_skips",
    "changed_expected_values", "loosened_comparisons", "unparseable_after", "config_silencing",
)
ORDER = WEAKENING[:-1] + ("renamed_tests", "added_test_files", "config_changes", "unparseable_before")
CAP = 10


def trunc(s: str) -> str:
    return s if len(s) <= 120 else s[:117] + "..."


# ── 파일 수집 ────────────────────────────────────────────────────────────────
def is_test_path(rel: str, globs: list[str] | None) -> bool:
    """기본 규칙: **/tests/**, **/test/**, test_*.py, *_test.py, conftest.py. globs가 있으면 그것만 사용."""
    p = Path(rel)
    if globs:
        return any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(p.name, g) for g in globs)
    if p.suffix != ".py":
        return False
    return bool({"tests", "test"} & set(p.parts[:-1])) or p.name.startswith("test_") \
        or p.name.endswith("_test.py") or p.name == "conftest.py"


def scan(root: Path, globs: list[str] | None) -> tuple[dict[str, Path], dict[str, Path]]:
    """루트 기준 상대 경로 → 파일. (테스트 파일, 설정 파일). __pycache__는 무시."""
    tests, configs = {}, {}
    for f in sorted(root.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts:
            continue
        rel = f.relative_to(root).as_posix()
        if f.name in CONFIG_FILES:
            configs[rel] = f
        elif is_test_path(rel, globs):
            tests[rel] = f
    return tests, configs


# ── AST 유틸 ─────────────────────────────────────────────────────────────────
def walk_body(fn: ast.AST):
    """함수 본문을 소스 순서(전위)로 순회. 중첩 def/class/lambda 안쪽은 내려가지 않는다."""
    stack = list(reversed(fn.body))
    while stack:
        n = stack.pop()
        yield n
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            stack.extend(reversed(list(ast.iter_child_nodes(n))))


def collect_tests(tree: ast.Module) -> dict[str, tuple[ast.AST, list[ast.expr]]]:
    """테스트 함수 수집. 키는 `Class.method` 또는 `func`, 값은 (노드, 상위 클래스 데코레이터)."""
    out: dict[str, tuple[ast.AST, list[ast.expr]]] = {}

    def visit(body, prefix, cls_decos):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                out[prefix + node.name] = (node, cls_decos)
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                visit(node.body, prefix + node.name + ".", cls_decos + node.decorator_list)

    visit(tree.body, "", [])
    return out


def module_skips(tree: ast.Module) -> list[str]:
    """모듈 수준 skip 요소: pytestmark/skip·importorskip 호출/collect_ignore 등."""
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            continue
        s = ast.unparse(node)
        if SKIP_RE.search(s) or s.startswith("collect_ignore"):
            out.append(trunc(s))
    return out


def fn_skips(fn: ast.AST, cls_decos: list[ast.expr]) -> list[str]:
    """함수·클래스 데코레이터와 본문 호출 중 skip/xfail/importorskip/SkipTest에 해당하는 것."""
    out = [ast.unparse(d) for d in list(fn.decorator_list) + cls_decos if SKIP_RE.search(ast.unparse(d))]
    for n in walk_body(fn):
        if isinstance(n, ast.Call) and SKIP_RE.search(ast.unparse(n.func)):
            out.append(trunc(ast.unparse(n)))
    return out


def is_assert_call(n: ast.AST) -> bool:
    return isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
        and (n.func.attr.startswith("assert") or n.func.attr in ("raises", "warns"))


def asserts_of(fn: ast.AST) -> list[ast.AST]:
    """assert 문의 조건식, self.assert* 호출, pytest.raises/warns 호출을 소스 순서로 수집."""
    return [n.test if isinstance(n, ast.Assert) else n
            for n in walk_body(fn) if isinstance(n, ast.Assert) or is_assert_call(n)]


def has_early_return(fn: ast.AST) -> bool:
    """어떤 assert보다 앞선 위치에 return이 있으면 True (근사치)."""
    nodes = list(walk_body(fn))
    rets = [n.lineno for n in nodes if isinstance(n, ast.Return)]
    asrs = [n.lineno for n in nodes if isinstance(n, ast.Assert) or is_assert_call(n)]
    return bool(rets) and bool(asrs) and min(rets) < max(asrs)


def lhs(node: ast.AST) -> str:
    if isinstance(node, ast.Compare):
        return ast.unparse(node.left)
    if isinstance(node, ast.Call) and node.args:
        return ast.unparse(node.args[0])
    return ast.unparse(node)


def literals(node: ast.AST) -> list[str]:
    return sorted(repr(n.value) for n in ast.walk(node) if isinstance(n, ast.Constant))


def pair_asserts(b: list[ast.AST], a: list[ast.AST]) -> list[tuple[ast.AST, ast.AST]]:
    """개수가 같으면 i번째끼리, 다르면 좌변 소스가 같은 것끼리 짝지음."""
    if len(b) == len(a):
        return list(zip(b, a))
    amap: dict[str, ast.AST] = {}
    for n in a:
        amap.setdefault(lhs(n), n)
    return [(n, amap[lhs(n)]) for n in b if lhs(n) in amap]


def approx_tol(node: ast.AST) -> dict[str, float | None] | None:
    """pytest.approx 호출의 abs/rel 허용치. approx가 없으면 None."""
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("approx"):
            return {kw.arg: kw.value.value if isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, (int, float)) else None
                    for kw in n.keywords if kw.arg in ("abs", "rel")}
    return None


def is_not_none(node: ast.AST) -> bool:
    return isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.IsNot) \
        and isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None


def loosened_reason(b: ast.AST, a: ast.AST) -> str | None:
    """b → a 변경이 비교를 완화했다면 그 이유 문자열, 아니면 None."""
    if ast.dump(a) == ast.dump(b):
        return None
    if isinstance(a, ast.Constant) and a.value is True:
        return "assert True"
    if is_not_none(a) and not is_not_none(b):
        return "is not None"
    if isinstance(b, ast.Compare) and isinstance(a, ast.Compare) and len(b.ops) == len(a.ops) == 1 \
            and isinstance(b.ops[0], ast.Eq) and type(a.ops[0]) in LOOSE_OPS:
        return f"== -> {LOOSE_OPS[type(a.ops[0])]}"
    if is_assert_call(b) and is_assert_call(a) and b.func.attr in STRONG_UNITTEST \
            and a.func.attr not in STRONG_UNITTEST:
        return f"{b.func.attr} -> {a.func.attr}"
    tb, ta = approx_tol(b), approx_tol(a)
    if ta is not None:
        if tb is None:
            return "approx added"
        for k, v in ta.items():
            if k not in tb:
                return f"approx {k}= added"
            if v is not None and tb[k] is not None and v > tb[k]:
                return f"approx {k}= increased"
    return None


class _Norm(ast.NodeTransformer):
    """식별자 이름을 지워 '이름만 바뀐' 본문을 같게 만든다. 키워드 인자 이름(rate= → hourly_rate=)도 식별자로 본다."""

    def visit_Name(self, node):
        node.id = "_"
        return node

    def visit_keyword(self, node):
        self.generic_visit(node)
        if node.arg is not None:
            node.arg = "_"
        return node

    def visit_arg(self, node):
        node.arg = "_"
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        node.attr = "_"
        return node


def fingerprint(fn: ast.AST, normalize: bool = False) -> str:
    body = copy.deepcopy(fn.body)
    if normalize:
        body = [_Norm().visit(s) for s in body]
    return "\n".join(ast.dump(s) for s in body)


# ── 비교 ─────────────────────────────────────────────────────────────────────
def compare_fn(rel: str, name: str, bfn, bdec, afn, adec, rep: dict) -> None:
    loc = {"file": rel, "test": name}
    if fingerprint(bfn) != fingerprint(afn) or [ast.dump(d) for d in bfn.decorator_list] != \
            [ast.dump(d) for d in afn.decorator_list]:
        rep["_modified"] += 1
    for s in (Counter(fn_skips(afn, adec)) - Counter(fn_skips(bfn, bdec))).elements():
        rep["added_skips"].append({**loc, "skip": s})
    if has_early_return(afn) and not has_early_return(bfn):
        rep["added_skips"].append({**loc, "skip": "early return before assert"})
    ba, aa = asserts_of(bfn), asserts_of(afn)
    if len(aa) < len(ba):
        rep["removed_asserts"].append({**loc, "before": len(ba), "after": len(aa)})
    for b, a in pair_asserts(ba, aa):
        why = loosened_reason(b, a)
        change = {**loc, "before": trunc(ast.unparse(b)), "after": trunc(ast.unparse(a))}
        if why:
            rep["loosened_comparisons"].append({**loc, "reason": why, **change})
        elif literals(b) != literals(a):
            rep["changed_expected_values"].append(change)


def compare_file(rel: str, bt: ast.Module, at: ast.Module, rep: dict) -> None:
    btests, atests = collect_tests(bt), collect_tests(at)
    for s in (Counter(module_skips(at)) - Counter(module_skips(bt))).elements():
        rep["added_skips"].append({"file": rel, "test": "<module>", "skip": s})
    deleted = [k for k in btests if k not in atests]
    added = [k for k in atests if k not in btests]
    pairs = [(k, k) for k in btests if k in atests]
    for exact in (True, False):  # 정확히 같은 본문 → 식별자만 다른 본문 순으로 rename 매칭
        fp_added = {}
        for k in added:
            fp_added.setdefault(fingerprint(atests[k][0], not exact), k)
        for k in list(deleted):
            nk = fp_added.pop(fingerprint(btests[k][0], not exact), None)
            if nk is not None:
                deleted.remove(k)
                added.remove(nk)
                pairs.append((k, nk))
                rep["renamed_tests"].append({"file": rel, "before": k, "after": nk, "exact": exact})
    rep["deleted_tests"] += [{"file": rel, "test": k} for k in deleted]
    rep["_added_names"] += added
    rep["_deleted_names"] += deleted
    for bk, ak in pairs:
        compare_fn(rel, bk, *btests[bk], *atests[ak], rep)


def compare_config(rel: str, bf: Path | None, af: Path | None) -> dict | None:
    b = bf.read_text(encoding="utf-8", errors="replace").splitlines() if bf else []
    a = af.read_text(encoding="utf-8", errors="replace").splitlines() if af else []
    if b == a:
        return None
    diff = [ln for ln in difflib.unified_diff(b, a, n=0, lineterm="")
            if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
    sil = sorted({m for ln in diff for m in SILENCING_RE.findall(ln)})
    return {"file": rel, "changed_lines": len(diff), "silencing": sil}


def parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None


def audit(before: Path, after: Path, globs: list[str] | None = None) -> dict:
    """BEFORE/AFTER 디렉터리를 비교해 보고서 dict를 반환한다 (summary 포함)."""
    rep: dict = {k: [] for k in ORDER}
    rep.update(_modified=0, _added_names=[], _deleted_names=[])
    bt, bc = scan(before, globs)
    at, ac = scan(after, globs)
    compared = 0
    deleted_file_names: dict[str, set[str]] = {}
    for rel, bf in bt.items():
        btree = parse(bf)
        if rel not in at:
            rep["deleted_test_files"].append(rel)
            deleted_file_names[rel] = set(collect_tests(btree)) if btree else set()
            continue
        if btree is None:
            rep["unparseable_before"].append(rel)
            continue
        atree = parse(at[rel])
        if atree is None:
            rep["unparseable_after"].append(rel)
            continue
        compared += 1
        compare_file(rel, btree, atree, rep)
    for rel, af in at.items():
        if rel in bt:
            continue
        atree = parse(af)
        names = set(collect_tests(atree)) if atree else set()
        hints = [f"{n} test name(s) with {d}" for d, s in deleted_file_names.items() if (n := len(names & s))]
        if n := len(names & set(rep["_deleted_names"])):
            hints.append(f"{n} test name(s) deleted elsewhere")
        rep["added_test_files"].append(rel + (f" (shares {'; '.join(hints)})" if hints else ""))
    for rel in sorted(set(bc) | set(ac)):
        if c := compare_config(rel, bc.get(rel), ac.get(rel)):
            rep["config_changes"].append(c)
    counts = {k: len(rep[k]) for k in ORDER}
    counts["config_silencing"] = sum(1 for c in rep["config_changes"] if c["silencing"])
    counts["added_tests"] = len(rep["_added_names"])
    rep["summary"] = {
        "weakening": any(counts[k] for k in WEAKENING),
        "counts": {k: counts[k] for k in WEAKENING + ("renamed_tests", "added_tests")},
        "modified_tests": rep["_modified"], "files_compared": compared,
    }
    for k in [k for k in rep if k.startswith("_")]:
        del rep[k]
    return rep


def render(rep: dict) -> str:
    """indent 1의 JSON. 목록 항목은 한 줄씩, 10개 초과는 '+N more'로 접는다."""
    parts = [f' "summary": {json.dumps(rep["summary"], ensure_ascii=False)}']
    for k in ORDER:
        items = rep.get(k) or []
        if not items:
            continue
        shown = items[:CAP] + ([f"+{len(items) - CAP} more"] if len(items) > CAP else [])
        body = ",\n".join("  " + json.dumps(x, ensure_ascii=False) for x in shown)
        parts.append(f' "{k}": [\n{body}\n ]')
    return "{\n" + ",\n".join(parts) + "\n}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="BEFORE/AFTER 테스트 디렉터리를 비교해 테스트 약화를 감지한다.")
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--tests-glob", action="append", metavar="GLOB",
                    help="테스트 파일 glob(상대 경로 또는 파일명). 지정하면 기본 규칙을 대체. 반복 가능")
    ap.add_argument("--json", action="store_true", help="JSON 출력(기본값, 호환용)")
    ap.add_argument("--quiet", action="store_true", help="summary 한 줄만 출력")
    args = ap.parse_args(argv)
    if not args.before.is_dir() or not args.after.is_dir():
        print("error: before/after는 디렉터리여야 합니다", file=sys.stderr)
        return 2
    rep = audit(args.before, args.after, args.tests_glob)
    print(json.dumps(rep["summary"], ensure_ascii=False) if args.quiet else render(rep))
    return 1 if rep["summary"]["weakening"] else 0


if __name__ == "__main__":
    sys.exit(main())
