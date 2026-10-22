# gate-eval 보고서: `repro-first`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-opus-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 20개(train 12/test 8), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| haiku | train | 12/12 | 100% | 100% |
| haiku | test | 8/8 | 100% | 100% |
| opus | train | 12/12 | 100% | 100% |
| opus | test | 8/8 | 100% | 100% |

**판정: 통과** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

## G2 확연한 이득 (품질 또는 비용)

### 모델 haiku

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| config-missing-timeout | 94%±10% | 72%±19% | 22% | 22% | 11% | 1 | 0 | 0/3 |
|  | ↑ 이득: A failing command ran before the first edit to appcfg/ | | | | | | | |
| median-even-length | 100%±0% | 67%±0% | 33% | 0% | 0% | 2 | 0 | 0/3 |
|  | ↑ 이득: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
| slugify-trailing-sep | 100%±0% | 78%±10% | 22% | 11% | 0% | 1 | 0 | 0/3 |
|  | ↑ 이득: A failing command ran before the first edit to slugger/ | | | | | | | |

- 노이즈 바닥(without 뒤집힘률 평균): 11% · 회귀율: 0% (0/18) · 이득 4건 · 순Δ +25.9% · rep 짝 with≥without 9/9
- 비용: 출력 토큰 -50% 감소 · 시간 -25% 감소 (비용형 기준 30% 이상)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **haiku 판정: 통과 (품질형)**

### 모델 opus

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| config-missing-timeout | 100%±0% | 94%±10% | 6% | 11% | 0% | 0 | 0 | 0/3 |
| median-even-length | 100%±0% | 61%±19% | 39% | 22% | 0% | 3 | 0 | 0/3 |
|  | ↑ 이득: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↑ 이득: A new test covering even-length median was added to tests/ and passes after the fix | | | | | | | |
|  | ↑ 이득: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| slugify-trailing-sep | 100%±0% | 83%±0% | 17% | 0% | 0% | 1 | 0 | 0/3 |
|  | ↑ 이득: A failing command ran before the first edit to slugger/ | | | | | | | |

- 노이즈 바닥(without 뒤집힘률 평균): 11% · 회귀율: 0% (0/18) · 이득 4건 · 순Δ +20.4% · rep 짝 with≥without 9/9
- 비용: 출력 토큰 -35% 감소 · 시간 -24% 감소 (비용형 기준 30% 이상)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **opus 판정: 통과 (품질형)**

**G2 판정: 통과 (품질형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 119 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 26줄 (상한 200)
- haiku: 컨텍스트 토큰 with 236,065 / without 169,527 (비율 1.39; 턴 수에 비례하는 참고치) · 출력 토큰 2,347/1,569 · 시간 20s/16s
- opus: 컨텍스트 토큰 with 231,776 / without 162,564 (비율 1.43; 턴 수에 비례하는 참고치) · 출력 토큰 1,821/1,353 · 시간 26s/21s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| pass | pass | pass | **채택 가능** |
