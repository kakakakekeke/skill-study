#!/usr/bin/env python3
"""결정적 검사: fixture 대비 outputs/의 변경이 허용 범위 안인가.

사용: scope_diff.py <fixture 이름> <허용 명세>
  허용 명세: "shop/pricing.py:apply_discount;tests/test_pricing.py:*"
  - 파일:* 는 파일 전체 허용, 파일:f,g 는 그 최상위 함수·클래스의 변경만 허용(그 밖의 최상위 코드·import 변경은 초과).
  - 새로 생긴 tests/ 아래 파일은 허용(요청한 변경의 테스트). 캐시·빌드 산물은 무시.
출력: 변경 목록과 초과 항목 JSON. 초과가 없으면 exit 0, 있으면 exit 1.
RUN_DIR(기본 cwd)/outputs 를 본다.
"""
from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IGNORE_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".claude", ".git", "node_modules"}
IGNORE_SUFFIX = {".pyc"}


def files(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file() and not (set(p.relative_to(root).parts) & IGNORE_DIRS) and p.suffix not in IGNORE_SUFFIX:
            out[str(p.relative_to(root))] = p.read_bytes()
    return out


def units(src: str) -> dict[str, str]:
    """최상위 정의 이름 → 정규화된 소스. 정의 밖의 코드(import, 상수)는 '<module>'로 모은다."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {"<unparsable>": src}
    out, rest = {}, []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = ast.dump(node, include_attributes=False)
        else:
            rest.append(ast.dump(node, include_attributes=False))
    out["<module>"] = "\n".join(rest)
    return out


def main() -> int:
    fixture, spec = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
    base = HERE.parent / "fixtures" / fixture
    out = Path(os.environ.get("RUN_DIR", ".")) / "outputs"
    allowed: dict[str, set[str]] = {}
    for part in filter(None, spec.split(";")):
        f, _, names = part.partition(":")
        allowed[f] = set(filter(None, names.split(",")))
    a, b = files(base), files(out)
    changed, excess = [], []
    for f in sorted(set(a) | set(b)):
        if a.get(f) == b.get(f):
            continue
        kind = "added" if f not in a else "deleted" if f not in b else "modified"
        entry = {"file": f, "kind": kind}
        if kind == "modified" and f.endswith(".py"):
            ua, ub = units(a[f].decode()), units(b[f].decode())
            entry["units"] = sorted(n for n in set(ua) | set(ub) if ua.get(n) != ub.get(n))
        changed.append(entry)
        if f in allowed:
            names = allowed[f]
            if "*" in names or kind != "modified" or not f.endswith(".py"):
                continue
            extra = [u for u in entry.get("units", []) if u not in names]
            if extra:
                excess.append({"file": f, "units": extra})
        elif kind == "added" and f.startswith("tests/"):
            continue
        else:
            excess.append({"file": f, "kind": kind, "units": entry.get("units")})
    print(json.dumps({"changed": changed, "excess": excess}, ensure_ascii=False))
    return 1 if excess else 0


if __name__ == "__main__":
    sys.exit(main())
