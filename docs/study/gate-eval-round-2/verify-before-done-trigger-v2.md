# gate-eval 보고서: `verify-before-done`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): []
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 36개(train 22/test 14), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| haiku | train | 21/22 | 90% | 100% |
| haiku | test | 13/14 | 83% | 100% |

- haiku 미발동: `before you say it's done: make the `Cart.total()` change and prove it with the a → 0.33 ['NONE', 'verify-before-done']` / `move the retry helper from utils/net.py into its own module utils/retry.py and u → 0.33 ['NONE', 'verify-before-done']`

| opus | train | 22/22 | 100% | 100% |
| opus | test | 12/14 | 100% | 75% |

- opus 과잉 트리거: `write unit tests for the slugify function, it has none right now. cover accents, → 1.00` / `configure ruff to ignore E501 in the tests folder and sort imports like isort → 1.00`


**판정: 실패** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

## G2 확연한 이득 (품질 또는 비용)

quality 결과 없음.

## G3 과하지 않은 토큰

- description ≈ 131 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 35줄 (상한 200)

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| fail | missing | pass | **백로그 (미입증 게이트 있음)** |
