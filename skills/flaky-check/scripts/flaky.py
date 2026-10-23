#!/usr/bin/env python3
"""Run a command N times and summarize pass/fail, failure rate, failure signatures, and timing.

  python3 flaky.py -n 20 [--timeout 120] [--keep-logs DIR] [--parallel 1] -- <command ...>

Exit code: 0 if every run passed, 2 if every run failed (deterministic), 1 if mixed (flaky).
"""
from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

NORMALIZE = [
    (re.compile(r"\x1b\[[0-9;]*[A-Za-z]"), ""),
    (re.compile(r"0x[0-9a-fA-F]+"), "0xHEX"),
    (re.compile(r"\b[0-9a-f]{7,40}\b"), "HASH"),
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ][\d:.]+Z?"), "TIMESTAMP"),
    (re.compile(r"(\.py|\.js|\.ts|\.go|\.rs|\.rb|\.java):\d+"), r"\1:N"),
    (re.compile(r"\d+(\.\d+)?"), "N"),
    (re.compile(r"\s+"), " "),
]
ERRORISH = re.compile(r"Error|Exception|FAILED|failed|assert|panic|Traceback|timeout|Timeout|refused|reset|killed", re.I)


def signature(stdout: str, stderr: str, code: int, timed_out: bool) -> tuple[str, str]:
    """(normalized key, example line). 마지막 에러성 줄을 우선, 없으면 마지막 비어있지 않은 줄."""
    if timed_out:
        return ("TIMEOUT", "TIMEOUT")
    lines = [ln.strip() for ln in (stderr + "\n" + stdout).splitlines() if ln.strip()]
    cand = [ln for ln in lines if ERRORISH.search(ln) and not ln.startswith(("=", "-", "_", "+", "~"))]
    # pytest 'E   ' 줄과 'FAILED x - msg' 줄 선호
    pref = [ln for ln in cand if ln.startswith("E ") or ln.startswith("FAILED ") or "Error" in ln or "Exception" in ln]
    pick = (pref or cand or lines or [f"exit {code}"])[-1]
    key = pick
    for pat, rep in NORMALIZE:
        key = pat.sub(rep, key)
    return (key[:140], pick[:160])


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (centre - half) / den), min(1.0, (centre + half) / den))


def run_once(i: int, cmd: list[str], timeout: float, logdir: str | None, keep_all: bool = False) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out, err, code, to = p.stdout, p.stderr, p.returncode, False
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        code, to = -1, True
    dt = time.time() - t0
    if logdir and (code != 0 or keep_all):
        with open(os.path.join(logdir, f"run-{i:03d}.{'fail' if code else 'pass'}.log"), "w") as f:
            f.write(f"# exit={code} timed_out={to} duration={dt:.2f}s\n--- stdout ---\n{out}\n--- stderr ---\n{err}")
    sig = signature(out, err, code, to) if code != 0 else None
    return {"i": i, "code": code, "dt": dt, "sig": sig, "timed_out": to}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--keep-logs", default=None, help="실패한 run의 stdout/stderr만 이 디렉터리에 남긴다")
    ap.add_argument("--keep-all-logs", action="store_true", help="통과한 run의 로그도 남긴다")
    ap.add_argument("--parallel", type=int, default=1, help="동시 실행 수. 병렬성 자체가 원인인지 보려면 올린다")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd:
        ap.error("command required after --")
    logdir = a.keep_logs
    if logdir:
        os.makedirs(logdir, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, a.parallel)) as ex:
        for r in ex.map(lambda i: run_once(i, cmd, a.timeout, logdir, a.keep_all_logs), range(1, a.n + 1)):
            results.append(r)
            print(f"\rrun {r['i']}/{a.n} {'FAIL' if r['code'] else 'ok'}   ", end="", file=sys.stderr, flush=True)
    print("", file=sys.stderr)
    results.sort(key=lambda r: r["i"])
    fails = [r for r in results if r["code"] != 0]
    k, n = len(fails), len(results)
    lo, hi = wilson(k, n)
    dts = [r["dt"] for r in results]
    print(f"[flaky-check] cmd: {' '.join(cmd)}")
    print(f"runs={n} pass={n-k} fail={k} fail_rate={k/n:.0%} (95% CI {lo:.0%}–{hi:.0%}) parallel={a.parallel}")
    print(f"duration s: min={min(dts):.2f} median={statistics.median(dts):.2f} max={max(dts):.2f}"
          + (f"  (fail runs median={statistics.median([r['dt'] for r in fails]):.2f})" if fails else ""))
    if k == 0:
        print("verdict: no failure reproduced in this environment (not proof of stability; try --parallel or CI-like conditions)")
    elif k == n:
        print("verdict: DETERMINISTIC failure (fails every run) — this is a bug, not flakiness")
    else:
        print(f"verdict: FLAKY — first failure at run {fails[0]['i']}; failing runs: {','.join(str(r['i']) for r in fails)[:80]}")
    if fails:
        groups: "OrderedDict[str, list]" = OrderedDict()
        for r in fails:
            groups.setdefault(r["sig"][0], []).append(r)
        print(f"failure signatures ({len(groups)} distinct):")
        for key, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            codes = sorted({r["code"] for r in rs})
            print(f"  {len(rs):>3}×  exit={codes}  {rs[0]['sig'][1]}")
    if logdir and fails:
        first = os.path.join(logdir, "run-%03d.fail.log" % fails[0]["i"])
        print(f"one log per failing run in {logdir}; start with: {first} (do not ls or cat them all)")
    elif logdir:
        print(f"no failing runs, nothing written to {logdir}")
    sys.exit(0 if k == 0 else 2 if k == n else 1)


if __name__ == "__main__":
    main()
