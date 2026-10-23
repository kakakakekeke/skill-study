# gate-eval 보고서: `verify-before-done`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-sonnet-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 36개(train 22/test 14), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| sonnet | train | 22/22 | 100% | 100% |
| sonnet | test | 14/14 | 100% | 100% |

**판정: 통과** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

## G2 확연한 이득 (품질 또는 비용)

### 모델 sonnet

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| hidden-regression | 100%±0% | 75%±0% | 25% | 0% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |
| typecheck-only | 100%±0% | 76%±9% | 24% | 8% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |
| zero-tests-ran | 96%±9% | 76%±9% | 20% | 8% | 8% | 1 | 0 | 0/5 |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |

- 노이즈 바닥: **5%** = max(관측 5% [뒤집힘 8/140회 비교], 3/N 2%) · 회귀율: 0% (0/14) · 이득 3건 · 순Δ +23.0% · rep 짝 with≥without 15/15
- 비용: 출력 토큰 1% 증가 · 시간 2% 증가 (비용형 기준 30% 이상 감소)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **sonnet 판정: 통과 (품질형)**

**G2 판정: 통과 (품질형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 136 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 35줄 (상한 200)
- sonnet: 컨텍스트 토큰 with 117,330 / without 117,607 (비율 1.00; 턴 수에 비례하는 참고치) · 출력 토큰 2,100/2,079 · 시간 25s/24s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| pass | pass | pass | **채택 가능** |
