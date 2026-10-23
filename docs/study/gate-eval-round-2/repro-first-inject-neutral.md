# gate-eval 보고서: `repro-first`

- 날짜: 2026-10-24
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-sonnet-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

trigger 결과 없음 (`evals/trigger.json` 또는 실행 누락).

## G2 확연한 이득 (품질 또는 비용)

조건: 기준선 `sib`(구성요소 siblings+skill) vs 처리 `inject`(hook+siblings+skill), `without_skill`(없음). 각 처리는 기준선과 따로 비교한다.

### 조건 나란히 (통과율 mean±sd / 훅 차단 평균)

| 모델 | eval | `sib` | `inject` | `without_skill` |
|---|---|---|---|---|
| haiku | config-missing-timeout | 67%±26% | 93%±9% | 57%±9% |
| haiku | config-missing-timeout-terse | 67%±0% | 97%±7% | 47%±18% |
| haiku | median-even-length | 67%±0% | 97%±7% | 67%±0% |
| haiku | median-even-length-terse | 100%±0% | 97%±7% | 67%±0% |
| haiku | slugify-trailing-sep | 93%±9% | 97%±7% | 83%±0% |
| haiku | slugify-trailing-sep-terse | 87%±7% | 100%±0% | 77%±15% |
| sonnet | config-missing-timeout | 70%±27% | 100%±0% | 33%±0% |
| sonnet | config-missing-timeout-terse | 60%±37% | 100%±0% | 33%±0% |
| sonnet | median-even-length | 100%±0% | 100%±0% | 33%±0% |
| sonnet | median-even-length-terse | 100%±0% | 100%±0% | 67%±0% |
| sonnet | slugify-trailing-sep | 100%±0% | 100%±0% | 80%±7% |
| sonnet | slugify-trailing-sep-terse | 77%±9% | 100%±0% | 83%±0% |

### 처리 `inject` (구성요소 hook+siblings+skill) vs `sib`

#### 모델 haiku

| eval | inject 통과율 (mean±sd) | sib 통과율 (mean±sd) | Δ | 노이즈 바닥(sib) | 뒤집힘(inject) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| config-missing-timeout | 93%±9% | 67%±26% | 27% | 37% | 10% | 1 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to appcfg/ | | | | | | | |
| config-missing-timeout-terse | 97%±7% | 67%±0% | 30% | 0% | 7% | 2 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to appcfg/ | | | | | | | |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
| median-even-length | 97%±7% | 67%±0% | 30% | 0% | 7% | 2 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
| median-even-length-terse | 97%±7% | 100%±0% | -3% | 0% | 7% | 0 | 0 | 0/5 |
| slugify-trailing-sep | 97%±7% | 93%±9% | 3% | 10% | 7% | 0 | 0 | 0/5 |
| slugify-trailing-sep-terse | 100%±0% | 87%±7% | 13% | 7% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to slugger/ | | | | | | | |

- 노이즈 바닥: **9%** = max(관측 9% [뒤집힘 32/360회 비교], 3/N 1%) · 회귀율: 0% (0/36) · 이득 6건 · 순Δ +16.7% · rep 짝 inject≥sib 28/30
- 비용: 출력 토큰 25% 증가 · 시간 25% 증가 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **haiku 판정: 통과 (품질형)**

#### 모델 sonnet

| eval | inject 통과율 (mean±sd) | sib 통과율 (mean±sd) | Δ | 노이즈 바닥(sib) | 뒤집힘(inject) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| config-missing-timeout | 100%±0% | 70%±27% | 30% | 30% | 0% | 3 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to appcfg/ | | | | | | | |
|  | ↑ 이득: A new test covering a config without the timeout key was added to tests/ and passes after  | | | | | | | |
|  | ↑ 이득: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| config-missing-timeout-terse | 100%±0% | 60%±37% | 40% | 40% | 0% | 4 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to appcfg/ | | | | | | | |
|  | ↑ 이득: A new test covering a config without the timeout key was added to tests/ and passes after  | | | | | | | |
|  | ↑ 이득: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
|  | ↑ 이득: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| median-even-length | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |
| median-even-length-terse | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |
| slugify-trailing-sep | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/5 |
| slugify-trailing-sep-terse | 100%±0% | 77%±9% | 23% | 13% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: A failing command ran before the first edit to slugger/ | | | | | | | |

- 노이즈 바닥: **14%** = max(관측 14% [뒤집힘 50/360회 비교], 3/N 1%) · 회귀율: 0% (0/36) · 이득 8건 · 순Δ +15.6% · rep 짝 inject≥sib 30/30
- 비용: 출력 토큰 11% 증가 · 시간 21% 증가 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **sonnet 판정: 통과 (품질형)**

**처리 `inject` G2 판정: 통과 (품질형)**

### 처리 `without_skill` (구성요소 없음) vs `sib`

#### 모델 haiku

