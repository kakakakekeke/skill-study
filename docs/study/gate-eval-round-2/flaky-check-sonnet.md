# gate-eval 보고서: `flaky-check`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-sonnet-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 34개(train 21/test 13), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| sonnet | train | 20/21 | 100% | 92% |
| sonnet | test | 13/13 | 100% | 100% |

- sonnet 과잉 트리거: `run the perf benchmark 15 times and report the p50/p95 latency spread → 0.67`


**판정: 통과** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

## G2 확연한 이득 (품질 또는 비용)

조건: 기준선 `without_skill`(구성요소 없음) vs 처리 `with_skill`(skill). 각 처리는 기준선과 따로 비교한다.

### 처리 `with_skill` (구성요소 skill) vs `without_skill`

#### 모델 sonnet

| eval | with_skill 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(with_skill) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| deterministic-not-flaky | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |
| pytest-two-signatures | 92%±11% | 80%±35% | 12% | 40% | 16% | 0 | 0 | 0/5 |
| shell-step-intermittent | 97%±7% | 100%±0% | -3% | 0% | 7% | 0 | 0 | 0/5 |

- 노이즈 바닥: **13%** = max(관측 13% [뒤집힘 20/150회 비교], 3/N 2%) · 회귀율: 0% (0/15) · 이득 0건 · 순Δ +2.9% · rep 짝 with_skill≥without_skill 13/15
- 비용: 출력 토큰 19% 감소 · 시간 49% 감소 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **sonnet 판정: 통과 (비용형)**

**처리 `with_skill` G2 판정: 통과 (비용형: 품질 동률, 비용 확연히 감소)**

**G2 판정 (스킬 게이트 = 처리 `with_skill`): 통과 (비용형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 180 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 28줄 (상한 200)
- `with_skill` sonnet: 컨텍스트 토큰 150,403 / 기준선 118,501 (비율 1.27; 턴 수에 비례하는 참고치) · 출력 토큰 1,221/1,514 · 시간 26s/52s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| pass | pass | pass | **채택 가능** |
