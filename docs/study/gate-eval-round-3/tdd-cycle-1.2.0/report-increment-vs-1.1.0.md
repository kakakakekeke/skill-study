# gate-eval 보고서: `tdd-cycle`

- 날짜: 2026-11-06
- Claude Code: 2.1.318 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-sonnet-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

trigger 결과 없음 (`evals/trigger.json` 또는 실행 누락).

## G2 확연한 이득 (품질 또는 비용)

조건: 기준선 `prev`(구성요소 hook+skill) vs 처리 `both`(hook+skill). 각 처리는 기준선과 따로 비교한다.

### 조건 나란히 (통과율 mean±sd / 훅 차단 평균)

| 모델 | eval | `prev` | `both` |
|---|---|---|---|
| haiku | article-store | 88%±0% / 차단 0.3 | 88%±0% / 차단 0.3 |
| haiku | article-store-mode | 92%±7% / 차단 0.3 | 88%±0% |
| haiku | duration-parse | 88%±0% / 차단 0.3 | 88%±0% / 차단 0.3 |
| haiku | duration-parse-mode | 88%±0% / 차단 0.3 | 88%±0% |
| haiku | feed-parse | 96%±7% / 차단 0.7 | 92%±7% |
| haiku | feed-parse-mode | 92%±7% / 차단 1.0 | 96%±7% / 차단 0.7 |
| haiku | refactor-dedup | 100%±0% | 100%±0% / 차단 0.3 |
| sonnet | article-store | 96%±7% / 차단 0.3 | 96%±7% |
| sonnet | article-store-mode | 96%±7% / 차단 1.0 | 96%±7% |
| sonnet | duration-parse | 88%±0% / 차단 1.3 | 88%±12% |
| sonnet | duration-parse-mode | 88%±0% / 차단 1.0 | 79%±14% / 차단 1.0 |
| sonnet | feed-parse | 100%±0% / 차단 1.7 | 96%±7% / 차단 1.0 |
| sonnet | feed-parse-mode | 88%±22% / 차단 1.0 | 96%±7% / 차단 1.3 |
| sonnet | refactor-dedup | 100%±0% / 차단 2.0 | 100%±0% / 차단 2.0 |

### 처리 `both` (구성요소 hook+skill) vs `prev`

#### 모델 haiku

| eval | both 통과율 (mean±sd) | prev 통과율 (mean±sd) | Δ | 뒤집힘(prev, 참고) | 뒤집힘(both) | 이득 | 셀 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| article-store | 88%±0% | 88%±0% | 0% | 0% | 0% | 0 | 0 | 0/3 |
| article-store-mode | 88%±0% | 92%±7% | -4% | 8% | 0% | 0 | 0 | 0/3 |
| duration-parse | 88%±0% | 88%±0% | 0% | 0% | 0% | 0 | 0 | 0/3 |
| duration-parse-mode | 88%±0% | 88%±0% | 0% | 0% | 0% | 0 | 0 | 0/3 |
| feed-parse | 92%±7% | 96%±7% | -4% | 8% | 8% | 0 | 0 | 0/3 |
| feed-parse-mode | 96%±7% | 92%±7% | 4% | 8% | 8% | 1 | 0 | 0/3 |
|  | ↑ 이득: 최종 테스트의 80% 이상이 동작 이유로 실패하는 것이 관찰됨 | | | | | | | |
| refactor-dedup | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 0/3 |

- 순Δ **-0.6%** (품질형 기준 ≥ 5%p) · 층화 순열 p↑ **0.8332** / p↓ 0.5021 (α 0.05) · 셀 회귀 **0**/51 · 이득 1건
- 참고: 노이즈 바닥 4% = max(관측 4% [뒤집힘 6/153회 비교], 3/N 2%) — 판정에 쓰지 않음
- 비용: 출력 토큰 8% 감소 · 시간 2% 감소 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- 훅 차단: run당 평균 0.2회 (PreToolUse 거부 + Stop hook feedback)
- **haiku 판정: 실패**

#### 모델 sonnet

| eval | both 통과율 (mean±sd) | prev 통과율 (mean±sd) | Δ | 뒤집힘(prev, 참고) | 뒤집힘(both) | 이득 | 셀 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| article-store | 96%±7% | 96%±7% | 0% | 8% | 8% | 0 | 0 | 0/3 |
| article-store-mode | 96%±7% | 96%±7% | 0% | 8% | 8% | 0 | 0 | 0/3 |
| duration-parse | 88%±12% | 88%±0% | 0% | 17% | 17% | 0 | 0 | 0/3 |
| duration-parse-mode | 79%±14% | 88%±0% | -8% | 0% | 17% | 0 | 0 | 0/3 |
| feed-parse | 96%±7% | 100%±0% | -4% | 0% | 8% | 0 | 0 | 0/3 |
| feed-parse-mode | 96%±7% | 88%±22% | 8% | 25% | 8% | 0 | 0 | 0/3 |
| refactor-dedup | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | 3/3 |

- 순Δ **-0.6%** (품질형 기준 ≥ 5%p) · 층화 순열 p↑ **0.6661** / p↓ 0.5015 (α 0.05) · 셀 회귀 **0**/51 · 이득 0건
- 참고: 노이즈 바닥 8% = max(관측 8% [뒤집힘 14/153회 비교], 3/N 2%) — 판정에 쓰지 않음
- 비용: 출력 토큰 7% 감소 · 시간 6% 감소 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 3 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- 훅 차단: run당 평균 0.8회 (PreToolUse 거부 + Stop hook feedback)
- **sonnet 판정: 실패**

  - 미호출 run 통과율: refactor-dedup/rep2=100%, refactor-dedup/rep1=100%, refactor-dedup/rep3=100%

**처리 `both` G2 판정: 실패**

**G2 판정 (스킬 게이트 = 처리 `both`): 실패** (모델마다. 품질형: 층화 순열 p↑ < 0.05 그리고 순Δ ≥ 5%p 그리고 셀 회귀 0. 비용형: 셀 회귀 0 그리고 순Δ ≥ -5%p 그리고 p↓ ≥ 0.05 그리고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 156 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 43줄 (상한 200)
- `both` haiku: 컨텍스트 토큰 1,974,148 / 기준선 1,866,915 (비율 1.06; 턴 수에 비례하는 참고치) · 출력 토큰 20,021/21,786 · 시간 136s/139s
- `both` sonnet: 컨텍스트 토큰 1,227,887 / 기준선 1,267,691 (비율 0.97; 턴 수에 비례하는 참고치) · 출력 토큰 10,559/11,323 · 시간 101s/107s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| missing | fail | pass | **백로그 (미입증 게이트 있음)** |
