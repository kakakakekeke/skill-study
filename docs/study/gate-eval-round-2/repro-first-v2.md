# gate-eval 보고서: `repro-first`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-opus-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 46개(train 28/test 18), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| haiku | train | 28/28 | 100% | 100% |
| haiku | test | 18/18 | 100% | 100% |
| opus | train | 28/28 | 100% | 100% |
| opus | test | 18/18 | 100% | 100% |

**판정: 통과** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

## G2 확연한 이득 (품질 또는 비용)

### 모델 haiku

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| cfg-already-fixed | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |
| cfg-partial-fix | 100%±0% | 73%±15% | 27% | 17% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to appcfg/ | | | | | | | |
| config-missing-timeout | 100%±0% | 50%±12% | 50% | 23% | 0% | 3 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to appcfg/ | | | | | | | |
|  | ↑ 이득: A new test covering a config without the timeout key was added to tests/ and passes after  | | | | | | | |
|  | ↑ 이득: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| median-even-length | 100%±0% | 67%±0% | 33% | 0% | 0% | 2 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
| slug-already-fixed | 100%±0% | 95%±11% | 5% | 10% | 0% | 0 | 0 | 0/5 |
| slug-partial-fix | 100%±0% | 83%±12% | 17% | 13% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to slugger/ | | | | | | | |
| slugify-trailing-sep | 100%±0% | 73%±22% | 27% | 20% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to slugger/ | | | | | | | |
| stats-already-fixed | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |
| stats-partial-fix | 100%±0% | 57%±9% | 43% | 10% | 0% | 3 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction (test or command) and it passe | | | | | | | |
|  | ↑ 이득: The agent did not conclude that the bug was already fixed; it identified that at least one | | | | | | | |

- 노이즈 바닥: **10%** = max(관측 10% [뒤집힘 54/480회 비교], 3/N 1%) · 회귀율: 0% (0/48) · 이득 11건 · 순Δ +22.4% · rep 짝 with≥without 45/45
- 비용: 출력 토큰 35% 증가 · 시간 6% 증가 (비용형 기준 30% 이상 감소)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **haiku 판정: 통과 (품질형)**

### 모델 opus

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| cfg-already-fixed | 100%±0% | 95%±11% | 5% | 10% | 0% | 0 | 0 | 0/5 |
| cfg-partial-fix | 83%±0% | 73%±9% | 10% | 10% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction (test or command) and it passe | | | | | | | |
| config-missing-timeout | 83%±12% | 90%±15% | -7% | 17% | 13% | 0 | 1 | 0/5 |
|  | ↓ 회귀: A failing command ran before the first edit to appcfg/ | | | | | | | |
| median-even-length | 97%±7% | 60%±15% | 37% | 27% | 7% | 3 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↑ 이득: A new test covering even-length median was added to tests/ and passes after the fix | | | | | | | |
|  | ↑ 이득: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| slug-already-fixed | 100%±0% | 95%±11% | 5% | 10% | 0% | 0 | 0 | 0/5 |
| slug-partial-fix | 93%±9% | 70%±7% | 23% | 7% | 10% | 2 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to slugger/ | | | | | | | |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction (test or command) and it passe | | | | | | | |
| slugify-trailing-sep | 90%±9% | 83%±0% | 7% | 0% | 10% | 0 | 0 | 0/5 |
| stats-already-fixed | 100%±0% | 95%±11% | 5% | 10% | 0% | 0 | 0 | 0/5 |
| stats-partial-fix | 87%±7% | 70%±7% | 17% | 17% | 7% | 1 | 0 | 0/5 |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction (test or command) and it passe | | | | | | | |

- 노이즈 바닥: **12%** = max(관측 12% [뒤집힘 58/480회 비교], 3/N 1%) · 회귀율: 2% (1/48) · 이득 7건 · 순Δ +11.3% · rep 짝 with≥without 42/45
- 비용: 출력 토큰 16% 증가 · 시간 8% 증가 (비용형 기준 30% 이상 감소)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **opus 판정: 실패**

**G2 판정: 실패** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 131 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 29줄 (상한 200)
- haiku: 컨텍스트 토큰 with 156,785 / without 115,491 (비율 1.36; 턴 수에 비례하는 참고치) · 출력 토큰 2,731/2,017 · 시간 28s/26s
- opus: 컨텍스트 토큰 with 122,494 / without 103,438 (비율 1.18; 턴 수에 비례하는 참고치) · 출력 토큰 1,728/1,487 · 시간 26s/24s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| pass | fail | pass | **백로그 (미입증 게이트 있음)** |
