#!/usr/bin/env python3
"""세 게이트 보고서: quality/·trigger/ 결과를 모아 report.md + summary.json.

G2 판정 규칙(조작적 정의, principles §2):
  노이즈 바닥 = without 반복들 사이에서 같은 assertion의 통과/실패가 뒤집히는 비율(쌍 단위, eval×model 평균).
  회귀 = without 다수결 통과 → with 다수결 실패인 assertion. 회귀율 = 회귀 수 / assertion 수.
  이득 = 반대 방향.
  노이즈 바닥 = max(관측 뒤집힘률, 3/N). N = without 반복 쌍 비교 횟수. 0건 관측은 과소추정이므로 rule-of-three 상한을 하한으로.
  필수 = 모델마다 회귀율 ≤ 노이즈 바닥.
  품질형 통과 = 필수 AND 순Δ(평균 통과율 with − without) > 노이즈 바닥 AND rep 짝 비교에서 with ≥ without 과반.
  비용형 통과 = 필수 AND |순Δ| ≤ 노이즈 바닥(동률) AND 출력 토큰 또는 소요 시간이 30% 이상 감소(COST_CUT).
  둘 다 아니면 실패. 노이즈 바닥 안의 순Δ는 품질 이득이 아니다. 컨텍스트 토큰 비율은 턴 수에 비례하므로 참고치.
G3 (잠정): description ≈토큰, SKILL.md 줄 수(<200), 실행 토큰 비율 with/without. 공식 측정은 /skill-doctor. 비율 > 1.5이고 G2 실패면 실패.
"""
from __future__ import annotations

import argparse
import itertools
import json
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


def sd(xs):
    xs = [x for x in xs if x is not None]
    return st.stdev(xs) if len(xs) > 1 else 0.0


