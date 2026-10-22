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

## 6. 다음에 더 볼 것

- `skills/engineering/diagnosing-bugs/` : "반복 오류 자가 보완" 목적과 가장 가까운 스킬. scripts/ 포함.
- `skills/engineering/retro/` : 세션 후 환경 개선 제안. 자가 보완 루프의 출발점으로 참고.
- `skills/engineering/code-review/` : 표준/스펙 두 축을 병렬 서브에이전트로 분리한 구조.
- `skills/engineering/tdd/tests.md`, `mocking.md` : 참조 파일 작성 예시.
- `.agents/writing-docs.md` : 사람용 문서 템플릿 (It's working if 섹션이 eval 힌트가 될 수 있음).
- `skills/in-progress/loop-me/`, `chief-of-staff/` : 베타 스킬의 실험 방식.
