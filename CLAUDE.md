# skill-study

Claude Code 스킬·플러그인을 만드는 프로젝트. 경량, eval 검증, 내장 스킬과 연동이 핵심.

## 먼저 읽을 것

- **규칙의 유일한 원본: `docs/principles.md`.** 스킬을 제안·설계·수정하기 전에 §2 세 게이트와 §6.3 체크리스트를 본다.
- 문서 지도와 읽는 순서: `docs/README.md`
- 스킬·플러그인 레이아웃 규칙: `skills/README.md`, `plugins/README.md`

## 이 저장소의 규약 (코드에서 추론 불가한 것만)

- 새 스킬은 `skill-creator`, 플러그인은 `plugin-authoring` 스킬로 시작한다.
- 디렉터리 이름 = `name` 필드, kebab-case.
- `.ref/`는 외부 저장소 클론. 읽기 전용, 수정하지 않는다.
- 커밋 메시지는 한국어.
- 규칙을 바꿀 땐 `docs/principles.md`만 고친다. 스터디 노트에 결론을 쓰지 않는다.
- 리서치 결과는 1차 출처를 직접 읽는 독립 검증 후에만 원칙에 반영한다.
