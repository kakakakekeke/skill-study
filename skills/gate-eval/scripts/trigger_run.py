#!/usr/bin/env python3
"""G1 트리거 측정 (자체 구현).

방법: 임시 프로젝트에 이 저장소의 **모든 스킬**을 `.claude/skills/`로 링크해 서로 경쟁시키고(내장 스킬도 보임),
각 쿼리를 `claude -p`로 보낸다. 프로젝트는 비어 있으므로 시스템 프롬프트 한 줄로 "코드가 없으니 먼저 어떤 스킬을
쓸지 결정해 Skill 도구로 호출하거나 NONE이라 답하라"고 한다. 대상 스킬이 Skill 도구로 호출되면 트리거.
skill-creator의 run_eval(첫 도구가 Skill이어야 함, description만 노출)보다 실제 로딩 경로에 가깝고, 라우팅 결정만 잰다.

입력: <skill>/evals/trigger.json = [{"query": ..., "should_trigger": true|false}, ...]
출력: <out>/trigger/<model>.json, <out>/trigger/summary.json
train/test는 skill-creator의 split_eval_set(seed 42)과 같은 분할(없으면 자체 구현)로 나눠 보고한다.

수행 중 모드(원칙 §2 "G1 측정 시점"): 문항 파일이 {"reason": ..., "items": [{"query", "should_trigger", "fixture"}]}
형식이면 문항마다 fixture를 임시 프로젝트로 복사하고 같은 경쟁 스킬을 링크한 채 과제를 실제로 수행시킨다(라우터 프롬프트 없음,
품질 실행과 같은 도구). 대상 스킬이 언제든 호출되면 발동이며, 그 순간 프로세스를 끝내 비용을 줄인다. `reason`(요청 문장에
발동 조건이 없다는 근거)은 측정 전에 적어야 하며 비어 있으면 거부한다.
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
from common import ALLOWED_TOOLS, clean_env, parse_frontmatter, skill_invoked  # noqa: E402
import subprocess  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402

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


def one_in_task(query: str, fixture: Path, competitors: list[Path], model: str, skill_name: str,
                timeout: int, max_turns: int, settings_text: str | None = None) -> dict:
    """fixture에서 과제를 실제로 수행시키고 대상 스킬 호출 여부를 본다. 호출되는 즉시 종료한다."""
    proj = Path(tempfile.mkdtemp(prefix="ge-intask-"))
    try:
        shutil.copytree(fixture, proj, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "node_modules", ".git"))
        sk = proj / ".claude" / "skills"
        sk.mkdir(parents=True)
        for d in competitors:
            (sk / d.name).symlink_to(d, target_is_directory=True)
        if settings_text:  # 훅 조건(예: 트리거 주입 훅). quality_run의 --hook과 같은 방식
            (proj / ".claude" / "settings.json").write_text(settings_text)
        cmd = ["claude", "-p", query, "--model", model, "--output-format", "stream-json", "--verbose",
               "--no-session-persistence", "--setting-sources", "project", "--strict-mcp-config",
               "--max-turns", str(max_turns), "--allowedTools", ALLOWED_TOOLS]
        proc = subprocess.Popen(cmd, cwd=proj, env=clean_env(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        timer = threading.Timer(timeout, proc.kill)  # 출력 없이 멈춰도 끝나게
        timer.start()
        t0, skills_called, triggered, turns, subtype = time.time(), [], False, 0, None
        assert proc.stdout is not None
        for line in proc.stdout:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "result":
                subtype = ev.get("subtype")
            if ev.get("type") == "assistant":
                turns += 1
                for c in ev["message"].get("content", []):
                    if c.get("type") == "tool_use" and c.get("name") == "Skill":
                        skills_called.append(str(c["input"].get("skill", "")))
                if skill_invoked([ev], skill_name):
                    triggered = True
                    break
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        timer.cancel()
        timed_out = not triggered and time.time() - t0 >= timeout
        return {"triggered": triggered, "chosen": ",".join(skills_called) or "NONE", "turns": turns,
                "timed_out": timed_out, "duration_s": round(time.time() - t0, 1), "result_subtype": subtype}
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", default="haiku,sonnet")
    ap.add_argument("--runs-per-query", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--skills-root", default=None, help="경쟁시킬 스킬들의 상위 디렉터리 (기본: 대상 스킬의 부모)")
    ap.add_argument("--eval-set", default=None, help="문항 파일 (기본: <skill>/evals/trigger.json)")
    ap.add_argument("--holdout", type=float, default=0.4, help="test 비율. description을 고친 뒤 새 문항만 돌릴 때는 1.0")
    ap.add_argument("--out-name", default="trigger", help="결과 하위 디렉터리 이름 (수행 중 판정과 라우터 참고치를 나눌 때)")
    ap.add_argument("--max-turns", type=int, default=30, help="수행 중 모드 전용")
    ap.add_argument("--hook", default=None, help="수행 중 모드 전용: 임시 프로젝트 .claude/settings.json으로 복사할 훅 설정(${SKILL_DIR} 치환)")
    a = ap.parse_args()

    skill_dir = Path(a.skill).resolve()
    name, desc, _ = parse_frontmatter(skill_dir / "SKILL.md")
    eval_path = Path(a.eval_set).resolve() if a.eval_set else skill_dir / "evals" / "trigger.json"
    raw = json.loads(eval_path.read_text())
    in_task = isinstance(raw, dict)
    if in_task:
        reason = (raw.get("reason") or "").strip()
        if not reason:
            sys.exit(f"수행 중 G1에는 측정 전에 적은 reason이 필요하다: {eval_path}")
        eval_set = raw["items"]
        for e in eval_set:
            if not (skill_dir / e["fixture"]).is_dir():
                sys.exit(f"fixture 없음: {e['fixture']}")
        if a.timeout == 120:
            a.timeout = 600  # 라우터 기본값은 수행에 너무 짧다
    else:
        eval_set = raw
    train, test = split_eval_set(eval_set, a.holdout)
    test_q = {q["query"] for q in test}
    out = Path(a.out).resolve() / a.out_name
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
    comp_dirs = [root / c for c in competitors]
    settings_text = Path(a.hook).read_text().replace("${SKILL_DIR}", str(skill_dir)) if a.hook else None
    method = (f"in-task (fixture per query, all repo skills linked, full tools, max-turns {a.max_turns}, stop on invoke)"
              if in_task else "router-decision (all repo skills linked, empty project, Skill-only)")
    if a.hook:
        method += f", hook {Path(a.hook).name}"
    summary = {"skill": name, "description": desc, "method": method, "in_task": in_task, "hook": a.hook,
               "reason": raw.get("reason") if in_task else None,
               "competitors": competitors, "runs_per_query": a.runs_per_query, "eval_set": str(eval_path), "holdout": a.holdout,
               "n_train": len(train), "n_test": len(test), "models": {}}
    try:
        for model in a.models.split(","):
            cached = out / f"{model}.json"
            if cached.exists():
                res = json.loads(cached.read_text())
            else:
                print(f"[trigger] {model}: {len(eval_set)} queries × {a.runs_per_query}", file=sys.stderr)
                rows = {i: {"query": e["query"], "should_trigger": e["should_trigger"], "chosen": [], "triggers": 0, "runs": 0, "detail": []} for i, e in enumerate(eval_set)}
                with ThreadPoolExecutor(max_workers=a.workers) as ex:
                    if in_task:
                        futs = {ex.submit(one_in_task, e["query"], (skill_dir / e["fixture"]).resolve(), [d.resolve() for d in comp_dirs],
                                          model, name, a.timeout, a.max_turns, settings_text): i
                                for i, e in enumerate(eval_set) for _ in range(a.runs_per_query)}
                    else:
                        futs = {ex.submit(one, e["query"], proj, model, name, a.timeout): i for i, e in enumerate(eval_set) for _ in range(a.runs_per_query)}
                    for f in as_completed(futs):
                        r = f.result(); i = futs[f]
                        rows[i]["runs"] += 1; rows[i]["triggers"] += int(r["triggered"]); rows[i]["chosen"].append(r["chosen"])
                        if in_task:
                            rows[i]["detail"].append({k: r[k] for k in ("turns", "duration_s", "timed_out", "result_subtype")})
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
