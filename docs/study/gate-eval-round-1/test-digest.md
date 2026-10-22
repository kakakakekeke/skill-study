# gate-eval 보고서: `test-digest`

- 날짜: 2026-10-22
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

## G2 확연한 품질 향상

### 모델 haiku

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| all-passing-verbose | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 3/3 |
| ci-log-file | 100%±0% | 80%±0% | 20% | 0% | 0% | 1 | 0 | 0/3 |
|  | ↑ 이득: Longest Bash tool output stayed under 80 lines | | | | | | | |
| pytest-noisy-failures | 80%±0% | 80%±0% | 0% | 0% | 0% | 0 | 0 | 0/3 |

- 노이즈 바닥(without 뒤집힘률 평균): 0% · 회귀율: 0% (0/13) · 이득 1건 · 순Δ +6.7% · rep 짝 with≥without 9/9
- with 설정에서 스킬 미호출 run: 3 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **haiku 판정: 통과**

  - 미호출 run 통과율: all-passing-verbose/rep3=100%, all-passing-verbose/rep2=100%, all-passing-verbose/rep1=100%

### 모델 opus

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| all-passing-verbose | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 2/3 |
| ci-log-file | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/3 |
| pytest-noisy-failures | 87%±12% | 80%±0% | 7% | 0% | 13% | 0 | 0 | 0/3 |

- 노이즈 바닥(without 뒤집힘률 평균): 0% · 회귀율: 0% (0/13) · 이득 0건 · 순Δ +2.2% · rep 짝 with≥without 9/9
- with 설정에서 스킬 미호출 run: 2 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **opus 판정: 통과**

  - 미호출 run 통과율: all-passing-verbose/rep2=100%, all-passing-verbose/rep1=100%

**G2 판정: 통과** (모든 모델에서 회귀율 ≤ 노이즈 바닥, 순Δ > 0, 짝 비교 과반)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 102 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 32줄 (상한 200)
- haiku: 컨텍스트 토큰 with 149,437 / without 142,856 (비율 1.05) · 출력 토큰 1,338/1,498 · 시간 15s/15s
- opus: 컨텍스트 토큰 with 166,252 / without 127,277 (비율 1.31) · 출력 토큰 1,155/1,111 · 시간 20s/17s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 이득 없음이면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| pass | pass | pass | **채택 가능** |
