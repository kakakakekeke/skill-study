# gate-eval 보고서: `test-digest`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): []
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 36개(train 22/test 14), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| haiku | train | 20/22 | 80% | 100% |
| haiku | test | 14/14 | 100% | 100% |

- haiku 미발동: `npm test is red on my branch, like 6 or 7 failures across different files. can y → 0.33 ['NONE', 'repro-first', 'test-digest']` / `tsc --noEmit is spitting out hundreds of errors after upgrading to typescript 5. → 0.33 ['NONE', 'test-digest']`

| opus | train | 22/22 | 100% | 100% |
| opus | test | 14/14 | 100% | 100% |

**판정: 통과** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

