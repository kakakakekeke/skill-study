# skill-study

Claude Code용 스킬과 플러그인을 만들고 실험하는 작업장.

## 구조

```
skill-study/
├── skills/     # 독립 스킬 (SKILL.md 단위)
├── plugins/    # 플러그인 (plugin.json 단위, 스킬·커맨드·훅 번들)
├── docs/       # 설계 메모, 아이디어 백로그
├── CLAUDE.md   # 이 저장소에서 Claude가 따를 규칙
└── README.md
```

## 작업 흐름

1. `docs/ideas.md`에 아이디어를 적는다.
2. 스킬이면 `skills/<name>/`, 플러그인이면 `plugins/<name>/`에 만든다.
3. 로컬에서 테스트한다.
   - 스킬: `~/.claude/skills/`에 심볼릭 링크 후 호출
   - 플러그인: `claude --plugin-dir ./plugins/<name>`
4. 안정화되면 별도 저장소나 마켓플레이스로 옮긴다.

## 로컬 테스트용 스킬 링크

```bash
ln -s "$(pwd)/skills/<name>" ~/.claude/skills/<name>
```
