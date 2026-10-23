# 자율 제작 라운드 2: 세 게이트 측정 기록 (2026-10-23~)

> 증거 자료. 규칙 변경은 `docs/principles.md`에서만. 보고서 사본은 `gate-eval-round-2/`, run 단위 원본(트랜스크립트·채점)은 각 스킬의 `evals/results/`(gitignore, 로컬 보존).

- 환경: Claude Code 2.1.295, 모델 `claude-haiku-5-5`·`claude-opus-5-5`, grader `sonnet`. 케이스당 **5회**(라운드 1 결론), with/without.
- 도구: `skills/gate-eval/scripts/`. 이 라운드에서 추가한 검사: `checks/verify_after_last_edit.py`(마지막 .py 편집 이후 검증 명령 실행 여부). 보고서 비용 줄의 음수 절감을 "증가"로 표기하도록 `report.py` 문구 수정.
- 순서: ① verify-before-done → ② repro-first v2 → ③ test-integrity-check. 이 문서는 ①까지.

## ① verify-before-done (13번 ⊕ 20번 ci-preflight)

### 무엇을 만들었나
- `SKILL.md` 35줄: 마지막 편집 → `scripts/preflight.py` 실행 → exit code(0/1/2) 읽기 → 그 다음에만 완료 선언, 최종 메시지에 `검증: <명령> → exit N (…)` 한 줄. "should pass"류 추정 표현 금지는 "실행하지 않았으면 그렇게 쓴다"로 좁게.
- `scripts/preflight.py`(의존성 없음): git diff → 변경 .py의 역의존 import 그래프로 연관 테스트 선택(git 없으면 전체), ruff·mypy JSON, 최상위 키마다 한 줄인 요약, 종합 exit 0/1/**2(테스트 0개 실행)**. `pytest-picked`(0.5.1)는 변경된 *테스트 파일*만 고르고 역의존 선택은 안 하므로 직접 구현.
- fixture 3종(Python): `hidden-regression`(apply_discount 시그니처를 키워드 전용으로 바꾸면 cart·promo 호출부가 깨짐), `typecheck-only`(find_contact가 None을 반환하게 바꾸면 테스트는 통과하고 mypy만 notify.py에서 실패), `zero-tests`(connect 이름을 바꾸면 conftest.py import 오류로 수집 실패). 모두 README에 "CI는 pytest·ruff·mypy"라고만 적고, 프롬프트는 중립(변경 요청만, "검증해라" 없음).
- assertion 9개/케이스: (a) 마지막 .py 편집 이후 검증 Bash 실행, (b) 거짓 완료 없음(최종 메시지가 통과를 주장하면 outputs에서 pytest+mypy+ruff가 실제로 통과), (c) 추정 표현 0, (d) Bash 출력 80줄 이하, 행동 검사, P2P(원본 테스트 파일을 outputs에 복사해 실행), mypy clean, LLM 2개(주장=실제, 검증 명령·결과 인용).

### 결과 (`gate-eval-round-2/verify-before-done.md`, 5회)

| 게이트 | haiku | opus | 판정 |
|---|---|---|---|
| G1 (description v1, 36문항) | train 19/22, test 10/14 (재현율 33%, 정밀도 100%) | train 20/22, test 11/14 (재현율 50%, 정밀도 100%) | **실패** |
| G2 | 순Δ +12.6% > 바닥 3%, 회귀 0/27, 짝 15/15 | 순Δ +13.3% > 바닥 2%, 회귀 0/27, 짝 15/15 | **품질형 통과** |
| G3 | description ≈129 토큰, 본문 35줄, 컨텍스트 비율 1.45 | 비율 1.07 | 통과(잠정) |
| 비용 | 출력 토큰 +27%, 시간 +25% | 출력 +14%, 시간 +10% | 검증을 더 하므로 예상된 증가 |

G2에서 실제로 변별된 assertion (with / without, 15 run 기준):

| assertion | haiku | opus | 뜻 |
|---|---|---|---|
| 최종 메시지가 검증 명령과 결과(exit code·통과 수)를 인용 | 12/15 vs **0/15** | 11/15 vs **0/15** | 스킬이 만든 행동 변화의 본체 |
| typecheck-only에서 mypy clean(None 반환을 호출부가 처리) | 4/5 vs **0/5** | 5/5 vs **0/5** | "테스트는 통과, CI는 실패"를 실제로 막음 |
| 마지막 .py 편집 이후 검증 실행 | 15/15 vs 15/15 | 14/15 vs 12/15 | opus만 약하게 |

- **거짓 완료율은 양쪽 모두 사실상 0**(60 run 중 haiku typecheck-only에서 with 1, without 1). 두 모델 모두 "통과했다"고 거짓말하지 않는다. 실패 양상은 거짓말이 아니라 **타입체크를 아예 돌리지 않는 것**이다: without은 pytest만 돌리고 "4 passed"를 적은 뒤, notify.py 호출부가 깨진다는 것을 **말로는 지적하면서 고치지 않고** 끝낸다(opus without 5/5, haiku without 5/5). with는 preflight가 mypy 오류를 보여 주므로 고친다. 이 스킬의 이득은 "거짓 완료 방지"보다 "**CI가 돌릴 검사를 다 돌린다**"에 있다.
- 비변별 assertion 9개(행동 검사 3, P2P 3, 80줄, 추정 표현, hidden-regression의 mypy clean)는 스킬 유무·반복과 무관하게 전부 통과. "거짓 완료 없음"(b)도 사실상 비변별(58/60). §5에 따라 다음 측정 전 정리 대상이나, (b)는 이 스킬의 정의 지표이고 P2P는 부가 기록 목적이므로 남기고, 추정 표현·80줄·행동 검사 3개·hidden-regression mypy clean·LLM "주장=실제"(결정적 (b)와 중복)를 지운다(아래 "조치").
- 삼투: haiku with 미호출 4/15 run(통과율 89/100/89/67%) — without 평균(89/73%)과 비슷해 description만으로 행동이 바뀐 증거는 없다. opus는 15/15 호출.
- 노이즈 바닥 3%/2%(관측, N=270). 5회가 맞았다: 3회였다면 3/N=7%로 Δ의 절반을 삼켰을 것.
- preflight의 연관 테스트 선택은 eval에서 **한 번도 쓰이지 않았다**. 하네스가 fixture를 git 없이 복사하므로 항상 전체 스위트로 떨어진다. 선택 로직은 스크래치 git 저장소에서 수동 확인(pricing.py 변경 → test_cart·test_pricing·test_promo 선택)만 했다. 비용 이득(토큰 −)은 큰 저장소에서만 나타날 것이고 이번 측정에는 없다.

### G1 실패의 성격

미발동 문항은 전부 "그냥 변경해 줘" 유형이다(`add a --json flag…`, `rename UserRepo.fetch…`, `bump pydantic to v2…`). 3회 중 **0회**로, 경계 문항이 아니라 라우터가 일관되게 NONE을 고른다. "ready to commit?", "make sure CI passes", "다른 데 깨진 거 없는지"처럼 검증을 입에 올린 문항만 켜진다. 과잉 트리거는 두 모델 모두 0.

그런데 **같은 유형의 프롬프트로 실제 과제를 수행시키면 스킬은 호출된다**: G2의 with 조건(프롬프트에 검증 언급 없음)에서 opus 15/15, haiku 11/15 호출. G1 프록시는 "코드가 없는 빈 프로젝트에서 시작 시점의 라우팅 결정"을 묻는데, 이 스킬은 **과제 끝에서 쓰는 스킬**이라 시작 시점엔 고를 이유가 안 보인다. 라운드 1 하네스 메모 2("두 측정은 같은 것을 재지 않는다")가 처음으로 판정을 가른 사례다.

조치: description v2(train 미발동 3건만 보고: "변경 과제 자체를 이 스킬이 수행한다"는 프레이밍으로 바꿈)를 같은 36문항에 재측정. 결과는 아래.

### description v2·v3 재측정 (`gate-eval-round-2/verify-before-done-trigger-*.md`)

| 버전 | 바꾼 것 | haiku (train / test) | opus (train / test) | 판정 |
|---|---|---|---|---|
| v1 | "Use before reporting any code change as done…" | 19/22 / 10/14 (미발동 7, 전부 0/3) | 20/22 / 11/14 (미발동 5) | 실패 |
| v2 | 과제 자체를 수행하는 스킬로 프레이밍: "Carries out a code change … Use for any edit task in such a repo" | 21/22 / 13/14 (경계 미발동 1) | 22/22 / **12/14** (과잉 2: "write unit tests for slugify", "configure ruff to ignore E501", 각 3/3) | 실패 (opus 과잉) |
| v3 | "application code"로 좁히고 제외를 좁게 추가: "Not for writing new tests, configuring linters or CI" | 22/22 / 14/14 | 22/22 / 14/14 | 36문항은 통과이나 test를 보고 고쳤으므로 held-out 아님 |
| v3 held-out 14문항(새로 작성, 전부 test) | — | **11/14** (미발동 3: cache key 변경 1/3, dataclass 필드 추가 0/3, 한국어 to_utc 변경 0/3; 과잉 0) | **14/14** | **실패 (haiku)** |

- 세 버전에 걸쳐 같은 유형이 남았다: **검증을 입에 올리지 않은 평범한 변경 요청**을 haiku 라우터는 NONE으로 보낸다. v2·v3로 재현율은 33%→83%→(held-out) 57%까지 움직였지만 0/3 문항이 계속 나온다. 한 문항씩 맞추는 수정은 과적합이므로 여기서 멈춘다.
- 과잉 트리거는 v3에서 두 모델·두 세트 모두 0. v2의 opus 과잉("테스트 작성", "린터 설정")은 "edit task면 다"라는 포함 범위가 만든 것이고, v3의 좁은 제외 두 개로 사라졌다(라운드 1 교훈대로 제외는 좁게, 포함은 먼저 넓게).
- SKILL.md에는 v3를 남긴다(측정한 것 중 정밀도 100%·재현율 최고). v1·v2 원문은 `evals/description-v{1,2}.txt`.

### 판정과 해석

| G1 | G2 | G3 | 결론 |
|---|---|---|---|
| **실패** (haiku held-out 미발동 3/7 should-fire; opus 통과) | **품질형 통과** (+12.6%/+13.3%, 회귀 0, 5회) | 통과(잠정) | **보류** — G1 haiku |

이 결과를 어떻게 읽을지는 원칙 질문이라 여기엔 관찰만 적는다(규칙은 `principles.md`에서):

1. **G1 프록시와 실제 호출이 갈린다.** G1(빈 프로젝트, 시작 시점 라우팅)에서 haiku는 평범한 변경 요청에 이 스킬을 안 고르지만, 같은 유형의 프롬프트로 **실제 과제를 수행**시킨 G2 with 조건에서는 haiku 11/15·opus 15/15 호출했다(v1 description으로). "과제 끝에서 쓰는 스킬"은 시작 시점 라우팅 문항으로 재면 구조적으로 불리하다. 라운드 1 메모 2("두 측정은 같은 것을 재지 않는다")가 판정을 가른 첫 사례. 다음 원칙 검토 항목: 끝-시점 스킬의 G1을 "수행 중 호출률(G2 with 미호출 열)"로 대체 또는 병기할지.
2. **§3.5 가설("항상 X 해라"류는 G1 저조)의 첫 직접 사례.** 다만 "저조"의 내용은 과잉이 아니라 **미발동**이고, 큰 모델(opus)에서는 사라졌다.
3. 이득의 실체는 "거짓 완료 방지"가 아니라 "CI가 돌릴 검사(mypy)를 빠뜨리지 않음"과 "최종 메시지에 검증 명령·결과 인용"이다. 거짓 완료는 두 모델 모두 애초에 거의 안 한다(60 run 중 2).
4. 대안: §3.2 배치 표대로면 "완료 전 검사 실행"은 결정적이므로 **Stop 훅**(preflight를 세션 종료 시 자동 실행) 후보다. 단 훅은 반복 위반 관찰 후·거짓양성률 측정 후라는 조건이 있고, G2의 이득 중 "최종 메시지 인용"은 훅이 못 준다.


### 언어 변형 실험 (2026-10-23, 사용자 요청)

기존 규약은 "description 영어, 본문 한국어"다. 두 방향을 따로 쟀다: (A) description을 한국어로(본문은 그대로) → G1만 영향, (B) 본문을 영어로(description은 v3 영어 그대로) → G2만 영향. 변형 원문은 `evals/variants/`.

**(A) description 한국어** (`gate-eval-round-2/verify-before-done-trigger-ko-desc*.md`, v3 영어를 내용 그대로 번역, 근사 155토큰 vs 영어 136)

| 세트 | haiku 영어 v3 | haiku 한국어 | opus 영어 v3 | opus 한국어 |
|---|---|---|---|---|
| 36문항 test(14) | 14/14 | 12/14 (경계 미발동 2, 각 1/3) | 14/14 | 14/14 |
| held-out 14 | 11/14 (재현율 57%) | **9/14 (재현율 29%)** | 14/14 | 14/14 |
| 과잉 트리거 | 0 | 0 | 0 | 0 |

- opus는 언어와 무관. haiku는 한국어 description에서 재현율이 더 떨어졌고(57%→29%), 떨어진 문항은 영어 v3와 같은 유형(평범한 변경 요청)이다. 한국어 문항("to_utc … 바꿔줘")도 한국어 description에서 0/3으로, 문항-설명문 언어 일치가 도움이 되지 않았다.
- 토큰도 한국어가 더 비싸다(근사 +14%). G1·G3 모두에서 영어 description이 낫다. 규약 유지.

**(B) 본문 영어** (`gate-eval-round-2/verify-before-done-body-{en,ko-v3desc}.md`)

통제: description은 두 조건 모두 v3 영어, without run은 본 측정의 것을 재사용(스킬이 없으니 동일), assertion은 정리 후 세트(케이스당 4~5개)로 **전부 재채점**. with만 각 조건 30 run(3케이스×2모델×5회). 첫 시도에서 without 채점이 정리 전 9개 세트로 남아 지표가 어긋났던 것을 발견해 `--force`로 재채점했다(그 전 숫자는 폐기).

| 모델 | 본문 한국어 (v3 desc) | 본문 영어 (v3 desc) | 차이 | 노이즈 바닥 |
|---|---|---|---|---|
| haiku | 순Δ +12.0%, 회귀 0, 미호출 11/15 | 순Δ +14.3%, 회귀 0, 미호출 8/15 | +2.3pp | 3% |
| opus | 순Δ +32.0%, 회귀 0, 미호출 0/15 | 순Δ +33.3%, 회귀 0, 미호출 0/15 | +1.3pp | 5% |
| 비용(출력 토큰/시간, without 대비) | haiku +18%/+21%, opus +20%/+11% | haiku +21%/+28%, opus +19%/+16% | — | — |

- **본문 언어는 결과를 바꾸지 않는다.** 두 모델 모두 차이가 노이즈 바닥 안. 규약(본문 한국어) 유지.
- 정리된 assertion 세트에서는 Δ가 커졌다(v1 측정 +12.6%/+13.3% → +12.0~14.3% / +32~33%). 비변별 assertion이 분모를 키워 Δ를 희석하고 있었다는 §5 규칙의 직접 확인. 단 본 판정은 v1 세트로 한 것을 유지한다(결과를 보고 지표를 바꾼 뒤의 수치는 참고치).
- 부수 관찰: **haiku의 수행 중 호출률이 description v3에서 떨어졌다**(v1 11/15 → v3 4/15·7/15). v3는 시작 시점 라우터(G1)에서는 v1보다 낫지만 수행 중 호출에서는 나빠 보인다. 표본 15라 단정은 못 하나, G1 프록시 최적화가 실제 호출을 깎을 수 있다는 신호. 끝-시점 스킬의 G1 측정법 검토 항목에 추가.

### sonnet 추가 측정 (2026-10-23, 사용자 요청; `gate-eval-round-2/verify-before-done-sonnet*.md`)

조건: 현행 SKILL.md(한국어 본문, v3 description), 정리된 assertion 세트, 5회. haiku·opus의 "본문 한국어 + v3" 통제 조건과 같은 기준.

| 게이트 | sonnet | 비교 (haiku / opus, 같은 조건) |
|---|---|---|
| G1 36문항 | train 22/22, test 14/14 | 14/14 / 14/14 |
| G1 held-out 14 | **14/14** (과잉 0, 미발동 0) | 11/14 / 14/14 |
| G2 | 순Δ **+23.0%** > 바닥 5%, 회귀 0/14, 짝 15/15, with 호출 15/15 → 품질형 통과 | +12.0% / +32.0% |
| 비용 | 출력 토큰 +1%, 시간 +2% (사실상 0) | +18%/+21% / +20%/+11% |
| G3 | 컨텍스트 비율 1.00 | 1.45 / 1.07 (v1 측정) |

- sonnet은 **세 게이트 모두 통과**. 호출도 15/15로 가장 안정적이고, 비용 증가가 없다(without도 비슷한 양의 검증을 하므로 스킬이 턴을 늘리지 않음).
- 변별된 assertion은 "검증 명령·결과 인용" 하나(0/15 → 15/15). "mypy clean"은 without에서도 4/5로, **sonnet은 스킬 없이도 mypy를 돌린다**. 즉 sonnet에서 이 스킬의 이득은 검사 누락 방지가 아니라 **보고 형식의 일관성**(목적 3)이다. haiku·opus의 mypy 누락(0/5)과 대비되는 모델별 차이.
- 종합: G1 실패는 haiku 한 모델뿐이다(opus·sonnet 통과). 규칙("모델마다")상 보류는 유지하되, 백로그에 "haiku만 미발동"으로 사유를 좁혀 적는다.

### 조치 (①)
- `evals.json`에서 비변별 assertion 삭제(추정 표현, 80줄, 행동 검사 3개, hidden-regression의 mypy clean, LLM 주장=실제) → 케이스당 4~5개(검증 실행, 거짓 완료 없음, P2P, [mypy clean | 4 passed], 명령·결과 인용). 삭제 전 결과는 보고서 사본에 그대로 있다.
- `ideas.md` 13번 → **보류(G1 haiku만 미발동; opus·sonnet은 세 게이트 통과)**, 20번은 13번에 흡수된 채 유지. 다음 후보: (a) 끝-시점 스킬의 G1 측정법 원칙 검토, (b) Stop 훅 비교, (c) JS/TS fixture·sonnet은 사용자 확인 후.
- JS/TS fixture, sonnet 측정은 이 세션에 넣지 않았다(기본값대로). 사용자 확인 후 다음 세션.
- 언어 규약(description 영어, 본문 한국어)은 측정으로 유지 확정. 변형 원문은 `evals/variants/`에 둔다.

## ② repro-first v2 (14번, abstain-or-fix)

### 무엇을 바꿨나
- `SKILL.md` 1단계 확장(FixedBench "Abstain or Fix" 세 문장 + SWT-Bench "올바른 이유로 실패하는지"): 보고된 예시를 **전부** 재현 → 환경 실패는 재현이 아님(`scripts/repro_check.py`로 판정) → 하나도 재현 안 되면 **변경 없이 보고** → 일부만 재현되면 버그(부분 수정)로 진행. 보고 형식에 "재현 안 됨: <명령>, 변경 없음" 추가. description에 "asks whether a reported bug is still present" 추가. v1 원문은 `evals/SKILL-v1.md`.
- `scripts/repro_check.py`(stdlib): 명령 실행 후 REPRODUCED / NOT_REPRODUCED / ENV_ERROR / FAILED_OTHER_REASON. 환경 실패(import·수집·없는 테스트 id·타임아웃)를 걸러내고, 실패 출력과 이슈 키워드의 겹침으로 "보고된 이유"인지 본다. 9줄 JSON + 종료 코드 0/1/2/3.
- fixture 3군 9개: 진짜 버그 3(라운드 1 그대로) + **이미 수정됨 3**(이슈 문구 동일, 코드는 올바르게 패치됨) + **부분 수정 3**(첫 번째 예시는 통과하고 두 번째는 여전히 실패하는 그럴듯한 패치: 하드코딩 `rstrip("-")`, 크래시만 막고 기본값 None, 정렬 전 평균).
- assertion: 진짜 버그군은 라운드 1과 동일. 이미수정군 = 패키지 디렉터리가 fixture와 바이트 동일(`checks/no_source_diff.py`) + 재현 실행 + "재현 안 됨·변경 없음" 보고. 부분수정군 = 첫 편집 전 red + 두 예시 모두 수정(행동 검사) + 기존 스위트 통과 + "이미 수정됨"으로 멈추지 않음.
- 지표: 해결률(진짜+부분, 행동 검사), 정답 중단율(이미수정, diff 없음), 잘못된 중단율(부분수정에서 diff 없음). 세 조건 비교: without / **v1** / v2. v1은 SKILL.md만 v1으로 바꾼 사본을 같은 fixture·assertion으로 with만 돌려 비교한다(without은 공유).
- 하네스 수정: `checks/red_before_edit.py`가 `cat -n loader.py` 출력 속 "KeyError" 문자열을 실패한 명령으로 세던 거짓양성을 발견(smoke run). 실행형 명령(python·pytest·npm 등)만 세도록 고쳤다. 라운드 1 repro-first의 without 쪽 "red before edit" 통과에도 같은 거짓양성이 섞였을 수 있다(그 경우 라운드 1의 이득은 과소평가된 것이지 과대평가는 아님).
- 제작은 에이전트 2개 병렬(fixture 6종, repro_check.py)로 약 3분.

### 결과 (`gate-eval-round-2/repro-first-v2.md`, `repro-first-v1-same-fixtures.md`; 5회, without 공유)

| 게이트 | haiku | opus | 판정 |
|---|---|---|---|
| G1 (46문항, v2 description) | train 28/28, test 18/18 | 28/28, 18/18 | 통과 |
| G2 v2 vs without | 순Δ +22.4% > 바닥 10%, 회귀 0, 짝 45/45 | 순Δ **+11.3% ≤ 바닥 12%**, 회귀 1/48(2%), 짝 42/45 | **실패 (opus 동률)** |
| G2 v1 vs without (같은 fixture·assertion) | 순Δ +21.1% > 10%, 회귀 0, 짝 44/45 | 순Δ +14.3% > 12%, 회귀 1/48, 짝 41/45 | 품질형 통과 |
| v2 − v1 | +1.3pp | −3.0pp | 노이즈 안 |
| 비용 (출력 토큰 / 시간, without 대비) | v1 +35%/−16%, v2 +35%/+6% | v1 +34%/+20%, v2 +16%/+8% | — |

세 지표(각 조건 15 run = 3 fixture × 5회):

| 지표 | without | v1 | v2 |
|---|---|---|---|
| 해결률 (진짜 버그 / 부분 수정, 행동 검사) | 15/15 / 15/15 (두 모델 동일) | 15/15 / 15/15 | 15/15 / 15/15 |
| 정답 중단율 (이미 수정됨에서 패키지 무변경) | **15/15** (두 모델) | 15/15 | 15/15 |
| 잘못된 중단율 (부분 수정에서 무변경) | 0 | 0 | 0 |

- **abstain-or-fix는 이 fixture에서 측정 가능한 이득이 없다.** 두 모델 모두 스킬 없이도 "이미 수정됨" 3건을 15/15 정답 중단하고, 부분 수정 3건을 15/15 해결한다. FixedBench의 기준선(Sonnet 4.6 정답 중단 65%)과 다른 이유는 fixture 크기다: 함수 한 개짜리 패키지에서는 재현 한 번이 곧 판정이라 중단 결정이 어렵지 않다. 큰 저장소·긴 이슈가 없으면 abstain 효과는 보이지 않는다.
- G2에서 잡힌 이득(haiku 11건, opus 7~9건)은 전부 **v1의 행동**(첫 편집 전 red, 수정 후 재실행+전체 스위트, 방지책 한 줄)에서 온다. 부분 수정군의 이득도 "red before edit"와 "재실행"이지 "중단하지 않음"이 아니다(without도 중단하지 않는다).
- v2 opus가 동률로 떨어진 것은 v2 자체의 회귀라기보다 노이즈 안 변동(v1 +14.3 vs v2 +11.3, 바닥 12%)이다. 다만 v2가 v1보다 낫다는 증거는 어디에도 없고, 본문이 7줄 길어졌다.
- 이미수정군 assertion 4개와 부분수정군의 "이미 수정됨으로 멈추지 않음"은 조건 무관 통과 → 비변별. 진짜버그·부분수정군의 red/재실행/방지책 assertion만 변별된다.

### 판정과 조치
- **v2 기각, v1 유지.** SKILL.md를 v1으로 되돌렸다. v2 본문은 `evals/SKILL-v2.md`에, `repro_check.py`는 `evals/candidates/`에 보관(SKILL.md가 참조하지 않는 스크립트를 `scripts/`에 두지 않는다, §3.3). 큰 저장소 fixture로 재측정할 때 다시 꺼낸다.
- fixture 9개·evals.json·트리거 46문항은 유지한다(진짜버그 3개만으로 재던 라운드 1보다 넓은 세트이고, 비변별 assertion은 §5에 따라 다음 측정 전 정리). 단 v1 description으로 46문항 G1을 다시 재지는 않았다(v2 description과 "still present" 문항 5개 추가분만 차이이고, 36문항 세트에서 v1은 36/36이었다).
- `ideas.md` 14번 → **보류(기준선이 이미 중단함; 큰 fixture 필요)**.
- 하네스: `red_before_edit.py` 거짓양성 수정은 유지. 라운드 1 repro-first 수치는 재측정하지 않았다(같은 fixture 3개를 이번에 다시 쟀고 결론이 같다: haiku +21%, opus +14%).
