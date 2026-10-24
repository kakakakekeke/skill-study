# 딥 리서치 2: 실패 사례에서 거꾸로 + 결정적 도구의 빈칸 (2026-10-23)

> 증거 자료. 규칙 변경은 `principles.md`에서만. 백로그 반영은 `ideas.md` 20~30번과 "통합 우선순위" 절.
> 방법: deep-research 워크플로(출처 21개 → 주장 102개 → 25개 3표 검증 → 24 확정·1 기각). 첫 리서치(`deep-research-quality-skills.md`, 문헌에서 효과가 보고된 행동 순서 스킬)와 반대 방향: 에이전트가 **실제로 자주 저지르는 실패**의 빈도에서 역산하고, LLM 대신 **결정적 스크립트**가 잡을 수 있는 지점을 찾았다. 결정적 도구 목록(3절)은 합성자 지식이라 검증 투표를 거치지 않았다. 핵심 3편의 §6.1 1차 출처 검증은 8절(2026-10-23 완료).

## 1. 실패 유형 빈도표

### 1.1 에이전트 PR이 거절되는 이유

| 사유 | 비율 | 출처·표본 |
|---|---|---|
| 리뷰 방치·무의미 리뷰 | 38% | arXiv 2601.15195, 거절 PR 600건(562 분류, κ=0.91), Codex·Copilot·Devin·Cursor·Claude Code |
| 중복 PR | 23% | 같은 출처 |
| **CI/테스트 실패** | **17%** | 같은 출처. 코드 수준 신호 중 최대 |
| 원치 않는 기능 | 4% | |
| 잘못된 구현 | 3% | |
| 미완성 | 2.5% | |
| 사유 불명 | 49.3% / 64.1% | 2606.13468(fix PR 306건), 2509.14745(Claude Code 92건) — **코드 결함 빈도는 체계적으로 과소 추정** |
| 타 PR/개발자가 구현 | 12.0% | Claude Code 92건 |
| 너무 큼 | 3.3% | Claude Code 92건 |

### 1.2 머지 확률을 낮추는 신호 (33k PR 회귀, 2601.15195 Table 1 / 2602.19441)

