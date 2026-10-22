#!/usr/bin/env python3
"""G1 트리거 측정 (자체 구현).

방법: 임시 프로젝트에 이 저장소의 **모든 스킬**을 `.claude/skills/`로 링크해 서로 경쟁시키고(내장 스킬도 보임),
각 쿼리를 `claude -p`로 보낸다. 프로젝트는 비어 있으므로 시스템 프롬프트 한 줄로 "코드가 없으니 먼저 어떤 스킬을
쓸지 결정해 Skill 도구로 호출하거나 NONE이라 답하라"고 한다. 대상 스킬이 Skill 도구로 호출되면 트리거.
skill-creator의 run_eval(첫 도구가 Skill이어야 함, description만 노출)보다 실제 로딩 경로에 가깝고, 라우팅 결정만 잰다.

입력: <skill>/evals/trigger.json = [{"query": ..., "should_trigger": true|false}, ...]
출력: <out>/trigger/<model>.json, <out>/trigger/summary.json
train/test는 skill-creator의 split_eval_set(seed 42)과 같은 분할(없으면 자체 구현)로 나눠 보고한다.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import clean_env, parse_frontmatter  # noqa: E402
import subprocess  # noqa: E402

ROUTER_PROMPT = (
    "The user's repository is not mounted in this sandbox, so you cannot run or read their code. "
    "Your only job is the routing decision: if one of your available skills clearly applies to this request, "
    "invoke it with the Skill tool right now (just the invocation, nothing else). "
    "If no skill applies and you would handle the request directly with ordinary tools, reply with exactly: NONE. "
    "Do not call any other tool."
)


def split_eval_set(eval_set: list[dict], holdout: float, seed: int = 42):
    random.seed(seed)
    trig = [e for e in eval_set if e["should_trigger"]]
    no = [e for e in eval_set if not e["should_trigger"]]
    random.shuffle(trig); random.shuffle(no)
    nt, nn = max(1, int(len(trig) * holdout)), max(1, int(len(no) * holdout))
    return trig[nt:] + no[nn:], trig[:nt] + no[:nn]


def one(query: str, proj: Path, model: str, skill_name: str, timeout: int) -> dict:
    cmd = ["claude", "-p", query, "--model", model, "--output-format", "stream-json", "--verbose",
           "--no-session-persistence", "--setting-sources", "project", "--strict-mcp-config", "--max-turns", "2",
           "--allowedTools", "Skill", "--append-system-prompt", ROUTER_PROMPT]
    try:
        proc = subprocess.run(cmd, cwd=proj, env=clean_env(), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"triggered": False, "chosen": "TIMEOUT"}
    chosen, text = None, ""
    for line in proc.stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for c in ev["message"].get("content", []):
                if c.get("type") == "tool_use" and c.get("name") == "Skill" and chosen is None:
                    chosen = str(c["input"].get("skill", ""))
                elif c.get("type") == "text":
                    text += c["text"]
    if chosen is None:
        chosen = "NONE" if "NONE" in text else f"text:{text.strip()[:60]}"
    return {"triggered": chosen.split(":")[-1] == skill_name or chosen == skill_name, "chosen": chosen}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", default="haiku,opus")
    ap.add_argument("--runs-per-query", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--skills-root", default=None, help="경쟁시킬 스킬들의 상위 디렉터리 (기본: 대상 스킬의 부모)")
    a = ap.parse_args()

    skill_dir = Path(a.skill).resolve()
    name, desc, _ = parse_frontmatter(skill_dir / "SKILL.md")
    eval_set = json.loads((skill_dir / "evals" / "trigger.json").read_text())
    train, test = split_eval_set(eval_set, 0.4)
    test_q = {q["query"] for q in test}
    out = Path(a.out).resolve() / "trigger"
    out.mkdir(parents=True, exist_ok=True)

    proj = Path(tempfile.mkdtemp(prefix="ge-trigger-"))
    sk = proj / ".claude" / "skills"
    sk.mkdir(parents=True)
    root = Path(a.skills_root).resolve() if a.skills_root else skill_dir.parent
    competitors = []
    for d in sorted(root.iterdir()):
        if (d / "SKILL.md").exists():
            fm = (d / "SKILL.md").read_text().split("---")[1]
            if "disable-model-invocation: true" in fm:
                continue  # 모델에 노출되지 않는 스킬은 경쟁자가 아니다
            (sk / d.name).symlink_to(d.resolve(), target_is_directory=True)
            competitors.append(d.name)
    summary = {"skill": name, "description": desc, "method": "router-decision (all repo skills linked, empty project, Skill-only)",
               "competitors": competitors, "runs_per_query": a.runs_per_query, "n_train": len(train), "n_test": len(test), "models": {}}
    try:
        for model in a.models.split(","):
            cached = out / f"{model}.json"
            if cached.exists():
                res = json.loads(cached.read_text())
            else:
                print(f"[trigger] {model}: {len(eval_set)} queries × {a.runs_per_query}", file=sys.stderr)
                rows = {i: {"query": e["query"], "should_trigger": e["should_trigger"], "chosen": [], "triggers": 0, "runs": 0} for i, e in enumerate(eval_set)}
                with ThreadPoolExecutor(max_workers=a.workers) as ex:
                    futs = {ex.submit(one, e["query"], proj, model, name, a.timeout): i for i, e in enumerate(eval_set) for _ in range(a.runs_per_query)}
                    for f in as_completed(futs):
                        r = f.result(); i = futs[f]
                        rows[i]["runs"] += 1; rows[i]["triggers"] += int(r["triggered"]); rows[i]["chosen"].append(r["chosen"])
                results = []
                for r in rows.values():
                    rate = r["triggers"] / r["runs"] if r["runs"] else 0
                    results.append({**r, "trigger_rate": rate, "pass": (rate >= 0.5) == r["should_trigger"]})
                res = {"results": results}
                cached.write_text(json.dumps(res, ensure_ascii=False, indent=1))
            rows = res["results"]

            def agg(subset):
                st = [r for r in subset if r["should_trigger"]]
                snt = [r for r in subset if not r["should_trigger"]]
                return {
                    "n": len(subset), "pass": sum(1 for r in subset if r["pass"]),
                    "should_fire_recall": (sum(1 for r in st if r["pass"]) / len(st)) if st else None,
                    "should_not_fire_precision": (sum(1 for r in snt if r["pass"]) / len(snt)) if snt else None,
                    "over_trigger": [f"{r['query'][:80]} → {r['trigger_rate']:.2f}" for r in snt if not r["pass"]],
                    "under_trigger": [f"{r['query'][:80]} → {r['trigger_rate']:.2f} {sorted(set(r['chosen']))}" for r in st if not r["pass"]],
                }
            summary["models"][model] = {"all": agg(rows), "train": agg([r for r in rows if r["query"] not in test_q]), "test": agg([r for r in rows if r["query"] in test_q])}
            s = summary["models"][model]["all"]
            print(f"[trigger] {model}: {s['pass']}/{s['n']} recall={s['should_fire_recall']} precision={s['should_not_fire_precision']}", file=sys.stderr)
    finally:
        shutil.rmtree(proj, ignore_errors=True)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