def fmt(x, pct=False, d=2):
    if x is None:
        return "—"
    return f"{x*100:.0f}%" if pct else f"{x:,.{d}f}" if isinstance(x, float) else f"{x:,}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    skill_dir = Path(a.skill).resolve()
    out = Path(a.out)
    name, desc, body = parse_frontmatter(skill_dir / "SKILL.md")
    fm = (skill_dir / "SKILL.md").read_text()
    user_invoked = "disable-model-invocation: true" in fm.split("---")[1]

    runs = load_runs(out / "quality") if (out / "quality").exists() else []
    by = defaultdict(list)  # (eval, model, config) -> runs
    for r in runs:
        by[(r["eval_name"], r["model_alias"], r["config"])].append(r)
    evals = sorted({k[0] for k in by})
    models = sorted({k[1] for k in by})

    lines = [f"# gate-eval 보고서: `{name}`", "",
             f"- 날짜: {date.today().isoformat()}", f"- Claude Code: {claude_version()}",
             f"- 모델(canonical): {sorted({m for r in runs for m in (r.get('models') or [])})}",
             f"- 호출 방식: {'user-invoked (description 상시 미로드)' if user_invoked else 'model-invoked'}", ""]
    summary = {"skill": name, "date": date.today().isoformat(), "claude_code": claude_version(), "user_invoked": user_invoked, "g1": {}, "g2": {}, "g3": {}}

    # ---- G1
    lines += ["## G1 정확한 트리거", ""]
    tsum = out / "trigger" / "summary.json"
    if user_invoked:
        lines += ["user-invoked 스킬: description이 모델에 노출되지 않으므로 G1은 해당 없음(사람이 켠다).", ""]
        summary["g1"] = {"verdict": "n/a"}
    elif tsum.exists():
        t = json.loads(tsum.read_text())
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
        summary["g1"] = {"verdict": "pass" if g1_ok else "fail", "models": t["models"]}
        lines += ["", f"**판정: {'통과' if g1_ok else '실패'}** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)", ""]
    else:
        lines += ["trigger 결과 없음 (`evals/trigger.json` 또는 실행 누락).", ""]
        summary["g1"] = {"verdict": "missing"}

    # ---- 비용 지표 (G2 비용형 판정과 G3가 함께 쓴다)
    COST_CUT = 0.30
    cost = {}
    for m in models:
        tw = [r.get("total_context_tokens") for e in evals for r in by.get((e, m, "with_skill"), [])]
        two = [r.get("total_context_tokens") for e in evals for r in by.get((e, m, "without_skill"), [])]
        ow = [r.get("output_tokens") for e in evals for r in by.get((e, m, "with_skill"), [])]
        owo = [r.get("output_tokens") for e in evals for r in by.get((e, m, "without_skill"), [])]
        dw = [r.get("duration_ms") for e in evals for r in by.get((e, m, "with_skill"), [])]
        dwo = [r.get("duration_ms") for e in evals for r in by.get((e, m, "without_skill"), [])]
        out_cut = 1 - mean(ow) / mean(owo) if mean(ow) and mean(owo) else None
        dur_cut = 1 - mean(dw) / mean(dwo) if mean(dw) and mean(dwo) else None
        cost[m] = {"context_tokens_with": mean(tw), "context_tokens_without": mean(two),
                   "ratio": (mean(tw) / mean(two)) if mean(tw) and mean(two) else None,
                   "output_tokens_with": mean(ow), "output_tokens_without": mean(owo), "output_cut": out_cut,
                   "duration_s_with": (mean(dw) or 0) / 1000, "duration_s_without": (mean(dwo) or 0) / 1000, "duration_cut": dur_cut}

    # ---- G2
    lines += ["## G2 확연한 이득 (품질 또는 비용)", ""]
    if not runs:
        lines += ["quality 결과 없음.", ""]
        summary["g2"] = {"verdict": "missing"}
    else:
        g2 = {}
        for m in models:
            lines += [f"### 모델 {m}", "", "| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |", "|---|---|---|---|---|---|---|---|---|"]
            nf_all, reg_all, gain_all, n_items_all, pair_wins, pair_total, deltas = [], 0, 0, 0, 0, 0, []
            osmosis = []
            cmp_total = cmp_flips = 0  # without 반복 쌍 비교 횟수·뒤집힘 수 (노이즈 바닥의 표본 크기)
            for e in evals:
                w, wo = by.get((e, m, "with_skill"), []), by.get((e, m, "without_skill"), [])
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
                    mw = majority([r["grading"]["expectations"][i]["passed"] for r in w])
                    mwo = majority([r["grading"]["expectations"][i]["passed"] for r in wo])
                    txt = w[0]["grading"]["expectations"][i]["text"]
                    if mw and not mwo:
                        gains.append(txt)
                    elif mwo and not mw:
                        regs.append(txt)
                for rw, rwo in zip(sorted(w, key=lambda r: r["rep"]), sorted(wo, key=lambda r: r["rep"])):
                    pair_total += 1
                    pair_wins += rw["grading"]["summary"]["pass_rate"] >= rwo["grading"]["summary"]["pass_rate"]
                not_invoked = [r for r in w if not r.get("skill_invoked")]
                osmosis += not_invoked
                nf_all.append(nf); reg_all += len(regs); gain_all += len(gains); n_items_all += n_items
                deltas.append(mean(pw) - mean(pwo))
                lines.append(f"| {e} | {fmt(mean(pw), True)}±{fmt(sd(pw), True)} | {fmt(mean(pwo), True)}±{fmt(sd(pwo), True)} | {fmt(mean(pw)-mean(pwo), True)} | {fmt(nf, True)} | {fmt(nfw, True)} | {len(gains)} | {len(regs)} | {len(not_invoked)}/{len(w)} |")
                for g_ in gains:
                    lines.append(f"|  | ↑ 이득: {g_[:90]} | | | | | | | |")
                for r_ in regs:
                    lines.append(f"|  | ↓ 회귀: {r_[:90]} | | | | | | | |")
            noise = mean(nf_all) or 0.0
            noise_ub = 3 / cmp_total if cmp_total else None  # 뒤집힘 0건일 때의 95% 상한(rule of three)
            floor = max(noise, noise_ub or 0.0)  # principles §2: 노이즈 바닥 = max(관측, 3/N)
            reg_rate = reg_all / n_items_all if n_items_all else 0.0
            net = mean(deltas) or 0.0
            consistent = pair_total and pair_wins * 2 > pair_total
            reg_ok = reg_rate <= floor + 1e-9
            c = cost.get(m, {})
            cuts = [x for x in (c.get("output_cut"), c.get("duration_cut")) if x is not None]
            best_cut = max(cuts) if cuts else 0.0
            if reg_ok and net > floor + 1e-9 and consistent:
                kind = "quality"
            elif reg_ok and abs(net) <= floor + 1e-9 and best_cut >= COST_CUT:
                kind = "cost"
            else:
                kind = None
            ok = kind is not None
            g2[m] = {"noise_floor_observed": noise, "noise_comparisons": cmp_total, "noise_flips": cmp_flips, "noise_floor_rule_of_three": noise_ub, "noise_floor": floor,
                     "regression_rate": reg_rate, "gains": gain_all, "regressions": reg_all, "net_delta": net,
                     "pair_wins": f"{pair_wins}/{pair_total}", "verdict": "pass" if ok else "fail", "kind": kind,
                     "output_cut": c.get("output_cut"), "duration_cut": c.get("duration_cut"),
                     "with_not_invoked": len(osmosis)}
            kind_txt = {"quality": "통과 (품질형)", "cost": "통과 (비용형)", None: "실패"}[kind]
            lines += ["", f"- 노이즈 바닥: **{fmt(floor, True)}** = max(관측 {fmt(noise, True)} [뒤집힘 {cmp_flips}/{cmp_total}회 비교], 3/N {fmt(noise_ub, True) if noise_ub is not None else '-'}) · 회귀율: {fmt(reg_rate, True)} ({reg_all}/{n_items_all}) · 이득 {gain_all}건 · 순Δ {net*100:+.1f}% · rep 짝 with≥without {pair_wins}/{pair_total}",
                      f"- 비용: 출력 토큰 {fmt(c.get('output_cut'), True) if c.get('output_cut') is not None else '-'} 감소 · 시간 {fmt(c.get('duration_cut'), True) if c.get('duration_cut') is not None else '-'} 감소 (비용형 기준 {int(COST_CUT*100)}% 이상)",
                      f"- with 설정에서 스킬 미호출 run: {len(osmosis)} (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)",
                      f"- **{m} 판정: {kind_txt}**", ""]
            if osmosis:
                lines.append("  - 미호출 run 통과율: " + ", ".join(f"{r['eval_name']}/rep{r['rep']}={fmt(r['grading']['summary']['pass_rate'], True)}" for r in osmosis))
                lines.append("")
        all_ok = all(v["verdict"] == "pass" for v in g2.values())
        kinds = {v["kind"] for v in g2.values()}
        overall_kind = "quality" if kinds == {"quality"} else ("cost" if all_ok else None)
        summary["g2"] = {"verdict": "pass" if all_ok else "fail", "kind": overall_kind, "models": g2}
        kind_txt = {"quality": "통과 (품질형)", "cost": "통과 (비용형: 품질 동률, 비용 확연히 감소)", None: "실패"}[overall_kind]
        lines += [f"**G2 판정: {kind_txt}** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 {int(COST_CUT*100)}% 이상 감소)", ""]
        lines += ["회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.", ""]

    # ---- G3
    lines += ["## G3 과하지 않은 토큰", ""]
    desc_tok, body_lines = approx_tokens(desc), len(body.strip().splitlines())
    lines += [f"- description ≈ {desc_tok} 토큰 (근사; 상시 로드{'되지 않음' if user_invoked else '됨'})", f"- SKILL.md 본문 {body_lines}줄 (상한 200)"]
    g3 = {"description_tokens_approx": desc_tok, "body_lines": body_lines, "models": {}}
    ratio_bad = False
    for m in models:
        c = cost[m]
        g3["models"][m] = c
        lines.append(f"- {m}: 컨텍스트 토큰 with {fmt(c['context_tokens_with'], d=0)} / without {fmt(c['context_tokens_without'], d=0)} (비율 {fmt(c['ratio'])}; 턴 수에 비례하는 참고치) · 출력 토큰 {fmt(c['output_tokens_with'], d=0)}/{fmt(c['output_tokens_without'], d=0)} · 시간 {fmt(c['duration_s_with'], d=0)}s/{fmt(c['duration_s_without'], d=0)}s")
        if c["ratio"] and c["ratio"] > 1.5 and summary["g2"].get("models", {}).get(m, {}).get("verdict") != "pass":
            ratio_bad = True
    g3_ok = body_lines < 200 and not ratio_bad
    g3["verdict"] = "pass" if g3_ok else "fail"
    summary["g3"] = g3
    lines += ["", f"**G3 판정(잠정): {'통과' if g3_ok else '실패'}** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.", ""]

    verdicts = [summary["g1"].get("verdict"), summary["g2"].get("verdict"), summary["g3"].get("verdict")]
    final = "채택 가능" if all(v in ("pass", "n/a") for v in verdicts) else "백로그 (미입증 게이트 있음)"
    summary["final"] = final
    lines += ["## 종합", "", f"| G1 | G2 | G3 | 결론 |", "|---|---|---|---|", f"| {verdicts[0]} | {verdicts[1]} | {verdicts[2]} | **{final}** |", ""]
    (out / "report.md").write_text("\n".join(lines))
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    print(str(out / "report.md"))


if __name__ == "__main__":
    main()
