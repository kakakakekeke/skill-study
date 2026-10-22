# 스터디: mattpocock/skills

- 원본: https://github.com/mattpocock/skills (로컬: `.ref/mattpocock-skills`)
- 읽은 시점: 2026-10-22, 커밋 `5beb35b`, 플러그인 버전 1.3.1
- 한 줄 요약: "프로세스를 소유하지 않는, 작고 조합 가능한 스킬 27개". GSD/BMAD/Spec-Kit 류의 무거운 프레임워크에 대한 반대 포지션이라 우리 원칙과 방향이 같다.

## 1. 저장소 구조

```
skills/
├── engineering/    # 20개, 코드 작업 (플러그인에 포함)
├── productivity/   # 7개, 비코드 작업 (플러그인에 포함)
├── in-progress/    # 베타, 공개하지만 플러그인 미포함
├── misc/           # 동결, 유지보수 안 함
└── deprecated/
.claude-plugin/plugin.json   # skills 배열에 promoted 스킬만 나열
.claude-plugin/marketplace.json
.agents/                     # 기여자(에이전트)용 규칙: invocation.md, writing-docs.md, ADR
.out-of-scope/               # 거절한 제안 한 건당 파일 하나 + 이유
docs/<bucket>/<skill>.md     # 사람용 문서 (What / When / Common questions / It's working if)
scripts/link-skills.sh       # ~/.claude/skills 에 심볼릭 링크
SCOPE.md                     # 이슈 채택 기준
```

각 스킬 폴더: `SKILL.md` + `agents/openai.yaml`(Codex 메타) + 선택적 참고 파일(`tests.md`, `mocking.md`, `SKILL-MECHANICS.md`).

## 2. 가장 중요한 설계 결정: 호출 축 (invocation)

스킬을 **하나의 축**으로만 나눈다. 누가 호출할 수 있는가.

| | user-invoked | model-invoked |
|---|---|---|
| frontmatter | `disable-model-invocation: true` | 없음 (기본) |
| description | 사람용 한 줄 요약. 트리거 문구 없음 | 모델용. "Use when ..." 트리거 문구 풍부하게 |
| 컨텍스트 비용 | **0** (description이 모델에 안 올라감) | description이 항상 로드됨 |
| 역할 | 오케스트레이션 (`/grill-me`, `/implement`) | 재사용 가능한 규율 (`grilling`, `tdd`) |
| 다른 스킬이 호출 가능? | **불가** | 가능 |

규칙: user-invoked는 model-invoked를 부를 수 있지만, 그 역은 없고 user-invoked끼리도 못 부른다.

이 결정의 효과:
- `/grill-me`의 SKILL.md는 **7줄**이다. 본문은 `Call the Skill tool with "grilling".` 한 줄. 실제 로직은 model-invoked `grilling`에 있다.
- `/grill-with-docs`는 `grilling` + `domain-modeling` 두 번 호출. 조합으로 새 스킬을 만든다.
- 자주 안 쓰는 건 user-invoked로 돌려서 토큰을 0으로 만든다. **"손으로만 켤 거면 description 비용을 내지 마라"**가 원칙.

스킬 간 의존은 반드시 `Call the Skill tool with "<name>"` 문장으로 표현한다. `../other/FILE.md` 상대 링크나 `/name` 언급은 안 쓴다. 이유: 하네스 중립 + 실제로 호출될 확률이 높음.

## 3. 스킬 작성 이론: writing-for-agents

이 저장소의 메타 스킬. 스킬·CLAUDE.md·참고 문서를 쓰는 방법 자체를 정의한다. 우리 프로젝트에 가장 직접적으로 쓸 내용.

**두 가지 비용(two loads)**
- *Context load*: 항상 로드되는 텍스트가 매 턴 쓰는 토큰과 주의력.
- *Cognitive load*: 사람이 "어떤 문서가 있고 언제 쓰는지" 기억하는 비용. 최소화 대상이 아니라 "사람의 주도권의 대가". 판단이 중요한 곳에만 쓴다.

**정보 계층(information hierarchy)**
1. in-file step (순서 있는 행동)
2. in-file reference (필요시 참조하는 규칙)
3. disclosed reference (별도 파일, 포인터로만 도달)

"모든 분기가 필요한 건 인라인, 일부 분기만 쓰는 건 포인터 뒤로". progressive disclosure는 토큰 최적화가 아니라 계층 보호 수단.

