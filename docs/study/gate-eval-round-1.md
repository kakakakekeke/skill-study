# 자율 제작 라운드 1: 네 스킬의 세 게이트 측정 기록 (2026-10-22)

> 증거 자료. 규칙 변경은 `docs/principles.md`에서만. 보고서 사본은 `gate-eval-round-1/`, run 단위 원본(트랜스크립트·채점)은 각 스킬의 `evals/results/`(gitignore, 로컬 보존).

- 환경: Claude Code 2.1.295, 모델 `claude-haiku-5-5`·`claude-opus-5-5`, grader `sonnet`. 케이스당 3회, with/without.
- 도구: `skills/gate-eval/scripts/` (이 라운드에서 만든 하네스).

## 하네스에서 발견한 것

1. **skill-creator의 `run_eval.py`는 CLI 2.1.295에서 트리거를 감지하지 못한다.** 커맨드 파일 방식으로 description을 노출하고 `--include-partial-messages` 스트림에서 Skill 도구 호출을 잡는데, 모델이 실제로 `Skill` 도구를 첫 도구로 호출한 쿼리(opus, 직접 확인)에서도 0으로 집계됐다. 20쿼리×3회×2모델 두 스킬 모두 재현율 0. 원인은 스트림 이벤트 형식 변화로 추정(partial json delta 누적이 비어 `content_block_stop`에서 False 반환). → 자체 라우팅 결정 측정으로 대체(`trigger_run.py`).
2. 자체 방식의 한계: "코드가 없으니 쓸 스킬을 고르라"는 결정 프록시다. 과제 수행 중 실제 호출률은 G2 표의 "with 미호출" 열로 따로 본다. 두 측정이 같은 것을 재지 않는다.
3. 하네스 자체의 버그 3건(이 라운드에서 수정): (a) `--out`을 상대 경로로 주면 script 검사가 `cwd=run_dir`에서 경로를 두 번 붙여 전부 실패 → 절대 경로로 통일. (b) 대상 스킬이 만든 산출물(`outputs/`) 안의 중첩 `grading.json`을 집계에 포함 → 제외. (c) 슬래시로 전개되는 user-invoked 스킬은 Skill 도구 호출이 없어 "미호출"로 집계 → 프롬프트가 `/name`으로 시작하면 호출로 인정.
4. 네 스킬 모두 G1 100%는 should-not 세트가 충분히 어렵지 않다는 신호일 수 있다. 다음 라운드에서 근접 사례(예: test-digest vs flaky-check vs repro-first 사이 경계 문장)를 더 넣어 떨어지는지 본다.

## 결과 요약

| 스킬 | G1 (test 구간, haiku/opus) | G2 순Δ haiku / opus | 회귀 | 노이즈 바닥 | G3 토큰 비율 haiku / opus | 결론 |
|---|---|---|---|---|---|---|
| test-digest | 8/8 · 8/8 | +7% / +2% | 0 | 0% | 1.05 / 1.31 | 채택 가능 (이득 작음, 아래 메모) |
| repro-first | 8/8 · 8/8 | +26% / +20% | 0 | 11% | — | 채택 가능 |
| flaky-check (2차) | 8/8 · 8/8 | +0.4% / +0.4% | 0 | 4% | 0.71 / 1.16 | 경계 통과 — 품질 동률, 이득은 시간·출력 토큰 |
| gate-eval | n/a (user-invoked) | +14% / +5% | 0 | 10~15% | **0.49 / 0.40** | 채택 가능 |

## 스킬별 메모

### test-digest
- 이득은 토큰 규율 assertion("가장 긴 Bash 출력 80줄 이하") 1건(haiku, ci-log). 원인 식별 assertion은 스킬 유무와 무관하게 통과 → **비변별**. opus는 압축 없이도 원인을 다 찾는다.
- "parse_range가 범위 끝을 빠뜨린다" assertion은 양쪽 모두 실패(11/12). grader가 "two tests 둘 다 언급"을 요구하는 문장 해석을 엄격히 한 것으로 보임. 다음 라운드에서 문장을 둘로 나눈다.
- 짧은 출력(all-passing) 케이스에서는 스킬이 호출되지 않았다(의도대로). 그 케이스는 "회귀 없음" 확인용.
- 컨텍스트 토큰 비율이 1보다 큰 이유: 측정값이 턴마다의 캐시 읽기 누적합이라 **턴 수**에 비례한다. 스킬 호출이 한 턴을 더 쓴다. 입력 토큰 절약은 Bash 출력 줄 수(assertion)로 보는 게 맞다.

### repro-first
- 이득이 일관: "첫 소스 수정 전에 실패 명령 실행" 결정적 검사가 세 케이스 모두 with에서만 통과. opus도 without에서는 median 케이스에서 재현 없이 바로 고치는 경향(61%).
- 회귀 0, 노이즈 바닥 11%(without 쪽이 더 흔들림).

