# skills/

독립적으로 배포 가능한 스킬 모음. 스킬 하나당 디렉터리 하나.

```
skills/
└── <skill-name>/
    ├── SKILL.md          # 필수: frontmatter(name, description) + 지침
    ├── references/       # 선택: 필요할 때만 읽는 상세 자료
    ├── scripts/          # 선택: 결정적 작업을 위한 스크립트
    └── evals/            # 선택: 트리거/품질 평가 케이스
```

- 디렉터리 이름 = `SKILL.md`의 `name` (kebab-case)
- `description`은 "무엇을 하는가 + 언제 트리거되는가"를 3인칭으로 작성
- 새 스킬은 `skill-creator` 스킬로 시작한다
