#!/usr/bin/env python3
"""G2 품질 실행기: evals.json의 각 케이스를 with/without × 모델 × 반복으로 claude -p 실행.

출력 레이아웃: <out>/quality/<eval-name>/<model>/<with|without>/rep-<k>/
  run.json, result.json, stream.jsonl, transcript.md, outputs/ (실행 후 프로젝트 사본)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import parse_frontmatter, run_claude, skill_invoked, transcript_md, usage_summary  # noqa: E402


def slug(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in s.lower()).strip("-")[:48]


def prepare_project(skill_dir: Path, ev: dict, with_skill: bool, name: str) -> Path:
    proj = Path(tempfile.mkdtemp(prefix=f"ge-{slug(name)}-"))
    fixture = ev.get("fixture")
    if fixture:
        src = (skill_dir / fixture).resolve()
        if not src.is_dir():
            raise FileNotFoundError(f"fixture 없음: {src}")
        shutil.copytree(src, proj, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', 'node_modules', '.git'))
    for f in ev.get("files", []) or []:
        src = (skill_dir / f).resolve()
        dst = proj / Path(f).name
        shutil.copytree(src, dst) if src.is_dir() else shutil.copy2(src, dst)
    (proj / ".claude").mkdir(exist_ok=True)
    if with_skill:
        skills_dir = proj / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / name).symlink_to(skill_dir.resolve(), target_is_directory=True)
    return proj


def one_run(skill_dir: Path, name: str, ev: dict, model: str, with_skill: bool, rep: int,
            run_dir: Path, timeout: int, max_turns: int) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    if (run_dir / "run.json").exists():
        return json.loads((run_dir / "run.json").read_text())  # 재실행 시 캐시
    proj = prepare_project(skill_dir, ev, with_skill, name)
    try:
        prompt = ev["prompt"] if with_skill else (ev.get("prompt_without") or ev["prompt"])
        res = run_claude(prompt, proj, model, timeout, max_turns)
        events, result = res["events"], res["result"]
        (run_dir / "stream.jsonl").write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events))
        (run_dir / "transcript.md").write_text(transcript_md(events, prompt))
        if result:
            (run_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
        out = run_dir / "outputs"
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(proj, out, ignore=shutil.ignore_patterns(".claude", "__pycache__", ".pytest_cache", "node_modules", ".git"), symlinks=True)
        info = {
            "eval_id": ev["id"], "prompt_used": prompt, "eval_name": ev.get("name") or f"eval-{ev['id']}",
            "model_alias": model, "config": "with_skill" if with_skill else "without_skill", "rep": rep,
            "skill_invoked": (skill_invoked(events, name) or prompt.lstrip().startswith(f"/{name}")) if with_skill else False,  # 슬래시 호출은 도구 호출 없이 전개된다
            "duration_ms": res["duration_ms"], "timed_out": res["timed_out"],
            "final_text": (result or {}).get("result", ""),
            **usage_summary(result),
        }
        if not result:
            info["stderr_tail"] = res["stderr"]
        (run_dir / "run.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
        return info
    finally:
        shutil.rmtree(proj, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models", default="haiku,opus")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--configs", default="with,without")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--max-turns", type=int, default=40)
    ap.add_argument("--only", default="", help="eval id 콤마 목록")
    a = ap.parse_args()

    skill_dir = Path(a.skill).resolve()
    name, _, _ = parse_frontmatter(skill_dir / "SKILL.md")
    evals = json.loads((skill_dir / "evals" / "evals.json").read_text())["evals"]
    if a.only:
        keep = {int(x) for x in a.only.split(",")}
        evals = [e for e in evals if e["id"] in keep]
    out = Path(a.out) / "quality"
    jobs = []
    for ev in evals:
        ename = slug(ev.get("name") or f"eval-{ev['id']}")
        for model in a.models.split(","):
            for cfg in a.configs.split(","):
                with_skill = cfg.strip() == "with"
                for rep in range(1, a.reps + 1):
                    run_dir = out / ename / model / ("with_skill" if with_skill else "without_skill") / f"rep-{rep}"
                    jobs.append((ev, model, with_skill, rep, run_dir))
    print(f"[quality] {len(jobs)} runs ({len(evals)} evals × {a.models} × {a.configs} × {a.reps})", file=sys.stderr)
    done = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(one_run, skill_dir, name, ev, m, w, r, d, a.timeout, a.max_turns): (ev, m, w, r) for ev, m, w, r, d in jobs}
        for fut in as_completed(futs):
            ev, m, w, r = futs[fut]
            done += 1
            try:
                info = fut.result()
                print(f"[quality] {done}/{len(jobs)} {info['eval_name']} {m} {'with' if w else 'without'} rep{r}: "
                      f"tokens={info.get('total_context_tokens')} turns={info.get('num_turns')} invoked={info.get('skill_invoked')}", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                print(f"[quality] {done}/{len(jobs)} FAILED {ev.get('name')} {m} {w} rep{r}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
