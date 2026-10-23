# 아이디어 백로그

채택 여부는 `principles.md` §2 세 게이트와 §6.3 체크리스트로 결정한다. 상태: 아이디어 / 선정 / 제작중 / 게이트 통과 / 보류(사유).

## 2026-10-22 자율 제작 라운드 후보 (효용 예상 순)

| # | 이름 | 종류 | 한 줄 설명 | 기여 목적 | 내장 중복 | 상태 |
|---|---|---|---|---|---|---|
| 1 | `gate-eval` | skill (user-invoked 라우터+scripts) | 이 저장소 스킬을 세 게이트 프로토콜(§5)로 측정: 노이즈 바닥, 모델 2종×3회, 이득·회귀 쌍, 토큰, 버전 기록 → 고정 형식 report.md | 3 (일정한 산출물), 전체 게이트의 도구 | skill-creator는 단일 모델·반복 없음·노이즈 바닥 없음, `claude plugin eval`은 형식 비호환 → 빈칸 | **게이트 통과 (비용형)** (10-23 5회: 두 모델 Δ가 노이즈 바닥 안, 출력 토큰 −89%/−81%·시간 −75%/−59%. haiku는 스킬 없으면 노이즈 바닥을 거의 안 넣음(1/5 vs 4/5); `study/gate-eval-round-1.md`) |
| 2 | `test-digest` | skill + script | 테스트·빌드·CI 로그의 긴 출력을 결정적 스크립트로 실패 요약 수십 줄로 압축 | 2 (토큰), 1 | 없음 | **보류** (10-23 5회 재측정: 노이즈 바닥 3%, haiku +5.3% 품질형이나 opus +2.7%는 동률·비용 절감 없음 → G2 실패. 변별 assertion은 "Bash 출력 80줄 이하" 1개뿐. 작은 모델 전용 등 다른 쓸모가 보이면 재검토. G1은 36/36) |
| 3 | `repro-first` | skill | 버그 수정 전 red가 되는 재현 명령을 먼저 만들고, 수정 후 green 확인, 끝에 "재발을 막을 검사 위치" 한 줄 | 4.6 (루프 우선), 1 | diagnosing-bugs(외부)는 과잉 트리거·무거움. 내장 없음 | **게이트 통과** (G2 +26%/+20%, 회귀 0) |
| 4 | `flaky-check` | skill + script | 명령을 N회 반복 실행해 실패율·실패 시그니처·시간을 수십 줄로 보고 (노이즈 바닥 측정기) | 1, 2 | 없음 | **게이트 통과 (비용형)** (2차: 회귀 0, 품질 동률, 시간 −76%/−60%·출력 토큰 −51%/−23%. 10-23 G2 비용형 신설로 판정. description v3는 새 held-out 13문항에서 13/13·13/13, 경계 문항 0) |
| 5 | 관찰 로그 Stop 훅 | plugin (hook) | 세션 종료 시 반복 오류를 관찰 로그에 기록, 2~3회 시 승격 후보 제안 | 4 | 없음 | 보류: §4.5 "해로움 판정자" 미정, 훅은 반복 위반 관찰 후(§3.2) |
| 6 | `ci-triage` | skill | 실패한 GitHub Actions 런의 로그를 가져와 원인 요약 | 1, 2 | `test-digest`가 `gh run view --log-failed` 입력도 처리하면 중복 | 보류: 2에 흡수 가능 여부 확인 후 |
| 7 | `hook-authoring` | skill | 훅 작성 + 거짓양성률 측정 절차 | 3 | `update-config`, `plugin-authoring`과 겹침 | 보류 |
| 8 | 세션 간 오류 패턴 축적 | plugin | 커밋 메시지의 "맞은 가설"을 모아 반복 패턴 추출 | 4 | 없음 | 아이디어: 5와 함께 설계 |
| 9 | `pr-summary` | skill | PR 설명 자동 작성 | 3 | 기본 모델이 이미 잘함 → G2 의심 | 보류 |
| 10 | 가이드라인 스킬("항상 X") | skill | 코딩 규약 강제 | 1 | §3.5 가설: G1 저조 예상 | 기각 |
| 11 | 문서 포인터 stale 검사 | skill | 코드 변경 후 README·CLAUDE.md의 깨진 포인터 탐지 | 1 | `/doctor prompt-audit`과 겹침 | 보류 |
| 12 | 버전 특정 API 지식 주입 | skill | 특정 프레임워크 최신 API 참조 | 1 | 스택 미정 (사용자 KIS/Kiwoom 스킬 별도 존재) | 아이디어 |

