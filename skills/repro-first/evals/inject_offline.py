#!/usr/bin/env python3
"""주입 훅 패턴의 오프라인 평가(모델 호출 없음). trigger.json을 train/test(seed 42)로 나누고 진단 문항을 별도 test로 본다.
패턴은 train만 보고 만든다. 사용: python3 evals/inject_offline.py"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "hooks"))
sys.path.insert(0, str(HERE.parent.parent / "gate-eval" / "scripts"))
from inject_trigger import classify  # noqa: E402
from trigger_run import split_eval_set  # noqa: E402

t = json.loads((HERE / "trigger.json").read_text())
train, test = split_eval_set(t, 0.4)
diag = json.loads((HERE / "trigger-intask-diag.json").read_text())["items"]
for name, rows in (("train", train), ("test", test), ("diag", diag)):
    fire = [r for r in rows if r["should_trigger"]]; no = [r for r in rows if not r["should_trigger"]]
    miss = [r["query"][:90] for r in fire if not classify(r["query"])]
    over = [r["query"][:90] for r in no if classify(r["query"])]
    print(f"{name}: recall {len(fire)-len(miss)}/{len(fire)}  false-positive {len(over)}/{len(no)}")
    for q in miss: print("   miss:", q.replace("\n", " "))
    for q in over: print("   over:", q.replace("\n", " "))
