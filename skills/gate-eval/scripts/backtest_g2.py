#!/usr/bin/env python3
"""G2 판정 규칙 소급 비교: 현행(노이즈 바닥) vs 개정안(층화 순열 검정 + 셀별 회귀 + 최소 효과 크기).

2026-10-24 제안, 사용자가 반영하기로 결정(아직 principles.md·report.py 미반영). 개정안:
  품질형 = 층화 순열 검정(eval 안에서 조건 라벨 섞기, 20,000회, seed 42) 단측 p < 0.05 AND 순Δ ≥ 5%p AND 셀 회귀 0
  셀 회귀(eval×assertion) = 기준선 k/k 통과인데 처리 다수결 실패, 또는 단측 Fisher p < 0.05
  비용형 = 셀 회귀 0 AND 순Δ ≥ −5%p AND 품질 저하 순열 p ≥ 0.05 AND 출력 토큰 또는 시간 30% 이상 감소
  노이즈 바닥은 판정에서 빼고 참고치로. run 짝 비교 과반은 삭제(순열 검정과 중복).
2026-10-24 실행 결과(57건, 판정 변경 9건 — 처음엔 8건으로 잘못 셌다): docs/study/gate-eval-round-2/g2-rule-backtest-2026-10-24.txt

사용: python3 backtest_g2.py <results_dir> [<results_dir> ...]   (각 디렉터리 = gate-eval 결과 폴더, quality/ 포함)
결과 폴더의 configs.json/baseline 규칙은 report.py와 같다. 증분 측정 폴더는 '<dir>::<baseline>'으로 기준선을 지정한다.
"""
from __future__ import annotations

import itertools
import json
import math
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

MDE = 0.05        # 개정안: 최소 효과 크기(확연한 이득), 순Δ 5%p
ALPHA = 0.05      # 순열 검정·Fisher 유의수준 (단측)
NONINF = -0.05    # 비용형 비열등 한계
COST_CUT = 0.30
B = 20000
SEED = 42


def load_runs(qdir: Path) -> list[dict]:
    runs = []
    for g in qdir.rglob("grading.json"):
        if "/outputs/" in str(g):
            continue
        r = json.loads((g.parent / "run.json").read_text())
        r["grading"] = json.loads(g.read_text())
        runs.append(r)
    return runs


def majority(v):
    return sum(v) * 2 > len(v)


def flips(reps):
    n = len(reps[0]["grading"]["expectations"]); f = t = 0
    for a, b in itertools.combinations(reps, 2):
        for i in range(n):
            t += 1; f += a["grading"]["expectations"][i]["passed"] != b["grading"]["expectations"][i]["passed"]
    return f, t


def fisher_one_sided(a_pass, a_n, b_pass, b_n):
    """H1: b(기준선) 통과율 > a(처리) 통과율. 초기하 분포 단측 p."""
    total_pass = a_pass + b_pass; N = a_n + b_n
    def h(k):  # 처리 쪽 통과 수가 k일 확률
        return math.comb(total_pass, k) * math.comb(N - total_pass, a_n - k) / math.comb(N, a_n)
    lo = max(0, total_pass - b_n)
    return sum(h(k) for k in range(lo, a_pass + 1))


def pr(r):
    return r["grading"]["summary"]["pass_rate"]


def mean(x):
    x = [v for v in x if v is not None]
    return st.mean(x) if x else None