**완료 기준(completion criterion)**: 모든 step은 "끝났는지 판별 가능한 조건"으로 끝나야 한다. 모호하면 premature completion이 생긴다. 먼저 조건을 날카롭게, 그래도 안 되면 시퀀스를 쪼개서 뒤 단계를 컨텍스트 밖으로.

**Leading word**: 모델 사전학습에 이미 있는 압축 개념어(_tracer bullet_, _seam_, _red_, _tight_)를 문장 대신 토큰으로 반복 사용. 설명 비용을 0에 가깝게 하고 행동을 일관되게 고정. "fast, deterministic, low-overhead" → _tight_.

**부정 금지**: "하지 마라"는 금지 대상을 컨텍스트에 끌어와 오히려 활성화시킨다. 긍정형으로 목표 행동을 쓴다.

**Pruning**
- 단일 진실 공급원. 환경(package.json, config)이 이미 말해주는 건 문서에 안 쓴다(캐시는 조회가 비쌀 때만).
- *No-op 테스트*: "이 문장이 기본 동작을 바꾸는가?" 안 바꾸면 문장 전체 삭제. 모델 상대적이므로 토론이 아니라 실행으로 판정.

## 4. 관찰한 패턴

**얇은 라우터 + 두꺼운 참조**
- 라우터(user-invoked): `grill-me`(7줄), `implement`(17줄), `handoff`(16줄)
- 참조(model-invoked): `tdd`(38줄 + tests.md + mocking.md), `codebase-design`(114줄), `writing-for-agents`(81줄 + SKILL-MECHANICS.md)
- `ask-matt`: user-invoked 스킬이 많아져 기억이 안 될 때를 위한 "라우터 스킬". 힌트만 주고 직접 못 부름.

**하드/소프트 의존 분리 (ADR 0001)**
- 설정 없으면 결과가 틀리는 스킬(`to-spec`, `to-tickets`, `triage`)만 "run `/setup-...`" 한 줄을 넣는다.
- 설정 없어도 덜 날카로울 뿐인 스킬(`tdd`, `diagnosing-bugs`)은 "GLOSSARY.md가 있으면 읽어라" 수준의 느슨한 문장만. 설정 포인터를 카고컬트하지 않는다.

**구현 vs 리뷰 분리 (retro 스킬의 핵심 관점)**
- 구현 에이전트는 컨텍스트 압력이 가장 크다(탐색+코딩+디버깅). 리뷰 에이전트는 diff만 받으므로 압력이 작다.
- 따라서 **코딩 표준 강제는 리뷰 에이전트 책임**. CLAUDE.md는 네비게이션 포인터만, `CODING_STANDARDS.md`는 리뷰 시에만 읽음.
- 기계적 규칙(금지 API, import 형태, 파일 위치)은 문서가 아니라 linter/pre-commit/CI로. 문서에는 판단이 필요한 것만.

**grilling의 설계 트리 + frontier**
- 질문을 "결정 트리"로 보고, 전제가 해결된 질문(frontier) 전부를 한 라운드에 번호 매겨 묻는다. 각 질문에 추천 답 제시, "yes"면 추천 수락.
- 사실 조사는 에이전트 몫(서브에이전트), 결정은 사람 몫.
- AskUserQuestion 같은 하네스 네이티브 UI는 의도적으로 안 씀(하네스 중립 + 선다형이 사고를 좁힘).

**스코프 관리를 저장소 안에 문서화**
- `SCOPE.md`: 이슈는 "실제 세션에서 관찰된 실패" + "철학 부합" 둘 다 통과해야 열림. 가설적 개선 제안은 닫음.
- `.out-of-scope/`: 거절 사유를 파일로 축적. 반복 제안 방지. 새 스킬 기여는 전면 거절("조합으로 되면 새 스킬 아님").

**멀티 하네스**
- 같은 SKILL.md를 Claude Code / Codex / Copilot / Gemini / Cursor 등에서 쓴다. `agents/openai.yaml`이 Codex용 메타.
- 하네스 내장 명령과 이름 충돌(`/code-review`, `/research`)은 네임스페이스(`/mattpocock-skills:code-review`)로 해결, 이름 안 바꿈.

## 5. 우리 프로젝트에 가져올 것 / 가져오지 않을 것

