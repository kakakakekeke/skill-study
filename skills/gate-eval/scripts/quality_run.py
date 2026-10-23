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


LEGACY = {"with": ("with_skill", {"skill"}), "without": ("without_skill", set())}


def parse_configs(spec: str) -> list[tuple[str, set[str]]]:
    """'with,without' (호환) 또는 'without=,skill=skill,hook=hook,both=skill+hook' → [(디렉터리 이름, 구성요소 집합)].
    구성요소: skill(.claude/skills/<name> 링크), hook(--hook settings.json 복사), siblings(같은 상위 디렉터리의 model-invoked 형제 스킬도 링크;
    실제 설치 환경의 경쟁을 재현한다). 이름만 있고 '='가 없으면 이름 자체를 구성요소로 해석한다."""
    out = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        if item in LEGACY:
            out.append(LEGACY[item]); continue
        name, _, comps = item.partition("=")
        comps = {c for c in comps.split("+") if c} if _ else ({name} if name in ("skill", "hook", "siblings") else set())
        bad = comps - {"skill", "hook", "siblings"}
        if bad:
            raise ValueError(f"알 수 없는 구성요소 {bad} (skill|hook|siblings)")
        out.append((name, comps))
    return out


def prepare_project(skill_dir: Path, ev: dict, comps: set[str], name: str, hook_settings: Path | None) -> Path:
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
    if "skill" in comps:
        skills_dir = proj / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / name).symlink_to(skill_dir.resolve(), target_is_directory=True)
    if "siblings" in comps:
        skills_dir = proj / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        for d in sorted(skill_dir.resolve().parent.iterdir()):
            md = d / "SKILL.md"
            if d.name == name or not md.exists() or "disable-model-invocation: true" in md.read_text().split("---")[1]:
                continue
            (skills_dir / d.name).symlink_to(d, target_is_directory=True)
    if "hook" in comps:
        if not hook_settings:
            raise ValueError("hook 구성요소에는 --hook <settings.json>이 필요하다")
        # claude -p는 --setting-sources project로 돌므로 프로젝트 settings.json의 훅이 적용된다 (2026-10-23 확인).
        txt = hook_settings.read_text().replace("${SKILL_DIR}", str(skill_dir.resolve()))
        (proj / ".claude" / "settings.json").write_text(txt)
    return proj


def hook_blocks(events: list[dict]) -> int:
    """훅이 막은 횟수: is_error인 tool_result 중 내용에 'hook'이 있는 것(PreToolUse) + 'Stop hook feedback' 사용자 메시지(Stop)."""
    n = 0
    for ev in events:
        if ev.get("type") != "user":
            continue
        content = ev.get("message", {}).get("content", [])
        if isinstance(content, str):
            n += content.startswith("Stop hook feedback")
            continue
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").startswith("Stop hook feedback"):
                n += 1
            if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("is_error"):
                body = c.get("content")
                if isinstance(body, list):
                    body = "\n".join(x.get("text", "") for x in body if isinstance(x, dict))
                if "hook" in str(body or "").lower():
                    n += 1
    return n


def one_run(skill_dir: Path, name: str, ev: dict, model: str, cfg: tuple[str, set[str]], rep: int,
            run_dir: Path, timeout: int, max_turns: int, hook_settings: Path | None) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    if (run_dir / "run.json").exists():
        return json.loads((run_dir / "run.json").read_text())  # 재실행 시 캐시
    cfg_name, comps = cfg
    with_skill = "skill" in comps
    proj = prepare_project(skill_dir, ev, comps, name, hook_settings)
    try:
        prompt = ev["prompt"] if with_skill else (ev.get("prompt_without") or ev["prompt"])
        res = run_claude(prompt, proj, model, timeout, max_turns, persist="hook" in comps)
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
            "model_alias": model, "config": cfg_name, "components": sorted(comps), "rep": rep,
            "hook_blocks": hook_blocks(events) if "hook" in comps else 0,
            "hook_messages": [e.get("content") for e in events if e.get("type") == "system" and e.get("subtype") == "informational"] if "hook" in comps else [],
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
    ap.add_argument("--models", default="haiku,sonnet")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--configs", default="with,without", help="예: with,without | without=,skill=skill,hook=hook,both=skill+hook")
    ap.add_argument("--hook", default=None, help="hook 구성요소용 settings.json (${SKILL_DIR} 치환, 임시 프로젝트 .claude/settings.json으로 복사)")
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
    out.mkdir(parents=True, exist_ok=True)
    configs = parse_configs(a.configs)
    hook_settings = Path(a.hook).resolve() if a.hook else None
    # 조건 정의를 결과 디렉터리에 남긴다 (report.py가 기준선=구성요소 없는 조건을 찾는 데 쓴다). 기존 항목과 병합.
    cfg_file = out / "configs.json"
    known = json.loads(cfg_file.read_text()) if cfg_file.exists() else {}
    known.update({n: sorted(c) for n, c in configs})
    cfg_file.write_text(json.dumps(known, ensure_ascii=False, indent=1))
    jobs = []
    for ev in evals:
        ename = slug(ev.get("name") or f"eval-{ev['id']}")
        for model in a.models.split(","):
            for cfg in configs:
                for rep in range(1, a.reps + 1):
                    run_dir = out / ename / model / cfg[0] / f"rep-{rep}"
                    jobs.append((ev, model, cfg, rep, run_dir))
    print(f"[quality] {len(jobs)} runs ({len(evals)} evals × {a.models} × {[c[0] for c in configs]} × {a.reps})", file=sys.stderr)
    done = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(one_run, skill_dir, name, ev, m, c, r, d, a.timeout, a.max_turns, hook_settings): (ev, m, c, r) for ev, m, c, r, d in jobs}
        for fut in as_completed(futs):
            ev, m, c, r = futs[fut]
            done += 1
            try:
                info = fut.result()
                print(f"[quality] {done}/{len(jobs)} {info['eval_name']} {m} {c[0]} rep{r}: "
                      f"tokens={info.get('total_context_tokens')} turns={info.get('num_turns')} invoked={info.get('skill_invoked')} hook_blocks={info.get('hook_blocks')}", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                print(f"[quality] {done}/{len(jobs)} FAILED {ev.get('name')} {m} {c[0]} rep{r}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