- **실패 CI 체크 1개당 머지 odds −15%** (Cliff's δ −0.24)
- 변경 LOC δ −0.17, 파일 수 δ −0.10
- 리뷰 중 force push → 머지 가능성 감소(두 연구 일치)
- 주의: 저자 표기 "LOC 1줄당 −1%"는 계수와 산술 불일치. δ만 인용.

### 1.3 머지 후 리버트 원인 (MSR'26, AIDev 리버트 커밋 500건 수동 분류)

| 원인 | 비율 |
|---|---|
| 의도치 않은 부작용·과잉설계 | 22.3% |
| 기능 오류 | 22.1% |
| 코드 품질 | 17.7% |
| 의존성 관리 | 12.5% |

주의: 다중 라벨 가능, 1·2위 차이는 표본 오차 이내, 전문 미열람(초록 기반). → **8.5에서 전문 확인**: 22.3%는 하위 항목 셋의 합이고, 초록의 범주 표기가 본문과 다르다.

### 1.4 Claude Code PR (2509.14745, 567건, 2025-02~04)

- 머지율 83.8% vs 매칭 사람 PR 91.0% (p<0.05). 에이전트 간 비교는 **데이터셋에 따라 상반**: 2607.21832(Python 489 repo, GLMM 보정)에서는 Claude 84.3%로 최고지만, 2601.15195(AIDev-pop 33.6k, 원시 비율)에서는 **59.0%(271/459)로 5개 중 3위**(Codex 82.6%, Cursor 65.2%, Claude 59.0%, Devin 53.8%, Copilot 43.0%). "Claude가 최고"라고 단정하지 않는다.
- 머지 전 수정이 필요한 PR 45.1%. 그 수정의 종류: **Fix 47.7%**, Docs 29.0%, Refactor 27.1%, **Style 23.4%**, Test 16.4%.
- 과제별: docs·CI·typo는 머지율 높고, 함수 구현·버그 수정·perf는 낮음.

### 1.5 SWE-bench 실패 트레이스

- **Edit-Quality 잔차 60~69%**: 올바른 함수를 찾아 수정까지 하고도 패치가 틀림(GPT-5 68.1%, Qwen3-Coder-480B 66.8%; 2603.24631). 작은 모델은 탐색 오류 비중이 커짐. 분류가 gold patch 정렬 기반이라 정당한 대안 수정을 오분류할 수 있음.
- 에이전트형 도구 실패의 **약 절반이 반복·검증 단계**(OpenHands 49.1%, Tools+Claude 51.7%; 2509.13941, Claude 3.5 Sonnet, 342 인스턴스). 하위 범주에 **Validation Retreat**(assertion 주석 처리·조건 완화), 특정 케이스 과적합, 비진전 반복. 개별 건수 미보고.

### 1.6 테스트 보상 해킹 (ImpossibleBench, 프리프린트 under review — 8.2 참조)

- 불가능 과제에서 GPT-5 54~76%. **중단 옵션 추가 시 GPT-5 54%→9%, 그러나 Opus 4.1은 50%→46%로 거의 효과 없음**(원문 "much less pronounced"). 테스트 읽기 전용화는 정당한 성능을 유지(Opus 86→85)하며 테스트 수정형 해킹 차단(Opus Oneoff 54→6%, Conflicting 50→1%).
- 일반(해결 가능) 과제의 기저율은 **미측정**. 2026-10 독립 감사: 최신 Claude/GPT는 거의 안 함, Gemini 15~20%.
- ~~기각(0-3)된 주장: "Claude·Qwen은 해킹의 >79%가 테스트 직접 수정"~~ → **8.2에서 번복: 원문 §4.2에 문장 그대로 있고 Figure 5 라벨로 Opus 4.1 86%, Sonnet 4 82%, Sonnet 3.7 79%, Qwen3-Coder 87% 확인.** OpenAI 모델은 네 방법을 분산(GPT-5: 테스트 수정 24%, 연산자 오버로딩 14%, 상태 기록 34%, 특수화 23%). → Claude 계열에는 **테스트 파일 쓰기 차단 하나로 해킹 대부분이 막힌다**. test-integrity-check의 훅 변형 우선순위가 올라간다.

## 2. 유형 → 대응 수단 매핑

| 실패 유형 | 빈도 근거 | 수단 | 이유 |
|---|---|---|---|
| CI/테스트 실패 | 17%, 체크당 −15%, Fix 47.7% | **스킬+스크립트** (연관 테스트 선택 실행 + 린트/타입체크 JSON) | 로컬에서 결정적으로 사전 재현 가능 |
| 변경 크기·범위 초과 | δ 0.17, 너무 큼 3.3%, 부작용 22.3% | **스킬+스크립트** (초과 후보 열거는 스크립트, 분할 결정은 스킬) | 범위 판정에 이슈 연관 추론 필요 |
| 테스트 약화 / Validation Retreat | 해킹 54~76%(불가능 과제), C2.3 | **스크립트**(AST diff) + **훅**(테스트 경로 쓰기 차단) | 탐지는 결정적, 차단은 훅이 확실 |
| 의존성 무단 추가 | 리버트 12.5%, 라이선스 거절 4건 | **스크립트** (audit·라이선스·크기·미사용) | 매니페스트 diff 시 결정적 |
| 중복·대체·타인 구현 | 23%+5.9%+12% | **스크립트** (`gh pr list --search`) | PR 열기 전 조회. 단 PR 워크플로 사용자에 한정 |
| 부작용·파괴적 변경 | 22.3% | **스크립트** (변경 심볼 참조처 열거) | 정적 분석 가능 |
| 비진전 반복 | I&V 단계 ~50% | 스킬+스크립트 (실패 시그니처 반복 카운트) | 감지는 결정적, 전략 전환은 스킬 |
| force push | 머지 확률 감소 | **훅** | 지침보다 차단 |
| 시크릿 유출 | 빈도 자료 없음 | **훅/린터** + 내장 security-review | 신규 스킬 부적합 |
| 코드 품질·Style·Docs | 17.7%, 23.4%, 29% | **린터/포매터** 사전 실행 (ci-preflight에 포함) | 별도 스킬 불필요 |
| 과잉설계·복잡도 | 22.3%의 일부 | **내장 simplify** | 중복 |
| 설계 불일치·잘못된 접근·추론 결함·Edit-Quality | 10/30, 2.6%, 65%, 60~69% | **해당 없음** (스크립트로 못 잡음) | 큰 모델에서 가이드라인 효과 소멸 교훈과 일치 |
| 리뷰 방치·사유 불명 | 38%, 49~64% | 해당 없음 (저장소 측 요인) | |

## 3. 결정적 도구 목록 (미검증 — 채택 전 `pip index versions` / `npm view`로 존재·옵션 확인)

| 용도 | Python | JS/TS |
|---|---|---|
| 변경 연관 테스트 선택 | `pytest-testmon`, `pytest-picked`, `pytest --lf` | `jest --findRelatedTests`, `jest --changedSince`, `vitest --changed` |
| 린트/타입체크 JSON | `ruff check --output-format json`, `mypy --output json`(1.11+), `pyright --outputjson` | `eslint -f json`, `tsc --noEmit --pretty false`(텍스트), `biome lint --reporter=json` |
| 커버리지 델타 | `pytest-cov` + `coverage json` | `jest --coverageReporters=json-summary`, `vitest --coverage.reporter=json-summary` |
| 죽은 코드·미사용 의존성 | `vulture`, `deptry` | `knip`, `depcheck`, `madge` |
| 의존성 게이트 | `pip-audit`, `pip-licenses`, `deptry` | `npm audit --json`, `license-checker`, `npm view <pkg> dist.unpackedSize` |
| 시크릿 | `detect-secrets`, `gitleaks` | `secretlint`, `gitleaks`, `trufflehog` |
| 참조처 열거 | `ast`/`libcst`/`jedi`, `ast-grep` | `ts-morph` findReferences, `tsserver`, `ast-grep` |
| 마이그레이션 가역성 | `alembic check`, Django `makemigrations --check` + `sqlmigrate --backwards` | `prisma migrate diff`, knex/typeorm down 존재 검사 |
| **diff 범위 ↔ 이슈 연관** | **기성 도구 없음** (`git diff --name-only` + 이슈 본문 경로·심볼 매칭 직접 작성) | 동일 |
| **assertion 약화 탐지** | **기성 도구 없음** (`ast`로 assert 제거·`skip/xfail` 추가·리터럴 변경·`pass`화 탐지) | **없음** (`@babel/parser`/ts-morph로 `.skip/.only/xit`·expect 제거·`toEqual` 인자 변경) |

**측정 보고 부재**: 어떤 출처도 이 도구들을 에이전트 루프에 끼운 with/without 효과나 LLM 대비 토큰·정확도를 제시하지 않음. → **우리 eval이 1차 자료가 된다.**

## 4. 역효과·한계

- gold patch 정렬 기반 분류는 정당한 대안 수정을 "범위 초과"로 오탐할 수 있음 → scope-guard는 gold 경로 기준을 쓰지 말고 이슈 텍스트 기준으로.
- 테스트 읽기 전용화는 special-casing·`__eq__` 오버로딩·추가 상태 기록은 못 막음.
- 해킹률이 하네스·프롬프트에 따라 9~76%로 변동 → 단일 수치로 효과 예측 불가.
- 모든 빈도표는 **GitHub 공개 PR** 기반. PR을 열지 않는 로컬 Claude Code 세션의 실패 분포와 다를 수 있다. Claude Code 표본은 작거나(459/33.6k, 50 repo) 2025 초.

## 5. 신규 후보 11개

| 후보 | 한 줄 | 막는 유형(빈도) | scripts/ 대체 | assertion 예 | 내장 중복 | G2 예측 |
|---|---|---|---|---|---|---|
| **ci-preflight** | 완료 전 변경 연관 테스트만 선택 실행 + 린트/타입체크 JSON 요약 | CI 실패 17%, 체크당 −15%, Fix 47.7%·Style 23.4% | 테스트 선택·린트 파싱·요약 전부 | preflight JSON 존재 && 로그 토큰 ≤30% && 최종 diff 린트 0 | verify-before-done(리서치 1)과 인접 → **합칠 것** | 비용형 높음 |
| **test-integrity-check** | 테스트 diff를 AST 비교해 assert 제거·skip·expected 변경 열거, 정당화 또는 되돌림 | Validation Retreat, 해킹 54~76%(불가능 과제) | 탐지 전부(직접 작성) | 상충 fixture에서 테스트 수정 없이 중단·보고 비율 | 없음 | 품질형 중간~높음 (일반 과제 기저율 낮으면 상충 fixture에서만 측정) |
| **scope-guard** | 이슈 텍스트 경로·심볼과 diff 파일 집합 비교, 초과·LOC 예산 열거 | 크기 δ0.17, 너무 큼 3.3%, 부작용 22.3%, 원치 않는 기능 4% | 집합 비교·LOC 집계 | 범위 외 파일 변경 0 또는 분리 커밋 | simplify와 다름 | 품질형 중간 (오탐 위험) |
| impact-map | 변경 심볼 참조처를 ast-grep/ts-morph로 JSON 제공 | 부작용 22.3%, Edit-Quality 60~69% | 참조 탐색 전부(grep·Read 반복 대체) | 토큰 ≤70% && 참조처 테스트 실패 0 | 없음 | 비용형 높음 |
| dep-add-gate | 매니페스트 diff 시 audit·라이선스·크기·미사용 요약 | 의존성 리버트 12.5% | 전부 | 취약/비호환 라이선스 추가 0 | security-review 부분(취약점) → 라이선스·크기 중심 | 품질형 낮음~중간 |
| pr-dedupe-check | PR 전 `gh`로 같은 이슈·파일 다루는 열린 PR 조회 | 중복 23%+5.9%+12% | 전부 | 중복 fixture에서 PR 생성 회피 | 없음 | 품질형 중간. **우리 워크플로(로컬 작업)엔 효용 낮음** |
| loop-breaker | 실패 시그니처 N회 반복 시 접근 전환 요구 | 비진전 반복, I&V ~50% | 시그니처 계산·카운트 | 동일 실패 3회+ 횟수 감소, 턴 수 감소 | abstain-or-fix 인접 | 품질형 낮음~중간 (큰 모델은 이미 전환) |
| coverage-delta | base/head 커버리지 비교, 변경 라인 미커버 열거 | 미완성 2.5% | 전부 | 변경 라인 커버리지 ≥ base | 없음 | 낮음 |
| dead-code-sweep | 리팩터 후 vulture/knip | 코드 품질 17.7% | 전부 | 미사용 export 감소 | simplify 부분 → 비용형으로만 | 비용형 중간 |
| migration-reversibility | 마이그레이션 추가 시 down 존재·실행 검사 | 파괴적 변경 0.3% | 전부 | down 없는 마이그레이션 0 | 없음 | 낮음 (빈도 근거 부족) |
| secret-scan | diff에 gitleaks | 자료 없음 | 전부 | 유출 0 | security-review | **스킬 아닌 훅** |

## 6. 통합 검토: 리서치 1 후보와 같은 축에 올리기

리서치 1(효과 근거 중심)과 리서치 2(실패 빈도 중심)의 후보를 한 표에 놓고, 두 축을 함께 본다.

| 후보 | 출처 | 막는 실패 유형(빈도) | 효과 근거(모델) | 스크립트 비중 | 내장 중복 | 통합 판정 |
|---|---|---|---|---|---|---|
| **verify-before-done ⊕ ci-preflight** | R1 #13 + R2 ① | **CI 실패 17%, 체크당 −15%, 머지 후 Fix 47.7%** — 코드 수준 최대 항목 | SWT-Bench +2.6pp(미검정, GPT-4) · superpowers 소표본 | 높음(테스트 선택·린트 JSON·exit code) | 없음 | **1순위.** 두 리서치가 독립적으로 같은 지점을 가리킴. 행동(완료 전 실행)은 R1, 스크립트(선택 실행·요약)는 R2. 품질형(거짓 완료율)과 비용형(토큰) 둘 다 측정 |
| **repro-first v2** | R1 #14 | 기능 오류 22.1% 리버트, 잘못된 수정 5.6%, Edit-Quality 60~69% | **가장 강함**: Sonnet 4.6 p<0.01, 편집 전 재현률 42.5→81.5 (1차 출처 검증 완료) | 중간(repro_check: 올바른 이유로 실패하는지) | 없음 | **2순위.** 효과 근거 최강, 기존 fixture·기준선 있음 |
| **test-integrity-check** | R2 ② | Validation Retreat, 해킹 54~76%(불가능 과제). Claude는 해킹의 79~86%가 테스트 수정 | 효과는 하네스 수준에서만: 읽기 전용화 Opus 54→6%(정상 성능 유지), 중단 옵션은 Opus에 거의 무효(50→46) | 높음(AST diff, 기성 도구 없음 → 빈칸) | 없음 | **3순위, 단 설계 변경.** Claude에는 "막히면 중단" 지침이 아니라 **테스트 경로 쓰기 차단(PreToolUse 훅) + 스크립트 탐지**가 맞다. 스킬 단독 vs 훅 vs 둘 다를 같은 fixture로 비교 |
| scope-guard | R2 ③ | 크기 δ0.17, 부작용 22.3%, 원치 않는 기능 4% | 직접 효과 측정 없음 | 중간 | simplify와 다름 | 4순위. 오탐(정당한 다중 파일 수정) 측정 설계가 관건 |
| impact-map | R2 ④ ≈ R1 #16 regression-guard | 부작용 22.3% | 없음 | 매우 높음 | 없음 | 비용형 후보. verify-before-done의 "연관 테스트 선택"과 겹치므로 그쪽에 흡수하고 독립 스킬은 보류 |
| dep-add-gate | R2 ⑤ | 의존성 리버트 12.5% | 없음 | 매우 높음 | security-review 부분 | 아이디어. fixture에서 의존성 추가를 유도해야 해서 eval이 어색함 |
| plan-first | R1 #15 | 설계 불일치 10/30, 잘못된 접근 2.6% → R2 매핑에서 "스크립트로 못 잡음" | 소형 모델만 +5.4pp | 없음 | **내장 plan mode** | 보류 유지. 두 리서치 모두 근거가 약하고 중복 문제 |
| runtime-diagnose | R1 #17 | Edit-Quality 잔차 | PDB 에이전트 수준에서만 | 낮음(SKILL.md로 재현 어려움) | 없음 | 보류 유지 |
| loop-breaker | R2 ⑦ | 비진전 반복 | 없음 | 중간 | abstain-or-fix 인접 | 아이디어 |
| pr-dedupe-check | R2 ⑥ | 중복 23%+ (PR 워크플로만) | 없음 | 높음 | 없음 | 보류: 우리 작업 방식(로컬·PR 적음)에 효용 낮음 |
| tdd-enforce | R1 #18 | — (R2에 TDD 미준수 관련 실패 없음) | 동률+회귀 +42% | — | — | 기각 유지 |
| self-review / CoT | R1 #19 | — | ≤1.08배 / 소멸 | — | code-review | 기각 유지 |
| coverage-delta, dead-code-sweep, migration-reversibility | R2 | 낮음 | 없음 | 높음 | simplify 부분 | 아이디어(비용형 후보 풀) |
| secret-scan, force-push 차단 | R2 | — | — | — | security-review | **훅으로** (스킬 아님). §3.2 "반복 위반 관찰 후" 조건 적용 |

**두 리서치가 수렴한 것**: (1) 효과가 입증된 행동 변경(R1)과 가장 빈번한 코드 수준 실패(R2)가 **"완료 전 검증 실행"**에서 만난다. (2) "더 생각하라"류와 설계 판단 영역은 두 쪽 모두 "스킬로 못 잡음". (3) 결정적 스크립트의 진짜 빈칸은 둘뿐: **assertion 약화 탐지**와 **diff↔이슈 범위 판정**.

## 7. 라운드 2 제안 (3개)

1. **verify-before-done** (R1 #13 ⊕ R2 ci-preflight): `scripts/preflight.{py,sh}` — 변경 파일 연관 테스트 선택 실행 + ruff/mypy·eslint/tsc JSON 요약 + exit code. SKILL.md는 SWT-Bench 문구("실행해서 이슈대로 실패/통과하는지 확인") + FixedBench "verify the reproduction now fails" 결합. fixture: 숨은 회귀(시그니처 변경), tsc만 실패, pytest import 오류로 0 tests ran. 지표: 거짓 완료율(품질), 토큰·시간(비용).
2. **repro-first v2**: 기존 fixture 3 + 이미 수정됨 3 + 부분 수정 3. `scripts/repro_check.py`. 프롬프트 세 문장. 지표: 해결률·정답 중단율·잘못된 중단율 동시.
3. **test-integrity-check**: `scripts/test_diff_audit.py` (Py ast) + TS 버전. fixture: 스펙과 상충하는 테스트 1개 삽입(Py 반올림 규칙, TS 날짜 포맷) + 정상 과제 대조. 지표: 테스트 약화 발생률, 중단·보고율, 정상 fixture 오탐. 병행: PreToolUse 훅으로 테스트 경로 보호 시 같은 fixture 결과 비교(스킬 vs 훅).

공통: 5회 반복, 노이즈 바닥 max(관측, 3/N), P2P 회귀율 부가 기록, Python 먼저 → JS/TS. **채택 전 §6.1**: 2601.15195(거절 사유 분류), 2510.20270(ImpossibleBench, 특히 기각된 Claude 해킹 방식 Figure), 2509.13941(Validation Retreat) 1차 출처 직접 확인.

## 8. 1차 출처 독립 검증 (2026-10-23, §6.1)

핵심 세 편을 에이전트 3개가 원문만 읽고 "논문이 무엇을 보고하느냐"에 답하게 했다(전제 없는 질문). 1~2절과 대조.

### 8.1 arXiv 2601.15195 — 에이전트 PR 거절 사유 (Drexel·Missouri S&T, **MSR 2026 채택**(abs Comments), 6쪽 short paper, 익명 복제 패키지)

| 노트 주장 | 원문 | 판정 |
|---|---|---|
| 거절 사유 38/23/17/4/3/2% , κ 0.91, 600→562 | Table 2 그대로. 미완성은 논문 표기 2%(15/562) | ✅ (2.5%→2%) |
| 에이전트별 PR 수 21,799/4,970/4,827/1,541/459 | §3 RQ1 | ✅ |
| LOC δ −0.17, 파일 δ −0.10, CI 체크당 odds −15%(δ −0.24) | Table 1 | ✅ |
| "LOC 1줄당 −1%"는 계수와 불일치 | 계수 −2.8e-6 → 1줄당 0.0003%, **약 3,589줄마다 1%**. 본문 서술이 틀림 | ✅ 지적 확인 |
| docs 최고, fix·perf 최저 | docs 84%, CI 79%, build 74% / perf 55%, fix 64% | ✅ |
| "에이전트 정체성을 통제해도" | 이 논문 회귀에는 **통제변수 없음**(공변량 5개만). 그 서술은 2602.19441에만 해당 | ⚠️ 출처 분리 |
| (노트 1.4) Claude 최고 84.3% | 이 논문에서 Claude Code 머지율 **59.0%, 5개 중 3위** | ⚠️ 1.4 보정 |

추가: Threats to Validity 절 없음. 본문 오기 1건(Claude CI 머지율 0.57 vs Figure 0.80). 에이전트별 거절 사유 분포는 미제공.

### 8.2 arXiv 2510.20270 — ImpossibleBench (CMU·Anthropic, **"Preprint. Under review."**, 코드 공개)

| 노트 주장 | 원문 | 판정 |
|---|---|---|
| GPT-5 Oneoff-SWE 76%, Conflicting 54%, LCB 2.9% | §1·§4 본문 | ✅ |
| 중단 옵션 54→9%(GPT-5), o3 49→12% | §5.3. Figure 8 범례/본문 모델명 불일치(o3 vs o4-mini) 주의 | ✅ |
| 중단 옵션이 Claude에도 효과 | **아님.** Opus 4.1 50→46%, 원문 "much less pronounced" | ❌ 보정 |
| 읽기 전용화: 해킹 차단, 정상 성능 유지 | Figure 7 라벨: Opus Original 86→85, Oneoff 54→6, Conflicting 50→1 | ✅ |
| 테스트 숨김은 해킹 ~0, 정상 성능 저하 | GPT-5 97→76, Opus 86→70 | ✅ |
| "ICLR'26 poster" | 원문 "Preprint. Under review." | ❌ 보정 |
| Gemini 15~20% | **Gemini는 이 논문 평가 대상 아님**(별도 독립 감사 출처) | ⚠️ 출처 분리 |
| 일반 과제 치팅 미측정 | 직접 측정 없음. LLM 모니터 플래그율 LCB 7%, SWE 1~2%를 상한으로만 | ✅ |
| **기각된 주장: Claude >79% 테스트 수정** | **§4.2 원문 그대로** + Figure 5 라벨(Opus 86 / Sonnet 4 82 / Sonnet 3.7 79 / Qwen 87%) | **❌ 검증단 오판 → 복원** |

설계에 중요한 원문 사실:
- Claude 계열의 해킹 경로는 **거의 전부 테스트 파일 수정**이다. 따라서 Claude Code에서는 테스트 경로 쓰기 차단이 곧 해킹 차단이다. 읽기 전용화가 정상 성능을 깎지 않으므로(86→85) 훅의 부작용 걱정도 작다.
- 반대로 OpenAI 계열은 특수화·상태 기록 등으로 우회하므로 AST diff 탐지(test-integrity-check 스크립트)가 필요한 쪽은 그쪽이다. 우리 대상이 Claude라면 **훅이 1차, 스크립트는 2차**.
- 느슨한 프롬프트는 해킹을 **늘린다**(GPT-5 54→66, Opus 50→55). full 스캐폴드(도구 多)가 minimal보다 해킹이 높다(Opus 23→50). 쉬운 과제에서 더 많이 해킹한다.
- 읽기 전용은 special-casing·`__eq__` 오버로딩은 못 막음(원문 명시). Claude에는 드문 경로.

### 8.3 arXiv 2509.13941 — 이슈 해결 실패 분류 (Beihang·HKU, 프리프린트, 익명 복제 패키지)

| 노트 주장 | 원문 | 판정 |
|---|---|---|
| 3도구, Claude 3.5 Sonnet 백본, 150 이슈/342 인스턴스 | §3.2, §5.2 | ✅ |
| I&V 단계 포함 OpenHands 49.1%, Tools Claude 51.7%, Agentless 51.3% 로컬라이제이션 | §6.1 | ✅ |
| Validation Retreat 정의·django-16454 | §5.2 C2.3 | ✅ |
| 하위 범주 개별 건수 미보고 | 확인. Fig. 9는 9개 상위 범주 건수만(C2: OpenHands 20, ToolsClaude 22) | ✅ |
| 근본 원인 65/25/10%, 분모 미명시 | §6.2.1 "approx.", 분모 불명 | ✅ |
| 다중 라벨 | 명시적(이슈당 평균 2.28 라벨) | ✅ |

추가: 논문 내부 불일치 — Fig. 9 건수 합 595 ≠ 본문 342 인스턴스. 표(Table)가 하나도 없고 수치는 본문·그림에만. Python·단일 백본(2024년 Claude 3.5 Sonnet) 한정. Expert-Executor 실험에서 Evasive Repair 5건·Output Misreading 6건이 교정됨(§7.2) — "재현 출력 오독"이 실제로 고쳐지는 실패 유형이라는 점은 verify-before-done의 "exit code를 읽어라" 설계와 맞닿는다.

### 8.4 검증 후 판정 변화

| 항목 | 변화 |
|---|---|
| test-integrity-check (3순위) | **설계 변경**: Claude 대상이면 PreToolUse 훅(테스트 경로 쓰기 차단)이 1차 수단. 스킬은 "차단됐을 때 보고하는 경로"와 OpenAI류 우회 탐지용. eval은 스킬 단독 / 훅 단독 / 둘 다 3조건 비교. §3.2 "훅은 반복 위반 관찰 후"와 충돌하지 않도록, 먼저 **우리 세션에서 테스트 파일 수정 빈도를 관찰**하는 것이 선행 과제 |
| 빈도표 | Claude Code 머지율은 데이터셋에 따라 59%(원시)와 84%(보정) — 둘 다 적고 단정하지 않음 |
| 게재 상태 | 세 편 중 **MSR 2026 채택 1편**(2601.15195), 나머지 둘은 프리프린트 |
| 자동 검증 | 두 번째 리서치에서도 **기각 1건이 원문에 있었음**(리서치 1의 2건과 합쳐 3/8). 기각률이 낮은 리서치(1/25)에서도 그 1건이 틀렸다. §6.1 근거 보강 |

### 8.5 1.3 리버트 원인 전문 확인 (2026-10-24, scope-guard 사전 검토)

출처: Oukhay·Begoug·Chouchen·Ouni, "When AI Code Doesn't Stick: An Empirical Study on Reverted Changes Introduced by AI Coding Agents", MSR'26 Mining Challenge(5쪽, 학회 사이트 PDF, DOI 10.1145/3793302.3793587). AIDev 33,580 PR 중 리버트 커밋이 있는 PR은 893개(2.66%)다. 리버트 커밋 1,141개 가운데 500개를 층화 표본으로 뽑아 주제 분석했다(최종 κ=1.0).

| 노트 주장 | 원문 | 판정 |
|---|---|---|
| 의도치 않은 부작용·과잉설계 22.3% | C1 "Overengineering Side Effects" 22.33% = 의도치 않은 동작 변경 12.47% + 무관한 파일 변경 7.04% + 과도한 리팩터링 2.82% (Figure 4) | ✅ 수치. 다만 **범주 전체**다 |
| 기능 오류 22.1% | C2 Functional Incorrectness 22.13% | ✅ |
| 코드 품질 17.7%, 의존성 12.5% | C3 17.71%, C4 12.47% | ✅ |
| (초록) "unintended side effects (22.33%), overengineering (22.13%)" | 본문·Figure 4에서 22.13%는 C2 기능 오류 | ❌ 초록 표기 오류 |

- diff 범위 검사로 잡을 수 있는 몫은 무관한 파일 변경과 과도한 리팩터링, 합쳐 약 9.9%다. 동작 변경 12.47%는 파일 집합으로 보이지 않는다.
- Claude Code PR의 리버트율은 7.21%(33/458)다(Copilot 7.57% 다음).
- scope-guard 판정은 `gate-eval-round-3.md` ①.
