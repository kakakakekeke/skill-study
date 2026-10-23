# 딥 리서치: 개발 품질(품질형) 스킬 후보 (2026-10-23)

> 증거 자료. 규칙 변경은 `principles.md`에서만. 백로그 반영은 `ideas.md` 13~19번.
> 방법: deep-research 워크플로(검색 5갈래 → 출처 23개 → 주장 110개 → 25개 3표 교차 검증 → 18 확정·7 기각). 원본 결과는 세션 작업 디렉터리에만 있고 여기엔 요약을 적는다. **§6.1에 따라 설계 전 1차 출처를 직접 읽는 독립 검증이 필요하다.** 특히 2026년 프리프린트(SWE-Doctor, FixedBench, TDAD, DCAS)는 독립 재현이 없다.

## 1. 질문

라운드 1에서 품질형 통과는 repro-first 하나였다. 모델의 행동 순서를 바꿔 개발 품질을 확연히 올리고, with/without assertion으로 측정 가능하며, 큰 모델에서도 효과가 남는 스킬 후보는 무엇인가. 대상 스택 Python·JS/TS.

## 2. 확정된 발견 (검증 투표 통과)

| # | 발견 | 근거·수치 | 모델 크기 | 신뢰 |
|---|---|---|---|---|
| F1 | superpowers의 세 "철칙" 스킬(TDD, systematic-debugging, verification-before-completion)은 전부 트랜스크립트 assertion으로 조작화 가능. 단 효과 수치 없음, 훅 강제 없음, 저자 스스로 "모델이 합리화하며 무시, 6회 반복 후 준수" 보고 | 원문 확인. 포크에서 test-runner-output 존재 13→100% 소표본 | — | 높음(존재) / 없음(효과) |
| F2 | 재현 → 런타임 진단 → 수정 순서는 프론티어 모델에서도 해결률을 올림. 단 재현 테스트가 "올바른 이유로 실패"할 때만. 외부 재현 생성기를 그대로 끼우면 fail-to-fail 테스트(30~58%)가 오도해 무효 | SWE-Doctor: Pro 50.5→59.4%, GPT-5.4 55.1→65.4, Sonnet 4.6 45.8→59.8, 10/10 조합 개선. Verified 이득(+0.7~1.9pp)은 Pro 50개 표본의 SD(2.0~2.2)와 비슷한 크기(우리 추론; 논문은 Verified 분산 미보고). 비용 Verified 1.9배, **Pro 1.2배** | GPT-5.4, Sonnet 4.6 | 높음 ✅ 7절 |
| F3 | "먼저 재현하라"만으로는 버그 없는 상황에서 중단 판단이 안 좋아지거나 악화. "재현 후 이슈 없으면 변경 없이 보고"(abstain-or-fix)는 정답 중단 65→80.5%(Sonnet 4.6), 60.5→88.5%(GPT-5.4 mini). 대가로 부분 수정 코드에서 과잉 중단 70.7→81.3%, 77.3→93.6% | FixedBench(**프리프린트, under review**), McNemar p<0.01. Opus 미측정 | Sonnet 4.6 | 높음 ✅ 7절 |
| F4 | 절차형 TDD 프롬프트 단독은 해결률 동률(31%=31%)이고 회귀율을 6.08→9.94%로 늘림 | TDAD, 30B 4-bit, n=100, 단일 실행, 유의성 없음 | 소형만 | 중간 |
| F5 | 행동 전 ≤8단계 계획(plan-first)은 Claude Code 스캐폴드에서 +5.4pp(42.8→48.2). 스캐폴드 의존(다른 곳 +1.4~1.8), 대형 모델 미검증 | DCAS(ASE '26), Qwen3-Coder-30B, 단일 실행 | 소형만 | 중간 |
| F6 | "스스로 검토하고 고쳐라"(self-repair)는 외부 근거 없이는 리샘플링 대비 ≤1.08배. 병목은 피드백 품질. 사람/강한 모델 피드백이면 1.58배 | Olausson et al. ICLR 2024, GPT-4(2023) | 구형 | 높음 |
| F7 | "제출 전 pytest를 돌려 이슈 설명대로 실패하는지 확인하라" 한 줄이 SWT-Bench 15.9→18.5%, 전용 도구를 넘음. **p<0.1%는 libro 대비 우위에 붙은 수치이며 +2.6pp 자체의 유의성은 미검정.** 비용 +65% | SWT-Bench(원문에 학회 표기 없음), GPT-4만 | 구형 | 중간 ✅ 7절 |
| F8 | CoT·Few-shot 같은 추론 스캐폴드는 모델이 커지거나 추론을 내장하면 이득이 ±3pp로 줄고 지연 +20~80%, 반복 일관성 하락 가능 | Wharton GAIL 2025, ICSME 2026 | 추론 모델 | 중간 |

## 3. 기각된 주장 (반영하지 않음)

- TDAD의 "GraphRAG+TDD로 회귀 70% 감소", "20줄 SKILL.md가 107줄보다 낫다(12→50%)" — 1-2, 0-3.
- ~~SWT-Bench의 "재현 테스트 필터 정밀도 47.8%", "테스트 생성과 수정 성공 무상관" — 0-3.~~ **→ 7절에서 번복: 두 주장 모두 원문 §5.3·Table 6에 그대로 있음. 검증단 오판.**
- Aging of PE의 "Mistral CoT −13.8%", "CCoT만 일관 효과" — 0-3.
- GAIL의 "비추론 모델 CoT +0.04~0.135" — 0-3.

## 4. 후보 표 (G2 품질형 통과 가능성 예측)

| 후보 | 바꾸는 행동 | assertion 예 | 근거 | 내장 중복 | 예측 |
|---|---|---|---|---|---|
| **verification-before-completion** | 완료 선언 전 테스트/빌드를 새로 실행하고 종료 코드를 읽음 | 마지막 Edit 이후·최종 메시지 전 테스트 Bash 존재; 최종 메시지의 통과 주장이 실제 exit code와 일치; "should pass"류 0 | F7, F1 | 없음 | **높음** — 외부 근거 생성형, "거짓 완료율"이 명확한 지표, 모델 크기 무관하게 측정 가능 |
| **repro-first + abstain-or-fix** | 재현이 올바른 이유로 실패함을 확인; 재현 불가면 변경 없이 보고 | 진짜 버그: 첫 수정 전 비0 종료 재현. 이미 수정됨: diff 없음. 부분 수정: 중단 아님 | F2, F3 | 없음(라운드 1 확장) | **높음** — 단 부분 수정 fixture의 과잉 중단을 같은 eval에서 재야 유효 |
| plan-first (≤8단계) | 첫 Edit 전 번호 매긴 계획 | 계획 블록 존재, 단계 ≤8, 계획 파일 ∩ 실제 수정 파일 Jaccard | F5 | **Claude Code plan mode와 중복 가능성 — §3.1 확인 필수** | 중간 — 소형만 검증, opus 소멸 위험 |
| runtime-diagnose | 재현 후 수정 전 런타임 관찰(pdb/console.log) | 첫 수정 전 디버거·로그 삽입 실행 | F2 어블레이션(F→F 40.6→53.1) | 없음 | 중간 — 재현 불확실 케이스에 집중, 비용 1.9배 |
| regression-guard | 수정 후 변경 모듈을 임포트하는 기존 테스트 전체 실행 | 완료 전 영향 범위 테스트 실행, P2P 실패 0 | F4(회귀율은 별도 지표 필요) | 없음 | 중간(품질) / 높음(비용형: 변경파일→테스트 매핑은 scripts/로 전면 대체) |
| three-strikes | 동일 테스트 3회 실패 시 중단·설계 재검토 | 3회 실패 후 추가 Edit 없이 질문/요약 | F1(수치 없음) | 없음 | 낮음~중간 — 트리거 빈도 낮아 N 확보 어려움 |
| tdd-enforce | 실패 테스트 없이 프로덕션 코드 금지 | 첫 소스 Edit 전 테스트 Edit + 실패 실행 | F4(동률, 회귀 증가), F1(저준수) | 없음 | **낮음** (새 기능 과제에선 재검토 여지) |
| scope-limit | 변경 범위를 이슈 관련 파일로 제한 | diff 파일·라인이 골든 대비 k배 이내, 무관 파일 0 | 직접 근거 없음 | simplify와 일부 | 낮음~중간(비용형 가능) |
| self-review-then-fix | 수정 후 스스로 검토 | — | F6(≤1.08배) | **code-review 중복** | 낮음 — 만들지 않음 |
| CoT/"step by step" 가이드라인 | — | — | F8 | — | 낮음 — 기각 확정(§3.5 가설 강화) |
| dependency-impact | 변경 심볼 참조처를 스크립트로 열거 후 수정 | — | 직접 수치 없음(GraphRAG 주장 기각) | 없음 | 낮음(품질) / 중간(비용형) |
| migration-safety | — | — | 근거 없음 | — | 후속 조사 |

## 5. 상위 3개 eval 설계 초안

공통: 기준선 5회 반복, 노이즈 바닥 = max(관측, 3/N), 모든 fixture에 P2P 회귀율 부가 기록(F4 교훈). 모델 haiku·opus(가능하면 sonnet 추가).

**[1] verification-before-completion**
- fixture: Python(pytest)·TS(vitest) 각 "수정 과제 + 숨은 회귀" — 겉보기 수정 후 다른 테스트가 깨짐(의존 함수 시그니처 변경), 빌드는 되나 `tsc` 실패, pytest import 오류로 0 tests ran.
- assertion: (a) 마지막 Edit 이후 테스트/빌드 Bash 존재, (b) 최종 메시지 통과 주장 = 실제 exit code, (c) 추정 표현 0.
- 지표: 거짓 완료율, 실제 통과율, 토큰. scripts/verify.sh가 테스트+타입체크+린트를 한 번에 돌려 JSON 요약(토큰 절감).

**[2] repro-first abstain-or-fix 확장**
- fixture: 각 스택 3군 — 진짜 버그(기존 fixture 재사용), 이미 수정됨(이슈 텍스트 동일, 코드는 패치됨), 부분 수정(틀린 패치 적용).
- assertion: 진짜 버그군 "첫 수정 전 재현 + 비0 종료", 이미수정군 "diff 없음 + 보고", 부분수정군 "중단 아님".
- 지표: 해결률, 정답 중단율, 잘못된 중단율 동시 보고. scripts/repro_check.py — exit code와 assertion 메시지가 이슈 키워드와 겹치는지 판정(fail-to-fail 걸러냄).

**[3] plan-first** (§3.1 내장 plan mode 중복 확인 후에만)
- fixture: 3파일 이상 다단계 과제 10개(Python: 모델 필드→마이그레이션→API→테스트, TS: 타입 변경→소비자 3곳→테스트).
- assertion: 첫 Edit 전 계획 블록, 단계 ≤8, 계획 파일과 실제 수정 파일 Jaccard.
- opus에서 효과 소멸 여부를 1차 체크포인트로. 소멸 시 비용형(턴 감소)으로 재분류.

## 6. 한계와 열린 질문

- **Opus를 실행자로 측정한 연구가 하나도 없다.** 프론티어에서 노이즈를 넘은 건 SWE-Doctor(Pro, GPT-5.4·Sonnet 4.6)와 FixedBench(Sonnet 4.6)뿐.
- 논문은 다단계 파이프라인을 측정했고, SKILL.md 한 장의 효과는 superpowers 포크 소표본 외 직접 측정이 없다. **준수율 자체를 재야 한다**(superpowers 저준수 이력).
- JS/TS 근거는 전무. 거의 전부 Python·SWE-bench 계열.
- superpowers 외 커뮤니티 저장소(mattpocock/skills, anthropics/skills)는 검증을 통과한 클레임이 없어 비교 불가.
- 열린 질문: 재현 테스트가 "올바른 이유로 실패"하는지를 경량 스크립트로 판정하는 신뢰할 방법; abstain-or-fix의 과잉 중단을 줄이면서 정답 중단을 유지하는 변형이 있는지.

## 7. 라운드 1과의 대조

문헌은 라운드 1 결론과 일치한다: 행동 순서를 바꾸고 **외부 근거(테스트 실행·종료 코드)를 생성시키는** 스킬만 효과가 있고, "더 생각하라"류 가이드라인은 큰 모델에서 소멸·역효과(§3.5 가설 → 근거 보강). repro-first가 유일한 품질형 통과였던 것도 F2·F7과 맞는다.

## 7. 1차 출처 독립 검증 (2026-10-23, §6.1)

핵심 세 편을 에이전트 3개가 각각 원문(arXiv HTML/PDF)만 읽고 "논문이 무엇을 보고하느냐"에 답하게 했다(전제 없는 질문, 표·절 번호 명시). 그 결과를 2절 발견과 대조했다.

### 7.1 SWE-Doctor (arXiv 2607.00990, NTU·KCL·PKU·UIUC·Tsinghua, 프리프린트, 코드 공개)

| 노트 주장 | 원문 | 판정 |
|---|---|---|
| Verified 73.7→75.7, Pro 50.5→59.4 | Table II 평균 그대로 | ✅ |
| GPT-5.4 Pro 55.1→65.4, Sonnet 4.6 Pro 45.8→59.8 | Table II | ✅ |
| 10/10 조합 최고 | Table II 행별 확인(DeepSeek Pro 58.9 > 57.9 포함) | ✅ |
| 5회 반복 54.0±2.0 vs 42.4±2.2 | Table VI(Pro 50개, GPT-5.4-mini) | ✅ |
| 기존 생성기 연결 74→71/71/73 | Table I(n=100, GPT-5.4) | ✅ |
| Stage 2 제거 시 FF 53.1→40.6, FP 60.0 동률 | Table V | ✅ |
| 단계 제거 시 8~10pp 하락 | Table IV(56.0 vs 46~48) | ✅ |
| 비용 1.9배 | Verified $0.43 vs $0.23 ✅. **Pro는 $0.64 vs $0.52 = 1.2배** — 노트가 비싼 쪽만 적음 | ⚠️ 보정 |
| Verified 이득은 SD 안 | 논문은 Verified 분산 미보고. Pro 표본의 SD를 외삽한 **우리 추론** | ⚠️ 표기 보정 |

설계에 중요한 원문 사실:
- Stage 1의 핵심은 **실행 기반 선별**: "타깃 코드에 도달한 뒤 assertion/예외로 실패하는 BRT만 유지, 환경 오류로 도달 전 실패하는 BRT는 폐기". 종료 조건은 "그냥 실패"가 아니라 "해당 요구사항 때문에 실패". → `repro_check.py`가 구현해야 할 판정 그 자체.
- Stage 2는 SKILL.md가 아니라 **PDB를 붙인 별도 디버깅 에이전트**이며 "런타임 증거 없이 결론 내리면 거부". SKILL.md 한 장으로 재현하기 어려운 부분. `runtime-diagnose` 후보는 이 격차를 감안해야 한다.
- FP/FF 분류는 **정답 패치 기준**(FP: 패치 후 통과, FF: 패치 후에도 실패). 우리 fixture는 정답을 알고 있으므로 같은 분류가 가능하다.
- Go 50개에서도 +4pp(36.0 vs 32.0, DeepSeek). 비Python 신호가 약하게나마 있음.

### 7.2 FixedBench — "Coding Agents Don't Know When to Act" (arXiv 2605.07769, ETH Zurich·LogicStar, **프리프린트 under review**, 코드 "공개 예정" URL 없음)

| 노트 주장 | 원문 | 판정 |
|---|---|---|
| Reproduce: Sonnet 65.0→65.5, GPT-5.4 mini 60.5→47.5 | Table 1, McNemar p=1.0 / 6.5e-5 | ✅ |
| Abstain-or-Fix: 65.0→80.5, 60.5→88.5 | Table 1, p=9.5e-3 / 2.3e-8 | ✅ |
| GPT-5.3 Codex 57.6→83.5 | §3.2, **SORCAR 하네스** 기준, p 미기재 | ✅(하네스 표기 추가) |
| 부분 수정 과잉 중단 70.7→81.3, 77.3→93.6 | Table 1(150개), p 미기재 | ✅ |
| 해결률 유지(72.5 / 65.5) | Table 1 Res. 열, CI 겹침, p 없음 | ✅ |
| "ICML 2026" | PDF 머리말 "Preprint. Under review." 학회명 없음 | ❌ 보정 |
| Opus 미측정, Python 전용 | §3.1 모델 목록(Sonnet-4.6만), §5 | ✅ |

설계에 중요한 원문 사실:
- 프롬프트 원문(Appendix E). Abstain or Fix: *"First, reproduce the issue described above. If the issue is not present (anymore), report that and don't make changes. Otherwise fix the issue and verify the reproduction now fails."* — 세 문장. SKILL.md에 그대로 쓸 수 있는 길이.
- trace 분석(§3.3, Sonnet): **편집 전 재현률** Issue 42.5% → Reproduce 70.0% → Abstain-or-Fix 81.5%. 이것이 라운드 1 repro-first의 결정적 검사("첫 소스 수정 전 실패 명령 실행")와 같은 지표다. 외부 연구에서 같은 지표가 쓰였다는 점이 우리 assertion 설계를 뒷받침한다.
- 저자 해석: "action bias는 더 생각한다고 풀리는 문제가 아니라 **과제 프레이밍**의 문제. 중단이 정당한 결과라고 말해 줘야 한다." 추론 노력 Low→Extra High에서 61.5→65.8, 유의하지 않음. → §3.5 가설("가이드라인은 효과 없음")과 F6·F8을 같은 방향에서 지지.
- Edit 프롬프트("Please edit the codebase…")는 중단률을 **악화**(Sonnet 65.0→56.5, mini 60.5→36.5). 우리 eval 프롬프트 문구가 결과를 흔들 수 있다는 경고. with/without 프롬프트는 중립적으로 써야 한다.
- 정답 테스트 파일이 이미 있으면 중단률 65.0→72.7(Appendix C). fixture에 테스트가 있는지가 변수.

### 7.3 SWT-Bench (arXiv 2406.12952 v3, ETH Zurich·LogicStar, 원문에 학회 표기 없음, 코드 공개)

| 노트 주장 | 원문 | 판정 |
|---|---|---|
| 15.9→18.5%, libro 14.1·aider 12.7·AutoCodeRover 9.1 초과 | Table 2 | ✅ |
| p<0.1% | §5.2: "outperforms **libro** … significant at p<0.1%". **SWE-Agent+ vs SWE-Agent 차이(+2.6pp ≈ 7/276)의 검정은 없음** | ❌ 의미 보정 |
| 개입은 "실행하라" 한 줄 | Fig. 14 tip 7: *"before submitting, make sure to run pytest and check if the code **fails as expected due to the issue description**. If it doesn't, revisit your code changes"* — "실행" + "올바른 이유로 실패하는지 확인" | ✅(내용 보강) |
| Claude 3.5 Sonnet 12.3 | Table 4 | ✅ |
| 비용 | SWE-Agent $291 → SWE-Agent+ $478 (+65%), Table 10 | 추가 |
| "NeurIPS 2024" | 원문·abs 모두 미표기 | ⚠️ 원문 미표기 |

**딥 리서치 검증단이 기각(0-3)한 두 주장이 원문에 있음**:
- "생성 테스트를 수정 패치 필터로 쓰면 precision 47.8%, recall 20%" — §5.3 원문 그대로.
- "테스트 생성 성공과 수정 성공은 상관 없음" — Table 6(overlap 7/44·50, p=72.8%), 결론 문장 "generating tests and fixes are distinct tasks of different difficulties".
→ 자동 검증의 "기각"은 "거짓"이 아니라 "검증단이 원문에서 찾지 못함"이다. 이 두 주장은 2절에 복원하지는 않되(후보 설계에 직접 쓰이지 않음), 교훈을 `principles.md` §6.1 근거에 추가한다.

### 7.4 검증 후 후보 판정 변화

| 후보 | 변화 |
|---|---|
| verify-before-done | 예측 **높음 유지**. 단 근거 강도는 낮춤: SWT-Bench +2.6pp는 미검정, 모델은 2023 GPT-4. 설계는 SWT-Bench 문구("올바른 이유로 실패하는지 확인")와 FixedBench "verify the reproduction now fails"를 합친다. **우리 eval이 이 스킬의 첫 유의성 검정이 된다.** |
| repro-first v2 | 예측 **높음 유지, 근거 가장 강함**. Sonnet 4.6에서 p<0.01, 편집 전 재현률 42.5→81.5라는 우리 assertion과 같은 지표가 외부에서 확인됨. 프롬프트 세 문장 확보. fixture 3군(진짜/이미 수정/부분 수정) 필수. |
| runtime-diagnose | 예측 **중간→낮음(품질형)**. 원문의 Stage 2는 디버거 에이전트라 SKILL.md로 재현하기 어렵고, 효과도 FF 케이스에 집중. 라운드 3 이후. |
| 전체 | 세 편 모두 Opus 미측정, Python 중심 유지. 게재 상태는 세 편 중 **학회 게재가 원문으로 확인된 것이 없음**(모두 프리프린트 또는 미표기). |
