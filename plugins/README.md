# plugins/

Claude Code 플러그인 모음. 플러그인 하나당 디렉터리 하나.

```
plugins/
└── <plugin-name>/
    ├── .claude-plugin/
    │   └── plugin.json   # 필수: name, description, version, author
    ├── skills/           # 선택: 번들 스킬
    ├── commands/         # 선택: 슬래시 커맨드 (.md)
    ├── agents/           # 선택: 서브에이전트 정의 (.md)
    ├── hooks/            # 선택: hooks.json
    └── .mcp.json         # 선택: MCP 서버 설정
```

- 로컬 테스트: `claude --plugin-dir ./plugins/<plugin-name>`
- 플러그인 안의 스킬은 `plugin-name:skill-name`으로 호출된다