**가져올 것**
- user-invoked / model-invoked 축으로 토큰 비용 설계. 손으로만 켤 스킬은 `disable-model-invocation: true`.
- 얇은 라우터 + 두꺼운 참조 구조. SKILL.md 본문은 짧게, 상세는 references/.
- writing-for-agents의 no-op 테스트, leading word, 긍정형 지시, 완료 기준. → 우리 eval 설계의 측정 항목으로 쓸 수 있다.
- 하드/소프트 의존 분리 원칙.
- 구현/리뷰 컨텍스트 압력 분리 관점. "반복 오류 자가 보완" 목적과 직결: 기계적 오류는 훅/린터, 판단 오류는 리뷰 규칙.
- `.out-of-scope/` 식의 거절 기록. 우리는 `docs/decisions/`로.

**가져오지 않을 것 / 다르게 할 것**
- 멀티 하네스 지원(`agents/openai.yaml`). 우리는 Claude Code 전용이므로 불필요한 파일.
- 이슈 트래커 통합(`to-spec`, `to-tickets`, `triage`, `setup-*`). 우리 목적(품질·토큰·산출물·자가보완)과 거리가 있고 무겁다.
- 내장 스킬과 이름이 겹치는 것들(`code-review`, `research`, `prototype`, `tdd`?). 우리 원칙 2번에 따라 **만들지 않고 내장을 연동**한다. 참고로 이 저장소는 충돌을 네임스페이스로 피하는 쪽을 택했다.
- `grilling`: Claude Code 내장 plan mode / AskUserQuestion과 역할이 겹친다. 재구현 대신 연동 여지만 검토.
- eval 체계가 **없다**. 이 저장소는 "작성자가 매일 쓴다"가 검증 수단이다. 우리는 skill-creator의 eval 도구로 효과를 측정해야 한다. 이 지점이 우리 프로젝트의 차별점.

## 6. 심층 분석: diagnosing-bugs

파일: `SKILL.md`(138줄) + `scripts/hitl-loop.template.sh` + `agents/openai.yaml`. model-invoked. 2026-05-31 `diagnose`로 추가, v1.0.0에서 현재 이름으로 변경.

### 구조: 6단계 게이트

체크리스트가 아니라 **게이트**다. 앞 단계의 조건이 참이 되기 전에는 다음 단계에 들어갈 수 없다.

| 단계 | 하는 일 | 다음 단계로 가는 조건 |
|---|---|---|
| 1. 피드백 루프 구축 | 이 버그에서 red가 되는 **명령 하나**를 만든다 | 명령을 한 번 이상 실행해 출력을 보였고, red-capable·deterministic·fast·agent-runnable |
| 2. 재현 + 최소화 | 루프를 돌려 red 확인, 요소를 하나씩 빼며 최소 재현 | 남은 모든 요소가 load-bearing (하나 빼면 green) |
| 3. 가설 | 3~5개 **반증 가능한** 가설을 순위 매겨 사용자에게 먼저 보임 | 각 가설이 "X가 원인이면 Y를 바꾸면 사라진다" 형태의 예측을 가짐 |
| 4. 계측 | 가설별 예측에 대응하는 프로브, 변수 하나씩 | 모든 디버그 로그에 `[DEBUG-xxxx]` 태그 |
| 5. 수정 + 회귀 테스트 | 올바른 seam이 있으면 테스트 먼저, 수정 후 원본 루프 재실행 | seam이 없으면 **그 자체가 발견**으로 기록 |
| 6. 정리 | 원본 재현 불가 확인, 태그 grep 결과 0, 맞은 가설을 커밋 메시지에 | 체크리스트 전부 통과 |

### 핵심 사상: "루프가 스킬이다"

- Phase 1에 **불균형하게** 노력을 쏟으라고 명시한다. "Build the right feedback loop, and the bug is 90% fixed."
- 가장 중요한 한 문장: *"If you catch yourself reading code to build a theory before this command exists, stop."* 에이전트의 기본 행동(코드 읽고 추측)을 명시적으로 차단하는 것이 이 스킬의 존재 이유다.
- 루프를 만드는 방법 10가지를 **선호 순서대로** 나열한다. 실패 테스트 → curl → CLI+fixture → headless browser → 캡처 재생 → 임시 하네스 → fuzz → bisect → 차등 비교 → HITL 스크립트.
- *tight*라는 leading word 하나에 "빠르고, 결정적이고, 신호가 날카로운"을 압축했다. "30초짜리 flaky 루프는 없는 것과 비슷하고, 2초짜리 결정적 루프는 디버깅 슈퍼파워."
- 비결정적 버그는 "깨끗한 재현"이 아니라 **재현율을 올리는 것**이 목표. 100번 반복, 병렬화, 스트레스, sleep 주입.

