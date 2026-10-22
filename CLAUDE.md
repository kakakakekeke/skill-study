# skill-study

Claude Code 스킬·플러그인을 만드는 프로젝트. 각 하위 폴더의 README.md에 구조 규칙이 있다.

## 규칙

- 새 스킬을 만들 때는 `skill-creator` 스킬을, 플러그인을 만들 때는 `plugin-authoring` 스킬을 먼저 사용한다.
- 스킬은 `skills/<name>/SKILL.md`, 플러그인은 `plugins/<name>/.claude-plugin/plugin.json`이 진입점이다.
- 디렉터리 이름과 `name` 필드는 kebab-case로 일치시킨다.
- SKILL.md 지침은 간결하게 쓰고, 긴 자료는 `references/`로 분리한다.
- 스크립트는 `scripts/`에 두고 실행 가능 권한을 준다.
- 커밋 메시지는 한국어로 쓴다.
