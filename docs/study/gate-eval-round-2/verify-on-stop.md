# gate-eval 보고서: `verify-on-stop`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-opus-5-5']
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
| haiku | typecheck-only | 50%±0% | 100%±0% / 차단 1.0 |
| haiku | zero-tests-ran | 67%±0% | 100%±0% |
| opus | fp-contradictory-tests | 100%±0% | 100%±0% / 차단 1.0 |
| opus | fp-docs-only | 100%±0% | 100%±0% |
| opus | fp-preexisting-failure | 100%±0% | 100%±0% |
| opus | fp-tdd-red | 100%±0% | 100%±0% / 차단 1.0 |
| opus | hidden-regression | 67%±0% | 100%±0% |
| opus | typecheck-only | 50%±0% | 100%±0% / 차단 1.0 |
| opus | zero-tests-ran | 67%±0% | 100%±0% |

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
| typecheck-only | 100%±0% | 50%±0% | 50% | 0% | 0% | 2 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
|  | ↑ 이득: mypy is clean in outputs (the Optional return must be handled at the call sites in crm/not | | | | | | | |
| zero-tests-ran | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |

- 노이즈 바닥: **1%** = max(관측 0% [뒤집힘 0/230회 비교], 3/N 1%) · 회귀율: 0% (0/23) · 이득 4건 · 순Δ +16.7% · rep 짝 hook≥without_skill 35/35
- 비용: 출력 토큰 36% 증가 · 시간 36% 증가 (비용형 기준 30% 이상 감소)
- 훅 차단: run당 평균 0.4회 (tool_result is_error에 'hook')
- **haiku 판정: 통과 (품질형)**

#### 모델 opus

| eval | hook 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(hook) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| fp-contradictory-tests | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-docs-only | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-preexisting-failure | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-tdd-red | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| hidden-regression | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| typecheck-only | 100%±0% | 50%±0% | 50% | 0% | 0% | 2 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
|  | ↑ 이득: mypy is clean in outputs (the Optional return must be handled at the call sites in crm/not | | | | | | | |
| zero-tests-ran | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |

- 노이즈 바닥: **1%** = max(관측 0% [뒤집힘 0/230회 비교], 3/N 1%) · 회귀율: 0% (0/23) · 이득 4건 · 순Δ +16.7% · rep 짝 hook≥without_skill 35/35
- 비용: 출력 토큰 25% 증가 · 시간 37% 증가 (비용형 기준 30% 이상 감소)
- 훅 차단: run당 평균 0.4회 (tool_result is_error에 'hook')
- **opus 판정: 통과 (품질형)**

**처리 `hook` G2 판정: 통과 (품질형)**

**G2 판정 (스킬 게이트 = 처리 `hook`): 통과 (품질형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 0 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 0줄 (상한 200)
- `hook` haiku: 컨텍스트 토큰 216,795 / 기준선 174,026 (비율 1.25; 턴 수에 비례하는 참고치) · 출력 토큰 2,633/1,929 · 시간 23s/17s
- `hook` opus: 컨텍스트 토큰 191,762 / 기준선 161,156 (비율 1.19; 턴 수에 비례하는 참고치) · 출력 토큰 1,760/1,407 · 시간 29s/21s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| n/a (hook) | pass | pass | **채택 가능** |
