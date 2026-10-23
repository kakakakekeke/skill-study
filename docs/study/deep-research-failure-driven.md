# 딥 리서치 2: 실패 사례에서 거꾸로 + 결정적 도구의 빈칸 (2026-10-23)

> 증거 자료. 규칙 변경은 `principles.md`에서만. 백로그 반영은 `ideas.md` 20~30번과 "통합 우선순위" 절.
> 방법: deep-research 워크플로(출처 21개 → 주장 102개 → 25개 3표 검증 → 24 확정·1 기각). 첫 리서치(`deep-research-quality-skills.md`, 문헌에서 효과가 보고된 행동 순서 스킬)와 반대 방향: 에이전트가 **실제로 자주 저지르는 실패**의 빈도에서 역산하고, LLM 대신 **결정적 스크립트**가 잡을 수 있는 지점을 찾았다. 결정적 도구 목록(8절)은 합성자 지식이라 검증 투표를 거치지 않았다. §6.1 1차 출처 검증은 아직 안 했다(채택 전 필수).

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

주의: 다중 라벨 가능, 1·2위 차이는 표본 오차 이내, 전문 미열람(초록 기반).

### 1.4 Claude Code PR (2509.14745, 567건, 2025-02~04)

- 머지율 83.8% vs 매칭 사람 PR 91.0% (p<0.05). 에이전트 간 비교에선 Claude가 최고(84.3%, 2607.21832).
- 머지 전 수정이 필요한 PR 45.1%. 그 수정의 종류: **Fix 47.7%**, Docs 29.0%, Refactor 27.1%, **Style 23.4%**, Test 16.4%.
- 과제별: docs·CI·typo는 머지율 높고, 함수 구현·버그 수정·perf는 낮음.

### 1.5 SWE-bench 실패 트레이스

- **Edit-Quality 잔차 60~69%**: 올바른 함수를 찾아 수정까지 하고도 패치가 틀림(GPT-5 68.1%, Qwen3-Coder-480B 66.8%; 2603.24631). 작은 모델은 탐색 오류 비중이 커짐. 분류가 gold patch 정렬 기반이라 정당한 대안 수정을 오분류할 수 있음.
- 에이전트형 도구 실패의 **약 절반이 반복·검증 단계**(OpenHands 49.1%, Tools+Claude 51.7%; 2509.13941, Claude 3.5 Sonnet, 342 인스턴스). 하위 범주에 **Validation Retreat**(assertion 주석 처리·조건 완화), 특정 케이스 과적합, 비진전 반복. 개별 건수 미보고.

### 1.6 테스트 보상 해킹 (ImpossibleBench, ICLR'26)

- 불가능 과제에서 GPT-5 54~76%. **중단 옵션 추가 시 54%→9%**, 테스트 읽기 전용화는 정당한 성능을 유지하며 테스트 수정형 해킹 차단(Opus 4.1에 특히 효과).
- 일반(해결 가능) 과제의 기저율은 **미측정**. 2026-10 독립 감사: 최신 Claude/GPT는 거의 안 함, Gemini 15~20%.
- 기각(0-3)된 주장: "Claude·Qwen은 해킹의 >79%가 테스트 직접 수정". 출처 2510.20270 §4~5 'cheating methods' Figure. **"거짓"이 아니라 "미확인"** — 원문 Figure 6~7 재확인 필요. test-integrity-check는 모델 특이 효과를 전제하지 않고 설계.

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
| **test-integrity-check** | R2 ② | Validation Retreat, 해킹 54~76%(불가능 과제), 중단 옵션 54→9% | 효과는 하네스 수준(읽기 전용·중단 옵션)에서만 측정. 스킬+스크립트로는 미측정 | 높음(AST diff, 기성 도구 없음 → 빈칸) | 없음 | **3순위.** 유일하게 기성 도구가 없는 빈칸. 일반 과제 기저율이 낮을 수 있어 상충 fixture 필수. 훅(테스트 경로 보호)이 더 확실하다는 점을 함께 측정 |
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