### gate-eval
- 비교: `/gate-eval skills/toy-greeter --models haiku --reps 2` vs 같은 뜻의 자연어 요청(스킬 없음). without에서 모델은 측정을 손으로 짜느라 토큰·시간을 2~2.5배 쓰고(opus 출력 토큰 11,975 vs 2,470), 노이즈 바닥·이득/회귀 쌍 같은 항목을 빠뜨리는 경우가 있었다(haiku 이득 1건).
- 이 스킬의 효용은 "같은 보고서가 매번 같은 형식으로 나온다"(목적 3)와 토큰 절반이다. G3 비율 0.4~0.5는 네 스킬 중 유일하게 1 미만.

### flaky-check (1차 → 2차)
- 1차 haiku 회귀: 스킬이 권한 `--keep-logs` 뒤 모델이 로그 디렉터리를 `ls`해 Bash 출력 80~118줄 → 토큰 규율 assertion 실패. 스킬이 **만든** 회귀. 수정: 실패 run 로그만 남기고 첫 파일 경로를 출력에 적어 `ls`가 필요 없게 함, SKILL.md에 "디렉터리를 ls하거나 전부 cat하면 아낀 토큰을 되돌려준다" 한 줄.
- 1차 grader 오류 1건(grader가 도구를 부르려다 구조화 출력 없음) → 재시도 3회 추가 후 재채점.
- 2차에서 드러난 assertion 결함: "checksum mismatch도 언급" assertion은 픽스처의 5% 확률 사건이 20회 표본에 **잡히는지**에 의존 → 스킬과 무관한 뒤집힘. "둘 이상의 서로 다른 오류가 관찰됐으면 분리 보고"로 재작성(결과를 보고 assertion을 고친 것이므로 여기 기록).
- 2차 결과: 두 모델 모두 회귀 0, 순Δ +0.4%(사실상 동률), haiku 토큰 규율 이득 1건. 시간은 haiku 21s vs 88s, opus 27s vs 68s, 출력 토큰 절반. 규칙상 통과지만 **품질 이득은 없다고 보는 게 정직하다**. G2 규칙(순Δ>0)으로는 통과 못 함. **규칙 질문**: 품질 동률이고 비용이 확연히 낮은 스킬을 G2 실패로 봐야 하는가. principles §2는 "확연한 품질 향상"이라고만 쓴다. 다음 원칙 검토 항목.

## 2026-10-23 추가: 어려운 트리거 세트

G1 100%가 문항이 쉬워서였는지 보려고, 스킬 셋 사이의 경계 문장·한국어·키워드는 겹치지만 다른 도구가 맞는 근접 사례를 넣어 스킬당 34~36문항(should 15~16)으로 늘렸다. 보고서 사본은 `gate-eval-round-1/*-trigger-hard-v*.md`.

| 스킬 | v1 (원 description) haiku / opus | 조치 | 최종 haiku / opus (test 구간) |
|---|---|---|---|
| test-digest | 34/36 (train 미발동 2: "npm test 6~7 failures", "tsc hundreds of errors", 각 0.33) / 36/36 | description에 "npm/yarn test", "type check", "several failing tests, hundreds of compiler errors" 단서와 "이미 짚어낸 실패를 고치는 건 아님" 추가 | 36/36 / 36/36 (14/14) |
| repro-first | 36/36 / 36/36 | 없음 | — |
| flaky-check | 33/34 (test 과잉 1: "why would a test pass locally and fail in CI? usual reasons" 0.67) / 34/34 | v2: "구체적 명령이 있을 때만" 제한 추가 → haiku 미발동 2건으로 **역효과**(느슨하게 지칭한 "the cypress test", "the integration suite"에서 빠짐). v3: "느슨하게 지칭해도 이름 붙은 테스트·스위트·CI 단계면 됨, 돌릴 것이 없는 일반 질문만 제외"로 완화 | 33/34 / 34/34 (test 12/13, 미발동 1: "retry-until-pass… how bad is it actually" 0.33) |

배운 것:
- 어려운 세트에서도 세 스킬 모두 규칙상 통과. 그러나 100%는 깨졌고, haiku가 opus보다 설명문에 민감하다. 흔들린 문항은 모두 3회 중 1~2회만 켜진 **경계 문항**이라 반복 3회가 필요했다.
- 부정 조건 한 줄은 재현율을 쉽게 깎는다(v2). 제외 조건은 "무엇이 없을 때"로 좁게 쓰고, 포함 범위를 먼저 넓게 적는 편이 안전했다.
- flaky-check의 과잉 트리거 문항은 **test 구간**에 있었다. 그걸 보고 description을 고쳤으므로 v3의 test 점수는 완전한 held-out이 아니다. 다음 라운드에 같은 종류(개념 질문) 문항을 새로 넣어 다시 본다.
- 남은 미발동 1건("retry-until-pass… how bad is it")은 더 손대지 않았다. 한 문항에 맞춰 고치면 과적합이다.
