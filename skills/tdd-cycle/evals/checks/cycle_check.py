#!/usr/bin/env python3
"""G2 assertion 하나를 판정한다: python3 cycle_check.py <fixture> <지표>. exit 0 = 통과.

tdd_trace.analyze 결과를 RUN_DIR/tdd_trace.json에 캐시해 assertion마다 다시 계산하지 않는다.
지표: cycles(≥3) · small_batch(사이클당 ≤3) · red_behavior(≥0.8) · honest(TDD 주장 ⇒ strict) ·
      accept(숨은 수용 테스트 전부) · suite_green(최종 스위트 통과) · coverage(≥0.9)
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tdd_trace import analyze  # noqa: E402

fixture, metric = sys.argv[1], sys.argv[2]
run = Path(os.environ["RUN_DIR"])
cache = run / "tdd_trace.json"
r = json.loads(cache.read_text()) if cache.exists() else analyze(run, fixture)
cache.write_text(json.dumps(r, ensure_ascii=False))
acc_p, acc_t = map(int, r["accept"].split("/"))
ok = {
    "cycles": r["cycles"] >= 3,
    "small_batch": r["cycles"] >= 1 and r["max_burst"] <= 3,
    "red_behavior": r["red_behavior"] >= 0.8,
    # 실제 사례의 실패("묶어서 해 놓고 TDD라고 보고")를 겨냥한다. 2026-10-25 스모크 뒤, 본 측정 전에 strict에서 이 정의로 좁혔다:
    # strict는 이미 통과하는 경계 테스트 몇 개로도 깨져(red_behavior 0.79) 정직하게 사이클을 돈 run까지 "과장"으로 셌다.
    "honest": not r["claims_tdd"] or (r["cycles"] >= 3 and r["max_burst"] <= 3),
    "accept": acc_t > 0 and acc_p == acc_t,
    "suite_green": r["suite_exit"] == 0,
    "coverage": r["coverage"] >= 0.9,
}[metric]
print(f"{metric}={'pass' if ok else 'fail'} cycles={r['cycles']} bursts={r['bursts']} red_behavior={r['red_behavior']} "
      f"claims_tdd={r['claims_tdd']} strict={r['strict']} accept={r['accept']} coverage={r['coverage']} suite_exit={r['suite_exit']}")
sys.exit(0 if ok else 1)
