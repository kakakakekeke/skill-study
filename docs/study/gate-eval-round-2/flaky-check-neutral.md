# gate-eval 보고서: `flaky-check`

- 날짜: 2026-10-24
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-sonnet-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

trigger 결과 없음 (`evals/trigger.json` 또는 실행 누락).

## G2 확연한 이득 (품질 또는 비용)

조건: 기준선 `without_skill`(구성요소 없음) vs 처리 `with_skill`(skill). 각 처리는 기준선과 따로 비교한다.

### 처리 `with_skill` (구성요소 skill) vs `without_skill`

#### 모델 haiku

| eval | with_skill 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(with_skill) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| deterministic-not-flaky | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |
| pytest-two-signatures | 100%±0% | 92%±11% | 8% | 12% | 0% | 0 | 0 | 0/5 |
| shell-step-intermittent | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |

- 노이즈 바닥: **4%** = max(관측 4% [뒤집힘 6/150회 비교], 3/N 2%) · 회귀율: 0% (0/15) · 이득 0건 · 순Δ +2.7% · rep 짝 with_skill≥without_skill 15/15
- 비용: 출력 토큰 42% 감소 · 시간 75% 감소 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **haiku 판정: 통과 (비용형)**

#### 모델 sonnet

| eval | with_skill 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(with_skill) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| deterministic-not-flaky | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |
| pytest-two-signatures | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |
| shell-step-intermittent | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |

- 노이즈 바닥: **2%** = max(관측 0% [뒤집힘 0/150회 비교], 3/N 2%) · 회귀율: 0% (0/15) · 이득 0건 · 순Δ +0.0% · rep 짝 with_skill≥without_skill 15/15
- 비용: 출력 토큰 24% 감소 · 시간 66% 감소 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **sonnet 판정: 통과 (비용형)**

**처리 `with_skill` G2 판정: 통과 (비용형: 품질 동률, 비용 확연히 감소)**

**G2 판정 (스킬 게이트 = 처리 `with_skill`): 통과 (비용형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 180 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 28줄 (상한 200)
- `with_skill` haiku: 컨텍스트 토큰 152,805 / 기준선 163,099 (비율 0.94; 턴 수에 비례하는 참고치) · 출력 토큰 1,826/3,145 · 시간 20s/79s
- `with_skill` sonnet: 컨텍스트 토큰 147,937 / 기준선 124,917 (비율 1.18; 턴 수에 비례하는 참고치) · 출력 토큰 1,215/1,592 · 시간 25s/72s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| missing | pass | pass | **백로그 (미입증 게이트 있음)** |