### 설계상 주목할 점

- **루프를 못 만들면 멈춘다.** 시도한 것을 나열하고 사용자에게 환경 접근, 캡처 산출물, 임시 계측 허가 중 하나를 요청한다. 가설로 넘어가지 않는다.
- **단일 가설 금지.** 첫 번째 그럴듯한 생각에 앵커링되는 것을 막기 위해 3~5개를 먼저 다 뽑는다. 사용자에게 보이는 이유는 "방금 #3 배포했어요" 같은 도메인 지식이 순위를 즉시 바꾸기 때문. 단, AFK면 블록하지 않고 진행.
- **태그된 로그.** `[DEBUG-a4f2]` 같은 고유 접두사. "태그 없는 로그는 살아남고, 태그된 로그는 죽는다." 정리를 grep 하나로 환원.
- **강제 red 검증** (2026-10-07 추가): 코드나 fixture를 변형해 red를 만들었다면, 원본과 `diff`해서 변형이 실제로 적용됐는지 증명한 뒤에 그 red를 믿어라. 실제 세션에서 "변형이 안 먹었는데 red라고 착각"한 실패가 있었다는 뜻.
- **Redact 섹션** (2026-08-06 추가): 명령·출력·캡처를 보여주는 스킬이라 시크릿 노출 위험. 먼저 `<REDACTED>` 처리, 자격증명은 env var로. 처음엔 길게 썼다가 "prose로 트림"한 커밋이 따로 있다(토큰 절약 정비).
- **HITL 템플릿.** 사람이 클릭해야만 재현되는 경우에도 `step`/`capture` 두 헬퍼로 구조화된 bash 스크립트를 만들어 사람을 "드라이브"한다. 캡처 값은 `KEY=VALUE`로 출력돼 에이전트가 파싱. Snyk가 고위험으로 오탐한 유일한 스킬.
- **올바른 seam이 없으면 테스트를 안 쓴다.** 얕은 seam의 회귀 테스트는 거짓 확신을 준다. 그 부재를 아키텍처 문제로 기록하고 `improve-codebase-architecture`로 넘긴다.

### 알려진 문제 (docs 페이지에 저자가 직접 기록)

