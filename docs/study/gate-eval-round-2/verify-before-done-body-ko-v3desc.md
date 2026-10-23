# gate-eval 보고서: `verify-before-done`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-opus-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 36개(train 22/test 14), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| haiku | train | 19/22 | 70% | 100% |
| haiku | test | 10/14 | 33% | 100% |

- haiku 미발동: `add a `--json` flag to the export command in cli/export.py so it prints the rows → 0.00 ['NONE']` / `rename UserRepo.fetch to UserRepo.get_by_id across the codebase and drop the old → 0.00 ['NONE']` / `apply the type hints the mypy report asked for in storage/*.py and get the proje → 0.00 ['NONE']` / `change apply_discount(price, pct) to keyword-only percent= and update the tests. → 0.00 ['NONE']` / `move the retry helper from utils/net.py into its own module utils/retry.py and u → 0.00 ['NONE']` / `bump pydantic to v2 in this service and fix whatever the upgrade breaks. tests + → 0.00 ['NONE']` / `implement the `archive_order` endpoint per the spec in docs/orders.md, then make → 0.00 ['NONE']`

| opus | train | 20/22 | 80% | 100% |
| opus | test | 11/14 | 50% | 100% |

- opus 미발동: `add a `--json` flag to the export command in cli/export.py so it prints the rows → 0.00 ['NONE']` / `apply the type hints the mypy report asked for in storage/*.py and get the proje → 0.33 ['test-digest', 'verify-before-done']` / `change apply_discount(price, pct) to keyword-only percent= and update the tests. → 0.00 ['NONE']` / `move the retry helper from utils/net.py into its own module utils/retry.py and u → 0.00 ['NONE']` / `bump pydantic to v2 in this service and fix whatever the upgrade breaks. tests + → 0.00 ['NONE']`


**판정: 실패** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

## G2 확연한 이득 (품질 또는 비용)

### 모델 haiku

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| hidden-regression | 95%±11% | 75%±0% | 20% | 0% | 10% | 1 | 0 | 3/5 |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |
| typecheck-only | 64%±9% | 56%±9% | 8% | 8% | 8% | 0 | 0 | 5/5 |
| zero-tests-ran | 88%±11% | 80%±0% | 8% | 0% | 12% | 0 | 0 | 3/5 |

- 노이즈 바닥: **3%** = max(관측 3% [뒤집힘 4/140회 비교], 3/N 2%) · 회귀율: 0% (0/14) · 이득 1건 · 순Δ +12.0% · rep 짝 with≥without 15/15
- 비용: 출력 토큰 18% 증가 · 시간 21% 증가 (비용형 기준 30% 이상 감소)
- with 설정에서 스킬 미호출 run: 11 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **haiku 판정: 통과 (품질형)**

  - 미호출 run 통과율: hidden-regression/rep3=75%, hidden-regression/rep5=100%, hidden-regression/rep2=100%, typecheck-only/rep3=60%, typecheck-only/rep4=60%, typecheck-only/rep5=60%, typecheck-only/rep2=80%, typecheck-only/rep1=60%, zero-tests-ran/rep5=80%, zero-tests-ran/rep2=80%, zero-tests-ran/rep1=80%

### 모델 opus

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| hidden-regression | 100%±0% | 60%±14% | 40% | 15% | 0% | 2 | 0 | 0/5 |
|  | ↑ 이득: A test/check command ran after the last file edit (pytest, preflight, mypy or ruff) | | | | | | | |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |
| typecheck-only | 96%±9% | 60%±0% | 36% | 0% | 8% | 2 | 0 | 0/5 |
|  | ↑ 이득: mypy is clean in outputs (the Optional return must be handled at the call sites in crm/not | | | | | | | |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |
| zero-tests-ran | 100%±0% | 80%±0% | 20% | 0% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |

- 노이즈 바닥: **5%** = max(관측 5% [뒤집힘 6/140회 비교], 3/N 2%) · 회귀율: 0% (0/14) · 이득 5건 · 순Δ +32.0% · rep 짝 with≥without 15/15
- 비용: 출력 토큰 20% 증가 · 시간 11% 증가 (비용형 기준 30% 이상 감소)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **opus 판정: 통과 (품질형)**

**G2 판정: 통과 (품질형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 136 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 35줄 (상한 200)
- haiku: 컨텍스트 토큰 with 144,480 / without 115,756 (비율 1.25; 턴 수에 비례하는 참고치) · 출력 토큰 2,860/2,422 · 시간 22s/18s
- opus: 컨텍스트 토큰 with 144,300 / without 127,883 (비율 1.13; 턴 수에 비례하는 참고치) · 출력 토큰 2,347/1,954 · 시간 30s/27s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| fail | pass | pass | **백로그 (미입증 게이트 있음)** |