## 2026-10-23 딥 리서치 후보 — 품질형 (근거: `study/deep-research-quality-skills.md`)

| # | 이름 | 종류 | 한 줄 설명 | 기여 목적 | 내장 중복 | 상태 |
|---|---|---|---|---|---|---|
| 13 | `verify-before-done` | skill + scripts/verify.sh | 완료 선언 전 테스트·타입체크·린트를 새로 실행하고 exit code를 최종 메시지에 인용. 거짓 완료율이 지표 | 1 | 없음 | **보류 (G1 haiku만 미발동)** (10-23 5회: G2 품질형 통과 haiku +12.6%/opus +13.3%/sonnet +23.0%·회귀 0, G3 통과. G1은 description v3로 opus·sonnet held-out 14/14 통과, haiku 11/14 — 검증을 언급 안 한 평범한 변경 요청에 라우터가 NONE. 실제 수행 중 호출은 haiku 11/15·opus 15/15로 G1 프록시와 갈림. 20번 ci-preflight 흡수(`scripts/preflight.py`). `study/gate-eval-round-2.md`) |
| 14 | `repro-first` v2 (abstain-or-fix) | 기존 스킬 확장 + scripts/repro_check.py | 재현이 올바른 이유로 실패하는지 확인, 재현 불가면 변경 없이 보고. fixture에 진짜 버그/이미 수정/부분 수정 3군 | 1, 4.6 | 없음 | **보류 (기준선이 이미 중단함)** (10-23 5회, fixture 3군 9개: without/v1/v2 모두 정답 중단 15/15·잘못된 중단 0·해결 15/15. v2−v1 Δ는 노이즈 안(+1.3/−3.0pp), v2 opus는 without 대비 동률로 G2 실패. v1 유지, v2 본문·repro_check.py는 evals/에 보관. 모듈 7개짜리 ledger 세트(옛 API·무관한 실패·틀린 신고·특수 처리·증상 변화·깊은 버그 6개)에서도 세 조건 모두 결과 assertion 60/60으로 동일 → 현 모델엔 빈칸 없음. `study/gate-eval-round-2.md`) |
| 15 | `plan-first` | skill | 첫 Edit 전 ≤8단계 계획 | 1 | **Claude Code plan mode와 중복 가능성 — §3.1 확인 전엔 착수 금지** | 보류: 소형 모델만 검증(+5.4pp), opus 소멸 위험 |
| 16 | `regression-guard` | skill + scripts | 수정 후 변경 모듈을 임포트하는 기존 테스트만 골라 실행, P2P 회귀 0 확인 | 1, 2 | 없음 | 보류: 23번 impact-map과 같은 것. 13번 verify-before-done의 연관 테스트 선택으로 흡수 |
| 17 | `runtime-diagnose` | skill | 재현 후 수정 전 디버거·로그로 런타임 관찰 | 1 | 없음 | 보류 (원문의 Stage 2는 PDB 디버거 에이전트 — SKILL.md로 재현 어려움. FF 케이스에만 효과. 라운드 3 이후) |
| 18 | `tdd-enforce` | skill | 실패 테스트 없이 프로덕션 코드 금지 | 1 | 없음 | **기각 후보** (TDAD 동률 + 회귀 +42%, superpowers 저준수. 새 기능 과제 한정 재검토 여지) |
| 19 | `self-review`, CoT 가이드라인 | — | — | — | code-review 중복 / §3.5 | **기각** (self-repair ≤1.08배, CoT는 추론 모델에서 ±3pp·지연 증가) |

