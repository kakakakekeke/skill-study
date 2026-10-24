# gate-eval 보고서: `verify-on-stop`

- 날짜: 2026-10-24
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-sonnet-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

훅 전용(SKILL.md 없음): 트리거는 결정적이다. G1은 거짓양성으로 보며, G2 표의 오탐 fixture(`fp-*`) 회귀와 차단 횟수로 판정한다(원칙 §3.2).

## G2 확연한 이득 (품질 또는 비용)

조건: 기준선 `without_skill`(구성요소 없음) vs 처리 `hook`(hook). 각 처리는 기준선과 따로 비교한다.

### 조건 나란히 (통과율 mean±sd / 훅 차단 평균)

| 모델 | eval | `without_skill` | `hook` |
|---|---|---|---|
| sonnet | fp-contradictory-tests | 40%±55% | 40%±55% / 차단 1.0 |
| sonnet | fp-docs-only | 100%±0% | 100%±0% |
| sonnet | fp-preexisting-failure | 100%±0% | 100%±0% |
| sonnet | fp-tdd-red | 100%±0% | 100%±0% / 차단 1.0 |
| sonnet | hidden-regression | 67%±0% | 100%±0% |
| sonnet | typecheck-only | 55%±21% | 95%±11% |
| sonnet | zero-tests-ran | 67%±0% | 93%±15% |

### 처리 `hook` (구성요소 hook) vs `without_skill`

#### 모델 sonnet

| eval | hook 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(hook) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| fp-contradictory-tests | 40%±55% | 40%±55% | 0% | 60% | 60% | 0 | 0 | n/a |
| fp-docs-only | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-preexisting-failure | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| fp-tdd-red | 100%±0% | 100%±0% | 0% | 0% | 0% | 0 | 0 | n/a |
| hidden-regression | 100%±0% | 67%±0% | 33% | 0% | 0% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| typecheck-only | 95%±11% | 55%±21% | 40% | 30% | 10% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |
| zero-tests-ran | 93%±15% | 67%±0% | 27% | 0% | 13% | 1 | 0 | n/a |
|  | ↑ 이득: The user is shown the verification result after the last edit (hook message, or final mess | | | | | | | |

- 노이즈 바닥: **13%** = max(관측 13% [뒤집힘 36/230회 비교], 3/N 1%) · 회귀율: 0% (0/23) · 이득 3건 · 순Δ +14.3% · rep 짝 hook≥without_skill 34/35
- 비용: 출력 토큰 11% 증가 · 시간 14% 증가 (비용형 기준 30% 이상 감소)
- 훅 차단: run당 평균 0.3회 (PreToolUse 거부 + Stop hook feedback)
- **sonnet 판정: 통과 (품질형)**

**처리 `hook` G2 판정: 통과 (품질형)**

**G2 판정 (스킬 게이트 = 처리 `hook`): 통과 (품질형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 0 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 0줄 (상한 200)
- `hook` sonnet: 컨텍스트 토큰 169,110 / 기준선 157,119 (비율 1.08; 턴 수에 비례하는 참고치) · 출력 토큰 1,591/1,428 · 시간 25s/22s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| n/a (hook) | pass | pass | **채택 가능** |
