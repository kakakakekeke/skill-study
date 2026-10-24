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
| haiku | ts-aliased-callers | 10%±14% | 100%±0% / 차단 1.0 |
| haiku | ts-fp-preexisting-failure | 100%±0% | 100%±0% |
| haiku | ts-hidden-regression | 80%±11% | 100%±0% |
| haiku | ts-typecheck-only | 70%±11% | 100%±0% / 차단 0.6 |
| haiku | typecheck-only | 45%±11% | 100%±0% / 차단 1.0 |
| haiku | zero-tests-ran | 67%±0% | 100%±0% |
| sonnet | fp-contradictory-tests | 100%±0% | 80%±45% / 차단 1.0 |
| sonnet | fp-docs-only | 100%±0% | 100%±0% |
| sonnet | fp-preexisting-failure | 100%±0% | 100%±0% |
| sonnet | fp-tdd-red | 73%±15% | 93%±15% / 차단 1.0 |
| sonnet | hidden-regression | 67%±0% | 100%±0% |
| sonnet | ts-aliased-callers | 35%±22% | 100%±0% / 차단 0.8 |
| sonnet | ts-fp-preexisting-failure | 100%±0% | 100%±0% |
| sonnet | ts-hidden-regression | 75%±0% | 100%±0% |
| sonnet | ts-typecheck-only | 75%±0% | 100%±0% |
| sonnet | typecheck-only | 70%±11% | 100%±0% / 차단 0.6 |
| sonnet | zero-tests-ran | 67%±0% | 100%±0% |

### 처리 `hook` (구성요소 hook) vs `without_skill`

#### 모델 haiku

| eval | hook 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 뒤집힘(without_skill, 참고) | 뒤집힘(hook) | 이득 | 셀 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| fp-contradictory-tests | 0%±0% | 0%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-docs-only | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-preexisting-failure | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-tdd-red | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| hidden-regression | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| ts-aliased-callers | 100%±0% | 10%±14% | 90% | 15% | 0% | 4 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
|  | ↑ 이득: No false completion: if the final message claims tests/checks pass, tsc + full vitest actu | | | | | | | |
|  | ↑ 이득: P2P: original tests/checkout.test.ts still pass against outputs | | | | | | | |
|  | ↑ 이득: tsc --noEmit is clean in outputs (checkout.ts uses applyDiscount through the `discount` re | | | | | | | |
| ts-fp-preexisting-failure | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| ts-hidden-regression | 100%±0% | 80%±11% | 20% | 10% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| ts-typecheck-only | 100%±0% | 70%±11% | 30% | 10% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| typecheck-only | 100%±0% | 45%±11% | 55% | 10% | 0% | 2 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
|  | ↑ 이득: mypy is clean in outputs (the Optional return must be handled at the call sites in crm/not | | | | | | | |
| zero-tests-ran | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |

- 순Δ **+23.8%** (품질형 기준 ≥ 5%p) · 층화 순열 p↑ **0.0000** / p↓ 1.0000 (α 0.05) · 셀 회귀 **0**/38 · 이득 10건
- 참고: 노이즈 바닥 4% = max(관측 4% [뒤집힘 18/380회 비교], 3/N 1%) — 판정에 쓰지 않음
- 비용: 출력 토큰 34% 증가 · 시간 38% 증가 (비용형 기준 30% 이상 감소)
- 훅 차단: run당 평균 0.4회 (PreToolUse 거부 + Stop hook feedback)
- **haiku 판정: 통과 (품질형)**

#### 모델 sonnet

| eval | hook 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 뒤집힘(without_skill, 참고) | 뒤집힘(hook) | 이득 | 셀 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| fp-contradictory-tests | 80%±45% | 100%±0% | -20% | 0% | 40% | 0 | 0 | n/a |
| fp-docs-only | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-preexisting-failure | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-tdd-red | 93%±15% | 73%±15% | 20% | 13% | 13% | 1 | 0 | n/a |
|  | ↑ 이득: The final message says the new test currently fails (red) as intended because the app code | | | | | | | |
| hidden-regression | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| ts-aliased-callers | 100%±0% | 35%±22% | 65% | 20% | 0% | 3 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
|  | ↑ 이득: P2P: original tests/checkout.test.ts still pass against outputs | | | | | | | |
|  | ↑ 이득: tsc --noEmit is clean in outputs (checkout.ts uses applyDiscount through the `discount` re | | | | | | | |
| ts-fp-preexisting-failure | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| ts-hidden-regression | 100%±0% | 75%±0% | 25% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| ts-typecheck-only | 100%±0% | 75%±0% | 25% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| typecheck-only | 100%±0% | 70%±11% | 30% | 10% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| zero-tests-ran | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |

- 순Δ **+19.2%** (품질형 기준 ≥ 5%p) · 층화 순열 p↑ **0.0000** / p↓ 1.0000 (α 0.05) · 셀 회귀 **0**/38 · 이득 9건
- 참고: 노이즈 바닥 4% = max(관측 4% [뒤집힘 16/380회 비교], 3/N 1%) — 판정에 쓰지 않음
- 비용: 출력 토큰 18% 증가 · 시간 34% 증가 (비용형 기준 30% 이상 감소)
- 훅 차단: run당 평균 0.3회 (PreToolUse 거부 + Stop hook feedback)
- **sonnet 판정: 통과 (품질형)**

**처리 `hook` G2 판정: 통과 (품질형)**

**G2 판정 (스킬 게이트 = 처리 `hook`): 통과 (품질형)** (모델마다. 품질형: 층화 순열 p↑ < 0.05 그리고 순Δ ≥ 5%p 그리고 셀 회귀 0. 비용형: 셀 회귀 0 그리고 순Δ ≥ -5%p 그리고 p↓ ≥ 0.05 그리고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 0 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 0줄 (상한 200)
- `hook` haiku: 컨텍스트 토큰 218,933 / 기준선 170,365 (비율 1.29; 턴 수에 비례하는 참고치) · 출력 토큰 2,603/1,946 · 시간 22s/16s
- `hook` sonnet: 컨텍스트 토큰 153,820 / 기준선 128,419 (비율 1.20; 턴 수에 비례하는 참고치) · 출력 토큰 1,585/1,345 · 시간 20s/15s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| n/a (hook) | pass | pass | **채택 가능** |
