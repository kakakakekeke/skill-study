#!/usr/bin/env python3
"""세 게이트 eval 오케스트레이터.

python3 gate_eval.py --skill skills/<name> [--models haiku,opus] [--reps 3] [--skip-trigger] [--skip-quality] [--grader sonnet]
결과: <skill>/evals/results/<YYYY-MM-DD>/ (gitignore 대상) 에 report.md, summary.json
단계는 각각 캐시되므로 중단 후 같은 명령을 다시 실행하면 이어서 한다.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent


def sh(args: list[str]) -> None:
    print("+", " ".join(args), file=sys.stderr)
    subprocess.run(args, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--models", default="haiku,opus")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--grader", default="sonnet")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--max-turns", type=int, default=40)
    ap.add_argument("--skip-trigger", action="store_true")
    ap.add_argument("--skip-quality", action="store_true")
    ap.add_argument("--skip-grade", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--configs", default="with,without", help="quality_run.py --configs 와 같음")
    ap.add_argument("--hook", default=None, help="quality_run.py --hook 과 같음")
    a = ap.parse_args()
    skill = Path(a.skill).resolve()
    out = Path(a.out) if a.out else skill / "evals" / "results" / date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    user_invoked = "disable-model-invocation: true" in (skill / "SKILL.md").read_text().split("---")[1]
    intask = skill / "evals" / "trigger-intask.json"
    if not a.skip_trigger and not user_invoked and intask.exists():
        # 원칙 §2 "G1 측정 시점": 수행 중 G1이 판정, 시작 시점 라우팅은 참고치(trigger-router/)
        sh([py, str(HERE / "trigger_run.py"), "--skill", str(skill), "--out", str(out), "--models", a.models,
            "--eval-set", str(intask), "--workers", str(a.workers)])
        if (skill / "evals" / "trigger.json").exists():
            sh([py, str(HERE / "trigger_run.py"), "--skill", str(skill), "--out", str(out), "--models", a.models,
                "--out-name", "trigger-router"])
    elif not a.skip_trigger and not user_invoked and (skill / "evals" / "trigger.json").exists():
        sh([py, str(HERE / "trigger_run.py"), "--skill", str(skill), "--out", str(out), "--models", a.models])
    if not a.skip_quality and (skill / "evals" / "evals.json").exists():
        cmd = [py, str(HERE / "quality_run.py"), "--skill", str(skill), "--out", str(out), "--models", a.models,
               "--reps", str(a.reps), "--workers", str(a.workers), "--timeout", str(a.timeout), "--max-turns", str(a.max_turns)]
        if a.only:
            cmd += ["--only", a.only]
        cmd += ["--configs", a.configs]
        if a.hook:
            cmd += ["--hook", a.hook]
        sh(cmd)
    if not a.skip_grade and (out / "quality").exists():
        sh([py, str(HERE / "grade.py"), "--skill", str(skill), "--out", str(out), "--grader", a.grader, "--workers", str(a.workers)])
    sh([py, str(HERE / "report.py"), "--skill", str(skill), "--out", str(out)])


if __name__ == "__main__":
    main()
