# gate-eval 보고서: `gate-eval`

- 날짜: 2026-10-23
- Claude Code: 2.1.295 (Claude Code)
- 모델(canonical): ['claude-haiku-5-5', 'claude-opus-5-5']
- 호출 방식: user-invoked (description 상시 미로드)

## G1 정확한 트리거

user-invoked 스킬: description이 모델에 노출되지 않으므로 G1은 해당 없음(사람이 켠다).

## G2 확연한 이득 (품질 또는 비용)

### 모델 haiku

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| measure-toy-skill | 95%±8% | 81%±8% | 14% | 10% | 10% | 1 | 0 | 0/3 |
|  | ↑ 이득: The report reports a baseline-vs-baseline noise floor (flip rate) and both gains and regre | | | | | | | |

- 노이즈 바닥(without 뒤집힘률 평균): 10% · 회귀율: 0% (0/7) · 이득 1건 · 순Δ +14.3% · rep 짝 with≥without 3/3
- 비용: 출력 토큰 91% 감소 · 시간 72% 감소 (비용형 기준 30% 이상)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **haiku 판정: 통과 (품질형)**

### 모델 opus

| eval | with 통과율 (mean±sd) | without 통과율 (mean±sd) | Δ | 노이즈 바닥(without) | 뒤집힘(with) | 이득 | 회귀 | with 미호출 |
|---|---|---|---|---|---|---|---|---|
| measure-toy-skill | 100%±0% | 95%±8% | 5% | 10% | 0% | 0 | 0 | 0/3 |

- 노이즈 바닥(without 뒤집힘률 평균): 10% · 회귀율: 0% (0/7) · 이득 0건 · 순Δ +4.8% · rep 짝 with≥without 3/3
- 비용: 출력 토큰 79% 감소 · 시간 57% 감소 (비용형 기준 30% 이상)
- with 설정에서 스킬 미호출 run: 0 (삼투 조건; 있으면 해당 run의 통과율을 따로 본다)
- **opus 판정: 통과 (비용형)**

**G2 판정: 통과 (비용형: 품질 동률, 비용 확연히 감소)** (필수: 모든 모델에서 회귀율 ≤ 노이즈 바닥. 품질형: 순Δ > 노이즈 바닥 그리고 짝 비교 과반. 비용형: 순Δ가 노이즈 바닥 안이고 출력 토큰 또는 시간 30% 이상 감소)

회귀 사례는 하나씩 정성 검토한다 — 각 run의 `grading.json` evidence와 `transcript.md`를 본다.

## G3 과하지 않은 토큰

- description ≈ 70 토큰 (근사; 상시 로드되지 않음)
- SKILL.md 본문 43줄 (상한 200)
- haiku: 컨텍스트 토큰 with 134,986 / without 945,012 (비율 0.14; 턴 수에 비례하는 참고치) · 출력 토큰 2,500/28,064 · 시간 67s/243s
- opus: 컨텍스트 토큰 with 172,031 / without 428,670 (비율 0.40; 턴 수에 비례하는 참고치) · 출력 토큰 2,470/11,975 · 시간 83s/191s

**G3 판정(잠정): 통과** — 공식 측정은 세션에서 `/skill-doctor`. 규칙: 본문 < 200줄, 토큰 비율 > 1.5인데 G2 실패면 실패.

## 종합

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| n/a | pass | pass | **채택 가능** |
