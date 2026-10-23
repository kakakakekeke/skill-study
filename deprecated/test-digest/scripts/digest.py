#!/usr/bin/env python3
"""Condense noisy test/build/CI output to the lines that explain a failure.

Usage:
  <command> 2>&1 | python3 digest.py            # pipe
  python3 digest.py ci.log [--lines 40]         # file
  python3 digest.py --format pytest ...         # force a format (pytest|jest|go|cargo|tsc|generic)

Exit code: 1 if failures were detected, 0 otherwise. Prints at most --lines lines.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, OrderedDict

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z?\s*")  # GitHub Actions timestamps


def clean(lines: list[str]) -> list[str]:
    return [TS.sub("", ANSI.sub("", ln)).rstrip("\n") for ln in lines]


def detect(lines: list[str]) -> str:
    text = "\n".join(lines[-400:]) + "\n" + "\n".join(lines[:200])
    if re.search(r"^=+ .*(passed|failed|error).* =+$|^FAILED .*::|^E\s{3}", text, re.M):
        return "pytest"
    if re.search(r"^(PASS|FAIL) .*\.(test|spec)\.[jt]sx?|^Tests:\s+\d|^\s*[✕×] |^\s*● ", text, re.M):
        return "jest"
    if re.search(r"^--- (FAIL|PASS): |^FAIL\s+\S+\s+[\d.]+s|^ok\s+\S+\s+[\d.]+s", text, re.M):
        return "go"
    if re.search(r"^test result: |^---- \S+ stdout ----|^test \S+ \.\.\. (ok|FAILED)", text, re.M):
        return "cargo"
    if re.search(r"^\S+\(\d+,\d+\): error TS\d+", text, re.M):
        return "tsc"
    return "generic"


def pytest_digest(lines: list[str]) -> list[str]:
    out: list[str] = []
    summary = [ln for ln in lines if re.match(r"^=+ .*(passed|failed|error|no tests ran).* =+$", ln)]
    out += summary[-1:] or ["(no pytest summary line found)"]
    short = [ln for ln in lines if re.match(r"^(FAILED|ERROR) \S+", ln)]
    # 실패 블록: "____ test_name ____" 부터 다음 블록/섹션까지
    blocks: "OrderedDict[str, list[str]]" = OrderedDict()
    cur = None
    for ln in lines:
        m = re.match(r"^_{3,} (.+?) _{3,}$", ln)
        if m:
            cur = m.group(1).strip()
            blocks[cur] = []
            continue
        if re.match(r"^={3,} .* ={3,}$|^-{3,} .* -{3,}$", ln):
            cur = None
            continue
        if cur is not None:
            blocks[cur].append(ln)
    if short:
        out.append(f"failures ({len(short)}):")
    for name, body in blocks.items():
        err = [b for b in body if b.startswith("E ")][:4]
        loc = [b for b in body if re.match(r"^\S+\.py:\d+: ", b)]
        out.append(f"- {name}")
        out += [f"    {e}" for e in err]
        if loc:
            out.append(f"    at {loc[-1]}")
    if not blocks:
        out += [f"- {s}" for s in short[:15]]
    warn = [ln for ln in lines if re.match(r"^=+ warnings summary =+$", ln)]
    if warn:
        kinds = Counter(re.sub(r"^.*/", "", re.sub(r":\d+:", ":N:", ln.strip()))[:90] for ln in lines if re.search(r"Warning:", ln) and not ln.startswith("E "))
        out.append(f"warnings: {sum(kinds.values())} ({len(kinds)} distinct); top: " + "; ".join(k for k, _ in kinds.most_common(2)))
    return out


def jest_digest(lines: list[str]) -> list[str]:
    out = [ln for ln in lines if re.match(r"^(Tests|Test Suites|Test Files):\s", ln)][-2:]
    fails = [ln for ln in lines if re.match(r"^\s*FAIL\s+\S", ln)]
    out += [f"failing files ({len(fails)}):"] + [f"- {f.strip()}" for f in fails[:10]] if fails else []
    cur, blocks = None, OrderedDict()
    for ln in lines:
        m = re.match(r"^\s*● (.+)$", ln)
        if m and "Console" not in m.group(1):
            cur = m.group(1).strip()
            blocks.setdefault(cur, [])
            continue
        if cur and ln.strip():
            blocks[cur].append(ln)
    for name, body in list(blocks.items())[:12]:
        out.append(f"- {name}")
        keep = [b.strip() for b in body if re.search(r"Error|expect\(|Expected|Received|at .*\.[jt]sx?:\d+", b)][:4]
        out += [f"    {k}" for k in keep]
    return out


def go_digest(lines: list[str]) -> list[str]:
    out = [ln for ln in lines if re.match(r"^(FAIL|ok)\s+\S+", ln)][-8:]
    fails = [ln for ln in lines if ln.startswith("--- FAIL: ")]
    out.append(f"failing tests ({len(fails)}):")
    for i, ln in enumerate(lines):
        if ln.startswith("--- FAIL: "):
            out.append(f"- {ln[len('--- FAIL: '):]}")
            out += [f"    {m.strip()}" for m in lines[i + 1:i + 6] if re.match(r"^\s+\S+\.go:\d+: ", m)][:3]
    panics = [ln for ln in lines if "panic:" in ln]
    out += [f"panic: {p.strip()[:160]}" for p in panics[:3]]
    return out


def cargo_digest(lines: list[str]) -> list[str]:
    out = [ln for ln in lines if ln.startswith("test result:")][-1:]
    fails = [re.sub(r" \.\.\. FAILED$", "", ln[len("test "):]) for ln in lines if re.match(r"^test \S+ \.\.\. FAILED$", ln)]
    out.append(f"failing tests ({len(fails)}):")
    for name in fails[:12]:
        out.append(f"- {name}")
        try:
            i = lines.index(f"---- {name} stdout ----")
            out += [f"    {m.strip()[:160]}" for m in lines[i + 1:i + 12] if "panicked at" in m or "assertion" in m or "left:" in m or "right:" in m][:4]
        except ValueError:
            pass
    errs = [ln for ln in lines if re.match(r"^error(\[E\d+\])?: ", ln)]
    if errs:
        out.append(f"compile errors ({len(errs)}):")
        out += [f"- {e[:160]}" for e in errs[:8]]
    return out


def tsc_digest(lines: list[str]) -> list[str]:
    errs = [ln for ln in lines if re.match(r"^\S+\(\d+,\d+\): error TS\d+", ln)]
    codes = Counter(re.search(r"error (TS\d+)", e).group(1) for e in errs)
    out = [f"tsc: {len(errs)} errors in {len({e.split('(')[0] for e in errs})} files; by code: " + ", ".join(f"{c}×{n}" for c, n in codes.most_common(6))]
    out += [f"- {e[:170]}" for e in errs[:15]]
    return out


def generic_digest(lines: list[str]) -> list[str]:
    pat = re.compile(r"\b(error|fail(ed|ure)?|exception|traceback|panic|fatal|assert(ion)?)\b", re.I)
    noise = re.compile(r"^\s*(npm (warn|notice)|warning:|deprecat)", re.I)
    seen, out = set(), []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or noise.search(s) or not pat.search(s):
            continue
        key = re.sub(r"\d+", "N", s)[:100]
        if key in seen:
            continue
        seen.add(key)
        out.append(f"L{i+1}: {s[:170]}")
    out = out[:22]
    out.append("tail:")
    out += [f"  {ln[:170]}" for ln in lines[-8:] if ln.strip()]
    return out


DIGESTERS = {"pytest": pytest_digest, "jest": jest_digest, "go": go_digest, "cargo": cargo_digest, "tsc": tsc_digest, "generic": generic_digest}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--lines", type=int, default=40)
    ap.add_argument("--format", choices=list(DIGESTERS), default=None)
    a = ap.parse_args()
    raw = open(a.file, errors="replace").readlines() if a.file else sys.stdin.readlines()
    lines = clean(raw)
    fmt = a.format or detect(lines)
    body = DIGESTERS[fmt](lines)
    failed = any(re.search(r"\bfail|error|panic|FAILED", ln, re.I) for ln in body[:3]) or any(ln.startswith("- ") for ln in body)
    head = f"[digest] {len(lines)} lines in -> {min(len(body)+1, a.lines)} out, format={fmt}"
    if len(body) + 1 > a.lines:
        body = body[: a.lines - 2] + [f"… {len(body) - (a.lines - 2)} more lines; rerun with --lines {len(body)+1} or narrow the command to one failing test"]
    print("\n".join([head] + body))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