## 2026-10-23 딥 리서치 2 후보 — 실패 빈도·결정적 도구 (근거: `study/deep-research-failure-driven.md`)

| # | 이름 | 종류 | 한 줄 설명 | 막는 실패(빈도) | 내장 중복 | 상태 |
|---|---|---|---|---|---|---|
| 20 | `ci-preflight` | scripts | 변경 연관 테스트 선택 실행 + 린트/타입체크 JSON 요약 | CI 실패 17%, 체크당 −15% | 없음 | **13번 verify-before-done에 흡수** (행동은 13, 스크립트는 20) |
| 21 | `test-integrity-check` | skill + scripts/test_diff_audit (+ 옵트인 hook) | 테스트는 스펙: 코드로 못 통과시키면 테스트를 고치지 않고 충돌 보고. AST diff 감사 스크립트 | Validation Retreat, 해킹 54~76%(불가능 과제) | 없음 | **게이트 통과** (10-23: G1 36문항 test 14/14·14/14, G2 품질형 haiku +41%/opus +20% 회귀 0, G3 본문 31줄. 기준선은 충돌형에서 두 모델 5/5 테스트 기대값 변경(공개적으로). 훅은 **보류(오탐)**: Edit|Write 매처는 opus의 `sed -i`에 안 걸리고, Bash까지 막으면 정당한 테스트 갱신 과제가 0/5 완료. `study/gate-eval-round-2.md` ③) |
| 22 | `scope-guard` | skill + scripts | 이슈 경로·심볼 vs diff 파일 집합, LOC 예산 | 크기 δ0.17, 부작용 22.3% | simplify와 다름 | 4순위 (오탐 측정 설계 필요) |
| 23 | `impact-map` | scripts | 변경 심볼 참조처 열거 JSON | 부작용 22.3% | 없음 | 보류: 13번의 연관 테스트 선택에 흡수. 16번 regression-guard와 통합 |
| 24 | `dep-add-gate` | scripts | 매니페스트 diff 시 audit·라이선스·크기 | 의존성 리버트 12.5% | security-review 부분 | 아이디어 |
| 25 | `pr-dedupe-check` | scripts | PR 전 gh로 중복 PR 조회 | 중복 23%+ | 없음 | 보류: 로컬 작업 중심인 우리 워크플로에 효용 낮음 |
| 26 | `loop-breaker` | skill + scripts | 실패 시그니처 반복 감지 시 전환 요구 | 비진전 반복 | abstain-or-fix 인접 | 아이디어 |
| 27 | `coverage-delta` / `dead-code-sweep` / `migration-reversibility` | scripts | 비용형 후보 풀 | 낮음 | simplify 부분 | 아이디어 |
| 28 | secret-scan, force-push 차단 | **hook** | 스킬 아님 | — | security-review | §3.2에 따라 반복 위반 관찰 후 훅으로 |

### 통합 우선순위 (리서치 1+2, 2026-10-23)

라운드 2 착수 순서: **① verify-before-done(13⊕20) → ② repro-first v2(14) → ③ test-integrity-check(21)**. 근거: ①은 효과 근거(R1)와 최다 빈도 실패(R2)가 만나는 유일한 지점, ②는 효과 근거 최강·기준선 보유, ③은 결정적 도구의 진짜 빈칸. 상세는 `study/deep-research-failure-driven.md` 6~7절. 채택 전 §6.1 1차 출처 검증: 2601.15195, 2510.20270, 2509.13941.

선정 기준: (a) 내장과 안 겹치는 빈칸, (b) 결정적 부분을 scripts/로 빼서 경량 가능, (c) G2를 **측정 가능한 assertion**으로 조작화할 수 있음, (d) 목적 1~4 중 하나에 직접 기여. 1번은 나머지 셋의 측정 도구이므로 먼저 만든다.
