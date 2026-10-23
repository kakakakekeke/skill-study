# gate-eval 보고서: `verify-before-done`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-opus-5-5']
- 호출 방식: model-invoked

## G1 정확한 트리거

**수행 중 G1** (원칙 §2 "G1 측정 시점"): fixture에서 과제를 실제로 수행시키고 대상 스킬이 언제든 호출되면 발동.
- 측정 전 근거: 발동 조건이 '애플리케이션 코드를 바꾼 뒤, 완료를 선언하기 전'이라 과제 진행 상태에 달려 있고, 평범한 변경 요청 문장에는 나타나지 않는다. 라운드 2에서 시작 시점 라우팅(haiku held-out 11/14)과 수행 중 호출(haiku 11/15, opus 15/15)이 갈렸다. 2026-10-23, 측정 전 작성.
- 경쟁 스킬: flaky-check, repro-first, test-integrity-check, verify-before-done

쿼리 22개(train 14/test 8), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| haiku | train | 6/14 | 0% | 100% |
| haiku | test | 4/8 | 0% | 100% |

- haiku 미발동: `Cart.total() should take a currency argument (default 'USD') and return the form → 0.00 ['NONE']` / `rename format_price to render_price across the package → 0.00 ['NONE']` / `add a WINTER15 promo and make promo codes case-sensitive from now on → 0.00 ['NONE']` / `add an optional phone field to Contact (default None) and mention it in welcome_ → 0.00 ['NONE']` / `reminder_subject should use the contact's full name, not just the first word → 0.00 ['NONE']` / `add remove_stock(conn, sku, qty) to inventory.py; it should refuse to take stock → 0.00 ['NONE']` / `rename the items table to stock in the schema and every query → 0.00 ['NONE']` / `let connect() take a pathlib.Path as well as a str → 0.00 ['NONE']` / `we need fractional discounts like 12.5%. make Line.discount_pct and apply_discou → 0.00 ['NONE']` / `rename Directory.get to Directory.by_id → 0.00 ['NONE']` / `find_contact에 이름으로도 찾을 수 있게 name 인자를 추가해줘. id나 name 중 하나만 받으면 돼 → 0.00 ['NONE']` / `low_stock should return (sku, qty) pairs instead of just the skus → 0.00 ['NONE']`

| opus | train | 10/14 | 50% | 100% |
| opus | test | 6/8 | 50% | 100% |

- opus 미발동: `add a WINTER15 promo and make promo codes case-sensitive from now on → 0.33 ['NONE', 'verify-before-done']` / `add an optional phone field to Contact (default None) and mention it in welcome_ → 0.00 ['NONE']` / `reminder_subject should use the contact's full name, not just the first word → 0.00 ['NONE']` / `let connect() take a pathlib.Path as well as a str → 0.00 ['NONE']` / `find_contact에 이름으로도 찾을 수 있게 name 인자를 추가해줘. id나 name 중 하나만 받으면 돼 → 0.00 ['NONE']` / `low_stock should return (sku, qty) pairs instead of just the skus → 0.00 ['NONE']`


**판정: 실패** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

참고치: 시작 시점 라우팅 (판정에 쓰지 않음)

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| haiku | train | 22/22 | 100% | 100% |
| haiku | test | 12/14 | 67% | 100% |
| opus | train | 22/22 | 100% | 100% |
| opus | test | 14/14 | 100% | 100% |

## G2 확연한 이득 (품질 또는 비용)

조건: 기준선 `without_skill`(구성요소 없음) vs 처리 `with_skill`(skill). 각 처리는 기준선과 따로 비교한다.

### 처리 `with_skill` (구성요소 skill) vs `without_skill`

#### 모델 haiku

| eval | with_skill 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(with_skill) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| hidden-regression | 85%±14% | 75%±0% | 10% | 0% | 15% | 0 | 0 | 3/5 |
| typecheck-only | 68%±11% | 60%±0% | 8% | 0% | 20% | 1 | 0 | 5/5 |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |
| zero-tests-ran | 96%±9% | 80%±0% | 16% | 0% | 8% | 1 | 0 | 1/5 |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |

- 노이즈 바닥: **2%** = max(관측 0% [뒤집힘 0/140회 비교], 3/N 2%) · 회귀율: 0% (0/14) · 이득 2건 · 순Δ +11.3% · rep 짝 with_skill≥without_skill 15/15
- 비용: 출력 토큰 6% 증가 · 시간 8% 증가 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 9 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **haiku 판정: 통과 (품질형)**

  - 미호출 run 통과율: hidden-regression/rep3=75%, hidden-regression/rep5=75%, hidden-regression/rep1=75%, typecheck-only/rep3=80%, typecheck-only/rep4=60%, typecheck-only/rep5=60%, typecheck-only/rep2=80%, typecheck-only/rep1=60%, zero-tests-ran/rep3=80%

#### 모델 opus

| eval | with_skill 통과율 (mean±sd) | without_skill 통과율 (mean±sd) | Δ | 노이즈 바닥(without_skill) | 뒤집힘(with_skill) | 이득 | 회귀 | 스킬 미호출 |
|---|---|---|---|---|---|---|---|---|
| hidden-regression | 70%±11% | 50%±0% | 20% | 0% | 25% | 1 | 0 | 0/5 |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |
| typecheck-only | 96%±9% | 52%±11% | 44% | 16% | 8% | 2 | 0 | 0/5 |
|  | ↑ 이득: mypy is clean in outputs (the Optional return must be handled at the call sites in crm/not | | | | | | | |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |
| zero-tests-ran | 100%±0% | 80%±0% | 20% | 0% | 0% | 1 | 0 | 0/5 |
|  | ↑ 이득: The final message cites the concrete verification command that was run after the last edit | | | | | | | |

- 노이즈 바닥: **5%** = max(관측 5% [뒤집힘 8/140회 비교], 3/N 2%) · 회귀율: 0% (0/14) · 이득 4건 · 순Δ +28.0% · rep 짝 with_skill≥without_skill 15/15
- 비용: 출력 토큰 13% 증가 · 시간 12% 증가 (비용형 기준 30% 이상 감소)
- 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **opus 판정: 통과 (품질형)**

**처리 `with_skill` G2 판정: 통과 (품질형)**

**G2 판정 (스킬 게이트 = 처리 `with_skill`): 통과 (품질형)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 136 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 35줄 (상한 200)
- `with_skill` haiku: 컨텍스트 토큰 201,089 / 기준선 200,929 (비율 1.00; 턴 수에 비례하는 참고치) · 출력 토큰 2,745/2,592 · 시간 21s/19s
- `with_skill` opus: 컨텍스트 토큰 221,888 / 기준선 190,955 (비율 1.16; 턴 수에 비례하는 참고치) · 출력 토큰 2,076/1,830 · 시간 28s/25s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| fail | pass | pass | **백로그 (미입증 게이트 있음)** |