| eval | without_skill 통과율 (mean±sd) | sib 통과율 (mean±sd) | Δ | 노이즈 바닥(sib) | 뒤집힘(without_skill) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| config-missing-timeout | 57%±9% | 67%±26% | -10% | 37% | 30% | 0 | 2 | n/a |
|  | ↓ 회귀: A new test covering a config without the timeout key was added to tests/ and passes after  | | | | | | | |
|  | ↓ 회귀: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| config-missing-timeout-terse | 47%±18% | 67%±0% | -20% | 0% | 20% | 0 | 2 | n/a |
|  | ↓ 회귀: A new test covering a config without the timeout key was added to tests/ and passes after  | | | | | | | |
|  | ↓ 회귀: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| median-even-length | 67%±0% | 67%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| median-even-length-terse | 67%±0% | 100%±0% | -33% | 0% | 0% | 0 | 2 | n/a |
|  | ↓ 회귀: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↓ 회귀: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
| slugify-trailing-sep | 83%±0% | 93%±9% | -10% | 10% | 0% | 0 | 1 | n/a |
|  | ↓ 회귀: A failing command ran before the first edit to slugger/ | | | | | | | |
| slugify-trailing-sep-terse | 77%±15% | 87%±7% | -10% | 7% | 13% | 0 | 0 | n/a |

- 노이즈 바닥: **9%** = max(관측 9% [뒤집힘 32/360회 비교], 3/N 1%) · 회귀율: 19% (7/36) · 이득 0건 · 순Δ -13.9% · rep 짝 without_skill≥sib 14/30
- 비용: 출력 토큰 17% 감소 · 시간 13% 감소 (비용형 기준 30% 이상 감소)
- **haiku 판정: 실패**

#### 모델 sonnet

| eval | without_skill 통과율 (mean±sd) | sib 통과율 (mean±sd) | Δ | 노이즈 바닥(sib) | 뒤집힘(without_skill) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| config-missing-timeout | 33%±0% | 70%±27% | -37% | 30% | 0% | 0 | 1 | n/a |
|  | ↓ 회귀: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
| config-missing-timeout-terse | 33%±0% | 60%±37% | -27% | 40% | 0% | 0 | 0 | n/a |
| median-even-length | 33%±0% | 100%±0% | -67% | 0% | 0% | 0 | 4 | n/a |
|  | ↓ 회귀: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↓ 회귀: A new test covering even-length median was added to tests/ and passes after the fix | | | | | | | |
|  | ↓ 회귀: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
|  | ↓ 회귀: The final message states a concrete recurrence-prevention measure (the added regression te | | | | | | | |
| median-even-length-terse | 67%±0% | 100%±0% | -33% | 0% | 0% | 0 | 2 | n/a |
|  | ↓ 회귀: A failing command ran before the first edit to statkit/ | | | | | | | |
|  | ↓ 회귀: After editing the source, the agent re-ran the reproduction and the full test suite and bo | | | | | | | |
| slugify-trailing-sep | 80%±7% | 100%±0% | -20% | 0% | 7% | 0 | 1 | n/a |
|  | ↓ 회귀: A failing command ran before the first edit to slugger/ | | | | | | | |
| slugify-trailing-sep-terse | 83%±0% | 77%±9% | 7% | 13% | 0% | 0 | 0 | n/a |

- 노이즈 바닥: **14%** = max(관측 14% [뒤집힘 50/360회 비교], 3/N 1%) · 회귀율: 22% (8/36) · 이득 0건 · 순Δ -29.4% · rep 짝 without_skill≥sib 8/30
- 비용: 출력 토큰 30% 감소 · 시간 23% 감소 (비용형 기준 30% 이상 감소)
- **sonnet 판정: 실패**

**처리 `without_skill` G2 판정: 실패**

**G2 판정 (스킬 게이트 = 처리 `inject`): 통과 (품질형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 119 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 26줄 (상한 200)
- `inject` haiku: 컨텍스트 토큰 237,990 / 기준선 172,499 (비율 1.38; 턴 수에 비례하는 참고치) · 출력 토큰 2,260/1,803 · 시간 20s/16s
- `inject` sonnet: 컨텍스트 토큰 216,875 / 기준선 193,845 (비율 1.12; 턴 수에 비례하는 참고치) · 출력 토큰 1,366/1,234 · 시간 29s/24s
- `without_skill` haiku: 컨텍스트 토큰 159,075 / 기준선 172,499 (비율 0.92; 턴 수에 비례하는 참고치) · 출력 토큰 1,492/1,803 · 시간 14s/16s
- `without_skill` sonnet: 컨텍스트 토큰 154,015 / 기준선 193,845 (비율 0.79; 턴 수에 비례하는 참고치) · 출력 토큰 861/1,234 · 시간 19s/24s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| missing | pass | pass | **백로그 (미입증 게이트 있음)** |
