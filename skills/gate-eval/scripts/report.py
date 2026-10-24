#!/usr/bin/env python3
"""세 게이트 보고서: quality/·trigger/ 결과를 모아 report.md + summary.json.

G2 판정 규칙(조작적 정의, principles §2, 2026-10-24 개정):
  순Δ = eval별 (처리 평균 통과율 − 기준선 평균 통과율)의 평균.
  순열 검정 = 층화(eval 안에서만 run의 조건 라벨을 섞음), 20,000회, seed 42. 통계량은 순Δ.
    p↑ = 섞은 순Δ ≥ 관측 순Δ 비율(처리가 낫다), p↓ = 섞은 순Δ ≤ 관측 순Δ 비율(처리가 나쁘다). 단측, (k+1)/(B+1).
  셀 회귀(eval×assertion) = 기준선 k/k 통과인데 처리 다수결 실패, 또는 단측 Fisher p < 0.05(기준선 통과율 > 처리).
  품질형 통과 = p↑ < 0.05 AND 순Δ ≥ 5%p AND 셀 회귀 0.
  비용형 통과 = 셀 회귀 0 AND 순Δ ≥ −5%p AND p↓ ≥ 0.05 AND 출력 토큰 또는 소요 시간이 30% 이상 감소(COST_CUT).
  둘 다 아니면 실패. 5%p·α 0.05는 잠정. 이득(다수결 실패 → 통과) 수는 참고치.
  노이즈 바닥(기준선 반복 쌍의 뒤집힘률, max(관측, 3/N))은 판정에 쓰지 않는 참고치. 컨텍스트 토큰 비율도 턴 수에 비례하므로 참고치.
  검산: backtest_g2.py(개정안 소급 비교)와 같은 계산이다.
G3 (잠정): description ≈토큰, SKILL.md 줄 수(<200), 실행 토큰 비율 with/without. 공식 측정은 /skill-doctor. 비율 > 1.5이고 G2 실패면 실패.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import statistics as st
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import approx_tokens, claude_version, parse_frontmatter  # noqa: E402


def load_runs(qdir: Path) -> list[dict]:
    runs = []
    for g in qdir.rglob("grading.json"):
        rd = g.parent
        if "/outputs/" in str(g):  # 대상 스킬이 만든 산출물 안의 중첩 결과는 제외
            continue
        run = json.loads((rd / "run.json").read_text())
        run["grading"] = json.loads(g.read_text())
        run["path"] = str(rd)
        runs.append(run)
    return runs


def majority(vals: list[bool]) -> bool:
    return sum(vals) * 2 > len(vals)


def flip_counts(reps: list[dict]) -> tuple[int, int]:
    """같은 설정의 반복들 사이에서 assertion별 pass가 뒤집힌 쌍 수와 비교한 쌍 수."""
    if len(reps) < 2:
        return 0, 0
    n_items = len(reps[0]["grading"]["expectations"])
    flips = total = 0
    for a, b in itertools.combinations(reps, 2):
        for i in range(n_items):
            total += 1
            if a["grading"]["expectations"][i]["passed"] != b["grading"]["expectations"][i]["passed"]:
                flips += 1
    return flips, total


def flip_rate(reps: list[dict]) -> float | None:
    flips, total = flip_counts(reps)
    return flips / total if total else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else None


MDE = 0.05      # 품질형 최소 순Δ (잠정)
ALPHA = 0.05    # 순열 검정·Fisher 단측 유의수준 (잠정)
NONINF = -0.05  # 비용형 비열등 한계 (잠정)
PERM_B = 20000
PERM_SEED = 42


def fisher_worse(t_pass: int, t_n: int, b_pass: int, b_n: int) -> float:
    """단측 Fisher: H1 = 기준선 통과율 > 처리 통과율. 처리 통과 수가 관측 이하일 초기하 확률."""
    k_all, n_all = t_pass + b_pass, t_n + b_n
    lo = max(0, k_all - b_n)
    return sum(math.comb(k_all, k) * math.comb(n_all - k_all, t_n - k) for k in range(lo, t_pass + 1)) / math.comb(n_all, t_n)


def perm_test(pools: list[tuple[list[float], list[float]]], obs: float) -> tuple[float, float]:
    """층화 순열 검정. pools = eval별 (처리 통과율들, 기준선 통과율들). 반환 (p↑, p↓)."""
    rng = random.Random(PERM_SEED)
    ge = le = 0
    for _ in range(PERM_B):
        ds = []
        for t_, b_ in pools:
            allv = t_ + b_
            rng.shuffle(allv)
            ds.append(st.mean(allv[:len(t_)]) - st.mean(allv[len(t_):]))
        d = st.mean(ds)
        ge += d >= obs - 1e-12
        le += d <= obs + 1e-12
    return (ge + 1) / (PERM_B + 1), (le + 1) / (PERM_B + 1)


def sd(xs):
    xs = [x for x in xs if x is not None]
    return st.stdev(xs) if len(xs) > 1 else 0.0


def cut_txt(x):
    if x is None:
        return "—"
    return f"{abs(x)*100:.0f}% {'감소' if x >= 0 else '증가'}"


def fmt(x, pct=False, d=2):
    if x is None:
        return "—"
    return f"{x*100:.0f}%" if pct else f"{x:,.{d}f}" if isinstance(x, float) else f"{x:,}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--baseline", default=None, help="기준선 조건 이름(증분 측정: 예 sib). 없으면 구성요소 없는 조건")
    a = ap.parse_args()
    skill_dir = Path(a.skill).resolve()
    out = Path(a.out)
    name, desc, body = parse_frontmatter(skill_dir / "SKILL.md")
    hook_only = not (skill_dir / "SKILL.md").exists()
    fm = "" if hook_only else (skill_dir / "SKILL.md").read_text()
    user_invoked = not hook_only and "disable-model-invocation: true" in fm.split("---")[1]

    runs = load_runs(out / "quality") if (out / "quality").exists() else []
    by = defaultdict(list)  # (eval, model, config) -> runs
    for r in runs:
        by[(r["eval_name"], r["model_alias"], r["config"])].append(r)
    evals = sorted({k[0] for k in by})
    models = sorted({k[1] for k in by})

    grader_errors = [f"{r['eval_name']}/{r['model_alias']}/{r['config']}/rep{r['rep']}" for r in runs
                     if any("GRADER ERROR" in str(e.get("evidence", "")) for e in (r.get("grading") or {}).get("expectations", []))]
    lines = [f"# gate-eval 보고서: `{name}`", "",
             f"- 날짜: {date.today().isoformat()}", f"- Claude Code: {claude_version()}",
             f"- 모델(canonical): {sorted({m for r in runs for m in (r.get('models') or [])})}",
             f"- 호출 방식: {'user-invoked (description 상시 미로드)' if user_invoked else 'model-invoked'}", ""]
    if grader_errors:  # 채점기 형식 오류는 실패로 집계된다. grade.py를 다시 돌리면 이 run만 재채점한다
        lines += [f"> **경고: 채점기 오류 {len(grader_errors)} run** — 판정 전에 `grade.py`를 다시 실행할 것: " + ", ".join(grader_errors[:6]), ""]
    summary = {"skill": name, "date": date.today().isoformat(), "claude_code": claude_version(), "user_invoked": user_invoked, "g1": {}, "g2": {}, "g3": {}}

    # ---- G1
    lines += ["## G1 정확한 트리거", ""]
    tsum = out / "trigger" / "summary.json"
    if hook_only:
        lines += ["훅 전용(SKILL.md 없음): 트리거는 결정적이다. G1은 거짓양성으로 보며, G2 표의 오탐 fixture(`fp-*`) 회귀와 차단 횟수로 판정한다(원칙 §3.2).", ""]
        summary["g1"] = {"verdict": "n/a (hook)"}
    elif user_invoked:
        lines += ["user-invoked 스킬: description이 모델에 노출되지 않으므로 G1은 해당 없음(사람이 켠다).", ""]
        summary["g1"] = {"verdict": "n/a"}
    elif tsum.exists():
        t = json.loads(tsum.read_text())
        if t.get("in_task"):
            lines += ["**수행 중 G1** (원칙 §2 \"G1 측정 시점\"): fixture에서 과제를 실제로 수행시키고 대상 스킬이 언제든 호출되면 발동.",
                      f"- 측정 전 근거: {t.get('reason')}", f"- 경쟁 스킬: {', '.join(t.get('competitors', []))}", ""]
        lines += [f"쿼리 {t['n_train']+t['n_test']}개(train {t['n_train']}/test {t['n_test']}), 쿼리당 {t['runs_per_query']}회, 임계 0.5.", "",
                  "| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |", "|---|---|---|---|---|"]
        g1_ok = True
        for m, d in t["models"].items():
            for part in ("train", "test"):
                s = d[part]
                lines.append(f"| {m} | {part} | {s['pass']}/{s['n']} | {fmt(s['should_fire_recall'], True)} | {fmt(s['should_not_fire_precision'], True)} |")
            # 판정: test 구간에서 과잉·미발동 각각 ≤ 1건
            te = d["test"]
            if len(te["over_trigger"]) > 1 or len(te["under_trigger"]) > 1:
                g1_ok = False
            if te["over_trigger"] or te["under_trigger"] or d["train"]["over_trigger"] or d["train"]["under_trigger"]:
                lines.append("")
                for lab, key in (("과잉 트리거", "over_trigger"), ("미발동", "under_trigger")):
                    items = d["train"][key] + te[key]
                    if items:
                        lines.append(f"- {m} {lab}: " + " / ".join(f"`{q}`" for q in items))
                lines.append("")
        summary["g1"] = {"verdict": "pass" if g1_ok else "fail", "in_task": bool(t.get("in_task")), "models": t["models"]}
        lines += ["", f"**판정: {'통과' if g1_ok else '실패'}** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)", ""]
        rsum = out / "trigger-router" / "summary.json"
        if t.get("in_task") and rsum.exists():
            r = json.loads(rsum.read_text())
            lines += ["참고치: 시작 시점 라우팅 (판정에 쓰지 않음)", "", "| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |", "|---|---|---|---|---|"]
            for m, d in r["models"].items():
                for part in ("train", "test"):
                    s_ = d[part]
                    lines.append(f"| {m} | {part} | {s_['pass']}/{s_['n']} | {fmt(s_['should_fire_recall'], True)} | {fmt(s_['should_not_fire_precision'], True)} |")
            summary["g1"]["router_reference"] = r["models"]
            lines.append("")
    else:
        lines += ["trigger 결과 없음 (`evals/trigger.json` 또는 실행 누락).", ""]
        summary["g1"] = {"verdict": "missing"}

    # ---- 조건 정의: 기준선 = 구성요소 없는 조건(configs.json) 또는 legacy 'without_skill'. 나머지는 처리(treatment).
    cfg_file = out / "quality" / "configs.json"
    cfg_defs = json.loads(cfg_file.read_text()) if cfg_file.exists() else {}
    configs = sorted({k[2] for k in by})
    baseline = a.baseline if a.baseline in configs else next((c for c in configs if cfg_defs.get(c) == []), "without_skill" if "without_skill" in configs else None)
    treatments = [c for c in configs if c != baseline]
    treatments.sort(key=lambda c: (c != "with_skill", c))  # legacy with_skill을 1차 처리로
    primary = treatments[0] if treatments else None  # 스킬 게이트 판정에 쓰는 처리
    comp_txt = lambda c: "+".join(cfg_defs.get(c) or (["skill"] if c == "with_skill" else [])) or "없음"  # noqa: E731

    # ---- 비용 지표 (처리별, 기준선 대비; G2 비용형 판정과 G3가 함께 쓴다)
    COST_CUT = 0.30
    cost = {}  # (treatment, model) -> dict
    for t in treatments:
        for m in models:
            tw = [r.get("total_context_tokens") for e in evals for r in by.get((e, m, t), [])]
            two = [r.get("total_context_tokens") for e in evals for r in by.get((e, m, baseline), [])]
            ow = [r.get("output_tokens") for e in evals for r in by.get((e, m, t), [])]
            owo = [r.get("output_tokens") for e in evals for r in by.get((e, m, baseline), [])]
            dw = [r.get("duration_ms") for e in evals for r in by.get((e, m, t), [])]
            dwo = [r.get("duration_ms") for e in evals for r in by.get((e, m, baseline), [])]
            out_cut = 1 - mean(ow) / mean(owo) if mean(ow) and mean(owo) else None
            dur_cut = 1 - mean(dw) / mean(dwo) if mean(dw) and mean(dwo) else None
            cost[(t, m)] = {"context_tokens_with": mean(tw), "context_tokens_without": mean(two),
                            "ratio": (mean(tw) / mean(two)) if mean(tw) and mean(two) else None,
                            "output_tokens_with": mean(ow), "output_tokens_without": mean(owo), "output_cut": out_cut,
                            "duration_s_with": (mean(dw) or 0) / 1000, "duration_s_without": (mean(dwo) or 0) / 1000, "duration_cut": dur_cut}

    # ---- G2
    lines += ["## G2 확연한 이득 (품질 또는 비용)", ""]
    if not runs or baseline is None or not treatments:
        lines += ["quality 결과 없음 (또는 기준선/처리 조건 누락).", ""]
        summary["g2"] = {"verdict": "missing"}
    else:
        lines += [f"조건: 기준선 `{baseline}`(구성요소 {comp_txt(baseline)}) vs 처리 " + ", ".join(f"`{t}`({comp_txt(t)})" for t in treatments) + ". 각 처리는 기준선과 따로 비교한다.", ""]
        # 조건 나란히 표 (eval × 조건 통과율, 훅 차단 수)
        if len(treatments) > 1 or any(r.get("hook_blocks") for r in runs):
            lines += ["### 조건 나란히 (통과율 mean±sd / 훅 차단 평균)", "",
                      "| 모델 | eval | " + " | ".join(f"`{c}`" for c in [baseline] + treatments) + " |",
                      "|---|---|" + "---|" * (len(treatments) + 1)]
            for m in models:
                for e in evals:
                    cells = []
                    for c in [baseline] + treatments:
                        rs = by.get((e, m, c), [])
                        if not rs:
                            cells.append("—"); continue
                        pr = [r["grading"]["summary"]["pass_rate"] for r in rs]
                        hb = [r.get("hook_blocks") or 0 for r in rs]
                        cell = f"{fmt(mean(pr), True)}±{fmt(sd(pr), True)}"
                        if any(hb):
                            cell += f" / 차단 {mean(hb):.1f}"
                        cells.append(cell)
                    lines.append(f"| {m} | {e} | " + " | ".join(cells) + " |")
            lines.append("")
        g2_all = {}  # treatment -> model -> dict
        for t in treatments:
            g2 = {}
            lines += [f"### 처리 `{t}` (구성요소 {comp_txt(t)}) vs `{baseline}`", ""]
            for m in models:
                lines += [f"#### 모델 {m}", "", f"| eval | {t} 통과율 (mean±sd) | {baseline} 통과율 (mean±sd) | Δ | 뒤집힘({baseline}, 참고) | 뒤집힘({t}) | 이득 | 셀 회귀 | 스킬 미호출 |", "|---|---|---|---|---|---|---|---|---|"]
                nf_all, reg_all, gain_all, n_items_all, deltas, pools = [], 0, 0, 0, [], []
                osmosis = []
                cmp_total = cmp_flips = 0  # 기준선 반복 쌍 비교 횟수·뒤집힘 수 (노이즈 바닥의 표본 크기)
                has_skill = "skill" in (cfg_defs.get(t) or (["skill"] if t == "with_skill" else []))
                for e in evals:
                    w, wo = by.get((e, m, t), []), by.get((e, m, baseline), [])
                    if not w or not wo:
                        continue
                    pw = [r["grading"]["summary"]["pass_rate"] for r in w]
                    pwo = [r["grading"]["summary"]["pass_rate"] for r in wo]
                    nf = flip_rate(wo)
                    nfw = flip_rate(w)
                    f_, t_ = flip_counts(wo)
                    cmp_flips += f_; cmp_total += t_
                    n_items = len(w[0]["grading"]["expectations"])
                    gains, regs = [], []
                    for i in range(n_items):
                        vw = [r["grading"]["expectations"][i]["passed"] for r in w]
                        vwo = [r["grading"]["expectations"][i]["passed"] for r in wo]
                        txt = w[0]["grading"]["expectations"][i]["text"]
                        if majority(vw) and not majority(vwo):
                            gains.append(txt)
                        # 셀 회귀: 기준선 k/k 통과인데 처리 다수결 실패, 또는 단측 Fisher p < α
                        p_f = fisher_worse(sum(vw), len(vw), sum(vwo), len(vwo))
                        if (all(vwo) and not majority(vw)) or p_f < ALPHA:
                            regs.append(f"[처리 {sum(vw)}/{len(vw)}, 기준선 {sum(vwo)}/{len(vwo)}, Fisher p={p_f:.3f}] {txt}")
                    pools.append((pw, pwo))
                    not_invoked = [r for r in w if not r.get("skill_invoked")] if has_skill else []
                    osmosis += not_invoked
                    nf_all.append(nf); reg_all += len(regs); gain_all += len(gains); n_items_all += n_items
                    deltas.append(mean(pw) - mean(pwo))
                    inv_txt = f"{len(not_invoked)}/{len(w)}" if has_skill else "n/a"
                    lines.append(f"| {e} | {fmt(mean(pw), True)}±{fmt(sd(pw), True)} | {fmt(mean(pwo), True)}±{fmt(sd(pwo), True)} | {fmt(mean(pw)-mean(pwo), True)} | {fmt(nf, True)} | {fmt(nfw, True)} | {len(gains)} | {len(regs)} | {inv_txt} |")
                    for g_ in gains:
                        lines.append(f"|  | ↑ 이득: {g_[:90]} | | | | | | | |")
                    for r_ in regs:
                        lines.append(f"|  | ↓ 셀 회귀: {r_[:130]} | | | | | | | |")
                noise = mean(nf_all) or 0.0
                noise_ub = 3 / cmp_total if cmp_total else None
                floor = max(noise, noise_ub or 0.0)  # 참고치: 판정에 쓰지 않는다(2026-10-24 개정)
                reg_rate = reg_all / n_items_all if n_items_all else 0.0
                net = mean(deltas) or 0.0
                p_up, p_down = perm_test(pools, net) if pools else (1.0, 1.0)
                c = cost.get((t, m), {})
                cuts = [x for x in (c.get("output_cut"), c.get("duration_cut")) if x is not None]
                best_cut = max(cuts) if cuts else 0.0
                if reg_all == 0 and p_up < ALPHA and net >= MDE - 1e-9:
                    kind = "quality"
                elif reg_all == 0 and p_down >= ALPHA and net >= NONINF - 1e-9 and best_cut >= COST_CUT:
                    kind = "cost"
                else:
                    kind = None
                ok = kind is not None
                hb = [r.get("hook_blocks") or 0 for e in evals for r in by.get((e, m, t), [])]
                g2[m] = {"noise_floor_observed": noise, "noise_comparisons": cmp_total, "noise_flips": cmp_flips, "noise_floor_rule_of_three": noise_ub, "noise_floor": floor,
                         "regression_rate": reg_rate, "gains": gain_all, "regressions": reg_all, "net_delta": net,
                         "perm_p_up": p_up, "perm_p_down": p_down, "verdict": "pass" if ok else "fail", "kind": kind,
                         "output_cut": c.get("output_cut"), "duration_cut": c.get("duration_cut"),
                         "with_not_invoked": len(osmosis), "hook_blocks_mean": mean(hb) if hb else None}
                kind_txt = {"quality": "통과 (품질형)", "cost": "통과 (비용형)", None: "실패"}[kind]
                lines += ["", f"- 순Δ **{net*100:+.1f}%** (품질형 기준 ≥ {MDE*100:.0f}%p) · 층화 순열 p↑ **{p_up:.4f}** / p↓ {p_down:.4f} (α {ALPHA}) · 셀 회귀 **{reg_all}**/{n_items_all} · 이득 {gain_all}건",
                          f"- 참고: 노이즈 바닥 {fmt(floor, True)} = max(관측 {fmt(noise, True)} [뒤집힘 {cmp_flips}/{cmp_total}회 비교], 3/N {fmt(noise_ub, True) if noise_ub is not None else '-'}) — 판정에 쓰지 않음",
                          f"- 비용: 출력 토큰 {cut_txt(c.get('output_cut'))} · 시간 {cut_txt(c.get('duration_cut'))} (비용형 기준 {int(COST_CUT*100)}% 이상 감소)"]
                if has_skill:
                    lines.append(f"- 스킬 미호출 run: {len(osmosis)} (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)")
                if any(hb):
                    lines.append(f"- 훅 차단: run당 평균 {mean(hb):.1f}회 (PreToolUse 거부 + Stop hook feedback)")
                lines += [f"- **{m} 판정: {kind_txt}**", ""]
                if osmosis:
                    lines.append("  - 미호출 run 통과율: " + ", ".join(f"{r['eval_name']}/rep{r['rep']}={fmt(r['grading']['summary']['pass_rate'], True)}" for r in osmosis))
                    lines.append("")
            all_ok = all(v["verdict"] == "pass" for v in g2.values())
            kinds = {v["kind"] for v in g2.values()}
            overall_kind = "quality" if kinds == {"quality"} else ("cost" if all_ok else None)
            g2_all[t] = {"verdict": "pass" if all_ok else "fail", "kind": overall_kind, "models": g2}
            kind_txt = {"quality": "통과 (품질형)", "cost": "통과 (비용형: 품질 동률, 비용 확연히 감소)", None: "실패"}[overall_kind]
            lines += [f"**처리 `{t}` G2 판정: {kind_txt}**", ""]
        summary["g2"] = {**g2_all[primary], "baseline": baseline, "primary": primary, "treatments": g2_all}
        lines += [f"**G2 판정 (스킬 게이트 = 처리 `{primary}`): {({'quality': '통과 (품질형)', 'cost': '통과 (비용형)', None: '실패'})[g2_all[primary]['kind']]}** (모델마다. 품질형: 층화 순열 p↑ < {ALPHA} 그리고 순Δ ≥ {MDE*100:.0f}%p 그리고 셀 회귀 0. 비용형: 셀 회귀 0 그리고 순Δ ≥ {NONINF*100:.0f}%p 그리고 p↓ ≥ {ALPHA} 그리고 출력 토큰 또는 시간 {int(COST_CUT*100)}% 이상 감소)", ""]
        lines += ["회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.", ""]

    # ---- 수행 중 호출률 (보고용, 원칙 §2 "수행 중 호출률과 보완")
    dsum = out / "trigger-intask-diag" / "summary.json"
    if dsum.exists():
        d = json.loads(dsum.read_text())
        INTASK_MIN = 0.5
        lines += ["## 수행 중 호출률 (보고용, 판정 아님)", "",
                  f"fixture에서 형제 스킬({', '.join(d.get('competitors', []))})을 연결하고 과제를 실제로 수행시켰을 때의 호출률이다. "
                  f"실효 이득 = G2 순Δ × 수행 중 재현율. 재현율이 {int(INTASK_MIN*100)}% 미만이면 보완(① 명시적 호출 → ② 행동 검사 훅 → ③ 트리거 주입 훅)을 붙인다.", "",
                  "| 모델 | 수행 중 재현율 | 과잉 | G2 순Δ | 실효 이득 | 보완 |", "|---|---|---|---|---|---|"]
        prim = (summary.get("g2") or {}).get("models") or {}
        summary["intask"] = {}
        for m, v in d["models"].items():
            a = v["all"]
            rec = a["should_fire_recall"]
            net = (prim.get(m) or {}).get("net_delta")
            eff = net * rec if (net is not None and rec is not None) else None
            need = rec is not None and rec < INTASK_MIN
            lines.append(f"| {m} | {fmt(rec, True)} | {len(a['over_trigger'])} | {f'{net*100:+.1f}%' if net is not None else '-'} | "
                         f"{f'{eff*100:+.1f}%' if eff is not None else '-'} | {'**필요**' if need else '-'} |")
            summary["intask"][m] = {"recall": rec, "over": len(a["over_trigger"]), "net_delta": net, "effective_gain": eff, "needs_compensation": need}
        lines.append("")

    # ---- G3
    lines += ["## G3 과하지 않은 토큰", ""]
    desc_tok, body_lines = approx_tokens(desc), len(body.strip().splitlines())
    lines += [f"- description ≈ {desc_tok} 토큰 (근사; 상시 로드{'되지 않음' if user_invoked else '됨'})", f"- SKILL.md 본문 {body_lines}줄 (상한 200)"]
    g3 = {"description_tokens_approx": desc_tok, "body_lines": body_lines, "models": {}}
    ratio_bad = False
    for t in treatments:
        for m in models:
            c = cost[(t, m)]
            g3["models"][m if t == primary else f"{t}/{m}"] = c
            lines.append(f"- `{t}` {m}: 컨텍스트 토큰 {fmt(c['context_tokens_with'], d=0)} / 기준선 {fmt(c['context_tokens_without'], d=0)} (비율 {fmt(c['ratio'])}; 턴 수에 비례하는 참고치) · 출력 토큰 {fmt(c['output_tokens_with'], d=0)}/{fmt(c['output_tokens_without'], d=0)} · 시간 {fmt(c['duration_s_with'], d=0)}s/{fmt(c['duration_s_without'], d=0)}s")
            if t == primary and c["ratio"] and c["ratio"] > 1.5 and summary["g2"].get("models", {}).get(m, {}).get("verdict") != "pass":
                ratio_bad = True
    g3_ok = body_lines < 200 and not ratio_bad
    g3["verdict"] = "pass" if g3_ok else "fail"
    summary["g3"] = g3
    lines += ["", f"**G3 판정(잠정): {'통과' if g3_ok else '실패'}** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.", ""]

    verdicts = [summary["g1"].get("verdict"), summary["g2"].get("verdict"), summary["g3"].get("verdict")]
    final = "채택 가능" if all(v == "pass" or str(v).startswith("n/a") for v in verdicts) else "백로그 (미입증 게이트 있음)"
    summary["final"] = final
    lines += ["## 종합", "", "| G1 | G2 | G3 | 결론 |", "|---|---|---|---|", f"| {verdicts[0]} | {verdicts[1]} | {verdicts[2]} | **{final}** |", ""]
    (out / "report.md").write_text("\n".join(lines))
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    print(str(out / "report.md"))


if __name__ == "__main__":
    main()