def evaluate(by, evals, t, base, cost):
    out = {}
    models = sorted({k[1] for k in by})
    for m in models:
        es = [e for e in evals if by.get((e, m, t)) and by.get((e, m, base))]
        if not es:
            continue
        # ---------- 현행
        nf, cf, ct, reg_old, items, deltas, pw_, pt_ = [], 0, 0, 0, 0, [], 0, 0
        for e in es:
            w, b = by[(e, m, t)], by[(e, m, base)]
            f, tt = flips(b); cf += f; ct += tt; nf.append(f / tt if tt else 0)
            n = len(w[0]["grading"]["expectations"]); items += n
            for i in range(n):
                mw = majority([r["grading"]["expectations"][i]["passed"] for r in w])
                mb = majority([r["grading"]["expectations"][i]["passed"] for r in b])
                reg_old += (mb and not mw)
            deltas.append(mean([pr(r) for r in w]) - mean([pr(r) for r in b]))
            for rw, rb in zip(sorted(w, key=lambda r: r["rep"]), sorted(b, key=lambda r: r["rep"])):
                pt_ += 1; pw_ += pr(rw) >= pr(rb)
        floor = max(mean(nf) or 0, 3 / ct if ct else 0)
        net = mean(deltas)
        reg_ok = reg_old / items <= floor + 1e-9
        c = cost.get(m, 0.0)
        if reg_ok and net > floor + 1e-9 and pw_ * 2 > pt_:
            old = "품질형"
        elif reg_ok and abs(net) <= floor + 1e-9 and c >= COST_CUT:
            old = "비용형"
        else:
            old = "실패"
        # ---------- 개정안
        # 셀별 회귀
        reg_new, reg_txt = 0, []
        for e in es:
            w, b = by[(e, m, t)], by[(e, m, base)]
            n = len(w[0]["grading"]["expectations"])
            for i in range(n):
                vw = [r["grading"]["expectations"][i]["passed"] for r in w]
                vb = [r["grading"]["expectations"][i]["passed"] for r in b]
                stable_pass = all(vb)
                maj_reg = majority(vb) and not majority(vw)
                p = fisher_one_sided(sum(vw), len(vw), sum(vb), len(vb))
                if (stable_pass and maj_reg) or p < ALPHA:
                    reg_new += 1; reg_txt.append(f"{e}#{i}")
        # 층화 순열 검정 (eval 안에서 라벨 섞기)
        rng = random.Random(SEED)
        pools = [([pr(r) for r in by[(e, m, t)]], [pr(r) for r in by[(e, m, base)]]) for e in es]
        obs = net
        ge = 0
        le = 0
        for _ in range(B):
            ds = []
            for a, bb in pools:
                allv = a + bb
                rng.shuffle(allv)
                ds.append(mean(allv[:len(a)]) - mean(allv[len(a):]))
            d = mean(ds)
            ge += d >= obs - 1e-12
            le += d <= obs + 1e-12
        p_up = (ge + 1) / (B + 1)      # 처리가 더 낫다
        p_down = (le + 1) / (B + 1)    # 처리가 더 나쁘다
        if reg_new == 0 and p_up < ALPHA and net >= MDE:
            new = "품질형"
        elif reg_new == 0 and p_down >= ALPHA and net >= NONINF and c >= COST_CUT:
            new = "비용형"
        else:
            new = "실패"
        out[m] = dict(net=net, floor=floor, reg_old=f"{reg_old}/{items}", old=old,
                      p_up=p_up, p_down=p_down, reg_new=reg_new, reg_txt=reg_txt, new=new, cost=c)
    return out


def main():
    rows = []
    for arg in sys.argv[1:]:
        d, _, base_override = arg.partition("::")
        d = Path(d)
        runs = load_runs(d / "quality")
        if not runs:
            continue
        by = defaultdict(list)
        for r in runs:
            by[(r["eval_name"], r["model_alias"], r["config"])].append(r)
        evals = sorted({k[0] for k in by})
        configs = sorted({k[2] for k in by})
        cfgf = d / "quality" / "configs.json"
        defs = json.loads(cfgf.read_text()) if cfgf.exists() else {}
        base = base_override or next((c for c in configs if defs.get(c) == []), "without_skill" if "without_skill" in configs else None)
        for t in [c for c in configs if c != base]:
            cost = {}
            for m in sorted({k[1] for k in by}):
                def avg(cfg, key):
                    return mean([r.get(key) for e in evals for r in by.get((e, m, cfg), [])])
                cuts = []
                for key in ("output_tokens", "duration_ms"):
                    a, b = avg(t, key), avg(base, key)
                    if a and b:
                        cuts.append(1 - a / b)
                cost[m] = max(cuts) if cuts else 0.0
            for m, v in evaluate(by, evals, t, base, cost).items():
                rows.append((str(d), t, base, m, v))
    for d, t, base, m, v in rows:
        name = d.split("/evals/results/")
        label = f"{Path(name[0]).name}/{name[1]}" if len(name) == 2 else d
        mark = "" if v["old"] == v["new"] else "  <== 변경"
        print(f"{label:45} {t:>8} vs {base:<13} {m:6} | 순Δ {v['net']*100:+6.1f}% 바닥 {v['floor']*100:4.1f}% 회귀(현행) {v['reg_old']:>5} → {v['old']:3} | "
              f"p↑ {v['p_up']:.4f} p↓ {v['p_down']:.3f} 회귀(개정) {v['reg_new']} 비용 {v['cost']*100:+.0f}% → {v['new']:3}{mark}")


if __name__ == "__main__":
    main()
