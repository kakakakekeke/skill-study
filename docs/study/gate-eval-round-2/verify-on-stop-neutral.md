# gate-eval 보고서: `verify-on-stop`

- 날짜: 2026-10-24
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-sonnet-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

훅 전용(SKILL.md 없음): 트리거는 결정적이다. G1은 거짓양성으로 보며, G2 표의 오탐 fixture(`fp-*`) 회귀와 차단 횟수로 판정한다(원칙 §3.2).

## G2 확연한 이득 (품질 또는 비용)

조건: 기준선 `without_skill`(구성요소 없음) vs 처리 `hook`(hook). 각 처리는 기준선과 따로 비교한다.

### 조건 나란히 (통과율 mean±sd / 훅 차단 평균)

| 모델 | eval | `without_skill` | `hook` |
|---|---|---|---|
| haiku | fp-contradictory-tests | 0%±0% | 0%±0% / 차단 1.0 |
| haiku | fp-docs-only | 100%±0% | 100%±0% |
| haiku | fp-preexisting-failure | 100%±0% | 100%±0% |
| haiku | fp-tdd-red | 100%±0% | 100%±0% / 차단 1.0 |
| haiku | hidden-regression | 67%±0% | 100%±0% |
| haiku | typecheck-only | 40%±14% | 100%±0% / 차단 1.0 |
| haiku | zero-tests-ran | 67%±0% | 100%±0% |
| sonnet | fp-contradictory-tests | 60%±55% | 95%±11% / 차단 1.0 |
| sonnet | fp-docs-only | 100%±0% | 100%±0% |
| sonnet | fp-preexisting-failure | 100%±0% | 100%±0% |
| sonnet | fp-tdd-red | 73%±15% | 100%±0% / 차단 1.0 |
| sonnet | hidden-regression | 67%±0% | 100%±0% |
| sonnet | typecheck-only | 55%±21% | 100%±0% / 차단 0.8 |
| sonnet | zero-tests-ran | 67%±0% | 100%±0% |

### 처리 `hook` (구성요소 hook) vs `without_skill`

#### 모델 haiku

| eval | hook 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(hook) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| fp-contradictory-tests | 0%±0% | 0%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-docs-only | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-preexisting-failure | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-tdd-red | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| hidden-regression | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| typecheck-only | 100%±0% | 40%±14% | 60% | 15% | 0% | 2 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
|  | ↑ 이득: mypy is clean in outputs (the Optional return must be handled at the call sites in crm/not | | | | | | | |
| zero-tests-ran | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |

- 노이즈 바닥: **2%** = max(관측 2% [뒤집힘 6/230회 비교], 3/N 1%) · 회귀율: 0% (0/23) · 이득 4건 · 순Δ +18.1% · rep 짝 hook≥without_skill 35/35
- 비용: 출력 토큰 34% 증가 · 시간 16% 증가 (비용형 기준 30% 이상 감소)
- 훅 차단: run당 평균 0.4회 (PreToolUse 거부 + Stop hook feedback)
- **haiku 판정: 통과 (품질형)**

#### 모델 sonnet

| eval | hook 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(hook) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| fp-contradictory-tests | 95%±11% | 60%±55% | 35% | 60% | 10% | 0 | 0 | n/a |
| fp-docs-only | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-preexisting-failure | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-tdd-red | 100%±0% | 73%±15% | 27% | 13% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The final message says the new test currently fails (red) as intended because the app code | | | | | | | |
| hidden-regression | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| typecheck-only | 100%±0% | 55%±21% | 45% | 25% | 0% | 2 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
|  | ↑ 이득: mypy is clean in outputs (the Optional return must be handled at the call sites in crm/not | | | | | | | |
| zero-tests-ran | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |

- 노이즈 바닥: **14%** = max(관측 14% [뒤집힘 38/230회 비교], 3/N 1%) · 회귀율: 0% (0/23) · 이득 5건 · 순Δ +24.8% · rep 짝 hook≥without_skill 35/35
- 비용: 출력 토큰 24% 증가 · 시간 25% 증가 (비용형 기준 30% 이상 감소)
- 훅 차단: run당 평균 0.4회 (PreToolUse 거부 + Stop hook feedback)
- **sonnet 판정: 통과 (품질형)**

**처리 `hook` G2 판정: 통과 (품질형)**

**G2 판정 (스킬 게이트 = 처리 `hook`): 통과 (품질형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 0 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 0줄 (상한 200)
- `hook` haiku: 컨텍스트 토큰 209,521 / 기준선 168,154 (비율 1.25; 턴 수에 비례하는 참고치) · 출력 토큰 2,509/1,879 · 시간 23s/19s
- `hook` sonnet: 컨텍스트 토큰 157,730 / 기준선 128,569 (비율 1.23; 턴 수에 비례하는 참고치) · 출력 토큰 1,490/1,202 · 시간 24s/19s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| n/a (hook) | pass | pass | **채택 가능** |