- **과잉 트리거** (#578, 4명 보고): "something is broken" 류 설명에 바로 발동해 간단한 질문에도 재현 시나리오를 만든다. GPT 계열에서 특히 심함. "가벼운 접근으로 시작해 필요할 때만 전체 진단"으로 바꾸기로 했으나 미반영. → **우리 eval에서 트리거 정확도를 측정해야 하는 이유의 실례.**
- **수정 전 게이트 없음** (#124, open): Phase 4→5 사이에 사용자 확인이 없어 근본 원인에 합의 전 코드를 고칠 수 있다.
- **triage와 중복**: triage의 3단계가 이 스킬 Phase 1~2의 얕은 버전인데 서로 언급이 없다.
- 시크릿 유출(#674)은 docs 페이지엔 open으로 적혀 있지만 SKILL.md에는 Redact 섹션이 들어갔다. 문서와 스킬의 동기화가 어긋난 예.

## 7. 심층 분석: retro

파일: `SKILL.md`(44줄) + `agents/openai.yaml`. **user-invoked**. 2026-09-24에 `in-progress`에서 `engineering`으로 승격.

### 구조: 4단계 + 참조

1. `writing-for-agents` 호출 (스타일 가이드이자 **판정 기준**: no-op 정의, 좋은 스킬의 정의).
2. 세션의 **1차 자료**를 읽는다. 지정 없으면 현재 세션, 아니면 머신의 세션 로그.
3. 7개 카테고리에서 개선 후보를 찾는다.
4. 심각도 순으로 **제안만** 한다. 사용자가 고르기 전까지 아무것도 바꾸지 않는다.

### 7개 카테고리와 "어디에 고치는가"

| 세션에서 관찰된 문제 | 처방 |
|---|---|
| 파일/사실을 찾는 데 오래 걸림 | 이미 읽는 파일에서 **navigation pointer** |
| 도구가 잡을 수 있던 실수 | **자동 검사**: lint 규칙, 타입, 테스트, pre-commit, CI |
| 리뷰어가 판단형 실수를 놓침 | `CODING_STANDARDS.md`에 규칙 (리뷰어만 읽음) |
| CLAUDE.md/AGENTS.md가 큼 | 조향 문구를 표준이나 검사로 **빼냄** |
| 비싼 도구 호출 | 도구 간소화 또는 교체 |
| 조향 파일에 행동을 안 바꾸는 문장 | **no-op 삭제** |
| 필요한 정보에 접근 불가 | 접근 확대: dev server 로그 tee, 읽기 전용 서비스 접근 |

### 핵심 사상 3가지

**(1) 코드가 아니라 환경을 고친다.** 에이전트가 낸 버그, 20번의 도구 호출로 찾은 파일, 리뷰어가 놓친 규칙. retro는 이것들을 직접 고치지 않는다. "저장소의 무엇이 이걸 허용했는가"를 묻고, 다음 번에 막을 검사·포인터·표준을 제안한다.

**(2) 기계적 위반은 검사로, 판단은 문서로.** 규칙을 쓰기 전에 위반을 분류한다. 금지 API, import 형태, 파일 위치 같은 **기계적** 위반은 무조건 결정적 검사(linter 커스텀 규칙, pre-commit, CI). "검사는 실패할 수 있지만 표준 문서의 문장은 실패할 수 없다." 저장소에 가드레일(pre-commit도 CI도 없음)이 전혀 없으면 그 자체가 발견. **이미 있는데 안 연결된 검사가 있으면 "연결하라"가 발견이고, 새로 만들자는 제안은 틀린 것.**

**(3) 표준은 리뷰어의 것.** 구현 에이전트는 탐색+코딩+디버깅으로 컨텍스트 압력이 최대. 리뷰 에이전트는 diff만 받으므로 여유가 있다. 그러므로 새 규칙은 적용할 여유가 있는 곳(리뷰)으로 간다. **CLAUDE.md에는 절대 넣지 않는다**: 모든 세션에 로드되어 다른 모든 문장의 가중치를 낮추고, 코드가 바뀌면 낡는다.

### 저자가 밝힌 약점

- **일반론 발명**: "작업이 끝나면 AI가 세션 중간의 고생을 잊고 카테고리를 채우려고 일반적 조언을 지어낸다." 그래서 모든 후보는 세션의 특정 순간으로 추적 가능해야 한다. 추적 안 되는 후보는 버려라.
- **규칙 누적**: prose의 no-op은 삭제 제안을 하지만, 자기가 지난달 제안한 lint 규칙·훅·CI는 감사하지 못한다. 세션 하나만 보기 때문. "좋은 코드에 계속 걸리는 규칙"은 사용자가 직접 지워야 한다.
- **자동화 거부**: "매 세션 자동 실행"과 "자동 적용"을 의도적으로 거부. 한 사용자가 "좋은 변경을 막는 auto-hook에 당했다"고 보고. 무난한 세션은 가르칠 게 없어서 매번 돌리면 아무도 필요 없는 규칙만 쌓인다.
- **메모리 시스템이 아님**: 일어난 일을 저장하지 않는다. 실수가 일어날 수 없게 환경을 바꾼다.

### 체인에서의 위치

```
grill-with-docs → to-spec → to-tickets → implement → code-review → retro
                                                diagnosing-bugs → retro (같은 세션)
```

diagnosing-bugs는 retro를 호출할 수 없다(user-invoked는 호출 불가). 사람이 같은 세션에서 `/retro`를 쳐야 한다.

## 8. '반복 오류 자가 보완' 목적과의 연결

우리 목적 4번은 "개발 중 반복적으로 발생하는 오류를 스스로 감지하고 보완하면서 진행"이다. 두 스킬은 이 루프의 두 반쪽이다.

```
[오류 발생] → diagnosing-bugs (이번 오류를 고친다)
                  ↓ 맞은 가설을 커밋 메시지에 기록
             retro (이 오류가 다시 일어날 수 없게 환경을 바꾼다)
                  ↓ 제안 → 사람 승인 → 검사/포인터/표준 추가
[다음 세션] → 같은 오류는 검사가 잡는다
```

### 그대로 가져올 원칙

1. **기계적 오류는 문서가 아니라 검사로 막는다.** "반복 오류 자가 보완"을 CLAUDE.md에 "~하지 마라"를 쌓는 방식으로 하면 토큰 절약 목적과 충돌하고, 부정형 지시라 효과도 낮다. 훅·린터·pre-commit이 정답. 이건 우리 목적 2(토큰 절약)와 4를 동시에 만족시킨다.
2. **구현/리뷰 분리.** 판단형 규칙은 리뷰 단계에서만 읽는 파일로. Claude Code 내장 `/code-review`, `/simplify`가 읽을 표준 파일을 두는 식으로 **내장 스킬과 연동**할 수 있다(원칙 2).
3. **"이미 있는데 안 연결된 검사"를 먼저 찾는다.** 새 도구를 만들기 전에 package.json 스크립트와 CI 워크플로를 읽는다.
4. **루프 우선.** 오류를 고칠 때 재현 명령이 먼저, 추측은 나중. 이건 eval 설계에도 그대로 적용된다: 스킬의 효과를 측정하는 "red가 되는 명령"이 없으면 그 스킬은 검증된 게 아니다.
5. **모든 후보는 특정 순간으로 추적 가능해야 한다.** 일반론을 지어내지 않게 하는 완료 기준. 우리 eval의 품질 지표 후보.

### 우리가 다르게 할 지점 (저자가 인정한 한계가 곧 우리 기회)

| mattpocock의 선택 | 한계 | 우리 방향 |
|---|---|---|
| retro는 세션 하나만 본다 | 어떤 오류가 **반복**되는지 알 수 없다 | 세션 간 **오류 패턴 축적**이 필요. 단, 메모리 시스템이 아니라 "검사로 환원된 것"만 남기는 방식으로 |
| 자기가 만든 검사를 감사하지 않는다 | 규칙이 영원히 쌓인다 | 검사에 **발생 횟수/최근 발화 시점**을 붙여, 더 안 걸리는 규칙은 제거 후보로 올리는 pruning 단계 |
| 자동 실행·자동 적용 거부 | 사람이 매번 `/retro`를 기억해야 함 | 자동 **적용**은 같은 이유로 거부. 그러나 "이 세션에서 같은 오류가 2회 이상 났다"는 **감지**는 자동화 가능(Stop 훅 등). 감지는 자동, 처방은 사람 승인 |
| diagnosing-bugs가 과잉 트리거 | 간단한 질문에도 무거운 절차 | 우리 스킬은 가볍게 시작하고 필요할 때만 깊어지는 **단계적 진입**. eval에서 트리거 정확도를 실측 |
| diagnosing-bugs → retro 수동 연결 | 고친 뒤 retro를 잊으면 학습이 안 됨 | 수정 완료 시점에 "이 오류를 막을 검사가 있는가"를 묻는 한 줄 체크를 수정 스킬 안에 둠 |
| 검증 수단 = 저자가 매일 쓴다 | 효과 입증 없음 | eval로 "스킬 있을 때 vs 없을 때" 반복 오류 재발률을 측정 |

### 내장 스킬과의 중복 점검

- Claude Code에는 `/code-review`, `/simplify`, `/security-review`가 내장. 리뷰 축은 **만들지 않는다**. 대신 그 리뷰어들이 읽을 표준 파일 위치와 형식을 정하는 쪽.
- 내장 `diagnosing-bugs` 대응물은 없다. 단, 우리 목적은 "하드 버그 진단" 자체보다 "반복 오류"에 있으므로, 10가지 루프 구축법 같은 두꺼운 참조는 가져오되 6단계 전체를 재구현할 필요는 없다.
- `retro` 대응 내장 스킬도 없다. 가장 유력한 첫 스킬 후보 영역. 단, Claude Code의 메모리 시스템·훅과 역할을 어떻게 나눌지가 설계 핵심.

## 9. 다음에 더 볼 것

- `skills/engineering/diagnosing-bugs/` : "반복 오류 자가 보완" 목적과 가장 가까운 스킬. scripts/ 포함.
- `skills/engineering/retro/` : 세션 후 환경 개선 제안. 자가 보완 루프의 출발점으로 참고.
- `skills/engineering/code-review/` : 표준/스펙 두 축을 병렬 서브에이전트로 분리한 구조.
- `skills/engineering/tdd/tests.md`, `mocking.md` : 참조 파일 작성 예시.
- `.agents/writing-docs.md` : 사람용 문서 템플릿 (It's working if 섹션이 eval 힌트가 될 수 있음).
- `skills/in-progress/loop-me/`, `chief-of-staff/` : 베타 스킬의 실험 방식.
