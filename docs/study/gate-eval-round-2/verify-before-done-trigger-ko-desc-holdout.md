# gate-eval 보고서: `verify-before-done`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): []
- 호출 방식: model-invoked

## G1 정확한 트리거

쿼리 14개(train 0/test 14), 쿼리당 3회, 임계 0.5.

| 모델 | 구간 | 통과 | should-fire 재현율 | should-not-fire 정밀도 |
|---|---|---|---|---|
| haiku | train | 0/0 | — | — |
| haiku | test | 9/14 | 29% | 100% |

- haiku 미발동: `switch the cache key in services/cache.py from str(user_id) to f"user:{user_id}" → 0.33 ['NONE', 'verify-before-done']` / `the Order dataclass needs a `currency` field defaulting to 'USD'. add it and thr → 0.00 ['NONE']` / `finish the pagination change in repo/listing.py — I started it yesterday, it's h → 0.33 ['NONE', 'verify-before-done']` / `make parse_duration accept '1h30m' as well as plain seconds. there's a pytest su → 0.00 ['NONE']` / `utils/dates.py의 to_utc 함수가 naive datetime도 받게 바꿔줘. 호출하는 곳이 몇 군데 있을 거야 → 0.00 ['NONE']`

| opus | train | 0/0 | — | — |
| opus | test | 14/14 | 100% | 100% |

**판정: 실패** (규칙: 모델마다 held-out test에서 과잉·미발동 각각 1건 이하)

## G2 확연한 이득 (품질 또는 비용)

quality 결과 없음.

## G3 과하지 않은 토큰

- description ≈ 136 토큰 (근사; 상시 로드됨)
- SKILL.md 본문 35줄 (상한 200)

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| fail | missing | pass | **백로그 (미입증 게이트 있음)** |
