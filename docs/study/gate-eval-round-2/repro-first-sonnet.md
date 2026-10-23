# gate-eval 보고서: `repro-first`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-sonnet-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 46개(train 28/test 18), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| sonnet | train | 28/28 | 100% | 100% |
| sonnet | test | 18/18 | 100% | 100% |

**판정: 통과** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

## G2 확연한 이득 (품질 또는 비용)

조건: 기준선 `without_skill`(구성요소 없음) vs 처리 `with_skill`(skill). 각 처리는 기준선과 따로 비교한다.

### 처리 `with_skill` (구성요소 skill) vs `without_skill`

#### 모델 sonnet

| eval | with_skill 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(with_skill) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| config-missing-timeout | 100%±0% | 50%±12% | 50% | 13% | 0% | 3 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to appcfg/ | | | | | | | |
|  | ↑ 이득: A new test covering a config without the timeout key was added to tests/ and passes after  | | | | | | | |
|  | ↑ 이득: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| median-even-length | 100%±0% | 33%±0% | 67% | 0% | 0% | 4 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↑ 이득: A new test covering even-length median was added to tests/ and passes after the fix | | | | | | | |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
|  | ↑ 이득: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| slugify-trailing-sep | 100%±0% | 83%±0% | 17% | 0% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to slugger/ | | | | | | | |

- 노이즈 바닥: **4%** = max(관측 4% [뒤집힘 8/180회 비교], 3/N 2%) · 회귀율: 0% (0/18) · 이득 8건 · 순Δ +44.4% · rep 짝 with_skill≥without_skill 15/15
- 비용: 출력 토큰 58% 증가 · 시간 63% 증가 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **sonnet 판정: 통과 (품질형)**

**처리 `with_skill` G2 판정: 통과 (품질형)**

**G2 판정 (스킬 게이트 = 처리 `with_skill`): 통과 (품질형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 119 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 26줄 (상한 200)
- `with_skill` sonnet: 컨텍스트 토큰 238,542 / 기준선 133,789 (비율 1.78; 턴 수에 비례하는 참고치) · 출력 토큰 1,445/912 · 시간 31s/19s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| pass | pass | pass | **채택 가능** |
