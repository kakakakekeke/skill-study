# gate-eval 보고서: `repro-first`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-opus-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 36개(train 22/test 14), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| haiku | train | 22/22 | 100% | 100% |
| haiku | test | 14/14 | 100% | 100% |
| opus | train | 22/22 | 100% | 100% |
| opus | test | 14/14 | 100% | 100% |

**판정: 통과** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

## G2 확연한 이득 (품질 또는 비용)

### 모델 haiku

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| ledger-fixed-stale-api | 96%±9% | 92%±11% | 4% | 12% | 8% | 0 | 0 | 0/5 |
| ledger-fixed-unrelated-failure | 80%±11% | 85%±14% | -5% | 15% | 10% | 0 | 0 | 0/5 |
| ledger-fixed-wrong-report | 100%±0% | 90%±14% | 10% | 15% | 0% | 0 | 0 | 0/5 |
| ledger-partial-changed-symptom | 100%±0% | 97%±6% | 3% | 6% | 0% | 0 | 0 | 0/5 |
| ledger-partial-specialcase | 100%±0% | 87%±14% | 13% | 23% | 0% | 0 | 0 | 0/5 |
| ledger-real-deep | 100%±0% | 94%±8% | 6% | 9% | 0% | 0 | 0 | 0/5 |

- 노이즈 바닥: **13%** = max(관측 13% [뒤집힘 42/330회 비교], 3/N 1%) · 회귀율: 0% (0/33) · 이득 0건 · 순Δ +5.2% · rep 짝 with≥without 28/30
- 비용: 출력 토큰 24% 증가 · 시간 2% 감소 (비용형 기준 30% 이상 감소)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **haiku 판정: 실패**

### 모델 opus

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| ledger-fixed-stale-api | 92%±11% | 92%±11% | 0% | 12% | 12% | 0 | 0 | 0/5 |
| ledger-fixed-unrelated-failure | 80%±11% | 90%±14% | -10% | 15% | 10% | 0 | 1 | 0/5 |
|  | ↓ 회귀: The agent ran a reproduction of the reported rounding bug itself (an invoice with 5+ taxed | | | | | | | |
| ledger-fixed-wrong-report | 100%±0% | 85%±14% | 15% | 15% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: The agent reproduced the example (3 x 0.333) and checked the documented rule (invoice.py d | | | | | | | |
| ledger-partial-changed-symptom | 100%±0% | 86%±10% | 14% | 11% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: The agent did not conclude that the bug was already fixed or not reproducible; it found a  | | | | | | | |
| ledger-partial-specialcase | 100%±0% | 87%±14% | 13% | 17% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to ledger/ | | | | | | | |
| ledger-real-deep | 100%±0% | 91%±8% | 9% | 9% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: The agent did not conclude that the bug was already fixed or not reproducible; it found a  | | | | | | | |

- 노이즈 바닥: **13%** = max(관측 13% [뒤집힘 42/330회 비교], 3/N 1%) · 회귀율: 3% (1/33) · 이득 4건 · 순Δ +6.9% · rep 짝 with≥without 27/30
- 비용: 출력 토큰 15% 증가 · 시간 15% 증가 (비용형 기준 30% 이상 감소)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **opus 판정: 실패**

**G2 판정: 실패** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 119 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 26줄 (상한 200)
- haiku: 컨텍스트 토큰 with 214,408 / without 163,063 (비율 1.31; 턴 수에 비례하는 참고치) · 출력 토큰 4,187/3,388 · 시간 31s/32s
- opus: 컨텍스트 토큰 with 150,525 / without 123,188 (비율 1.22; 턴 수에 비례하는 참고치) · 출력 토큰 2,570/2,226 · 시간 35s/30s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| pass | fail | pass | **백로그 (미입증 게이트 있음)** |
