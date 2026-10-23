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
- 여기 있는 스킬은 제작중이거나 배포 중이다. 배포 = `.claude-plugin/marketplace.json` 등록(세 게이트 통과), 미통과는 `deprecated/`로 옮긴다. 규칙은 `docs/principles.md` §6.4
- `gate-eval`은 이 저장소 전용 내부 도구라 등록하지 않는다

설치 (배포 중인 스킬):

```
/plugin install flaky-check --marketplace kakakakekeke/skill-study
/plugin install repro-first --marketplace kakakakekeke/skill-study
/plugin install test-integrity-check --marketplace kakakakekeke/skill-study
```

자동으로 안 켜질 때는 직접 부른다. 다른 스킬이 함께 설치돼 있으면 모델이 스킬을 덜 고르는 경우가 측정됐다(repro-first 수행 중 호출 haiku 11%·sonnet 56%, `docs/study/gate-eval-round-2.md` ⑤):

| 상황 | 호출 |
|---|---|
| 버그를 고칠 때 (재현 → 최소 수정 → 재발 방지) | `/repro-first <버그 설명>` (1.1.0부터 버그 신고로 보이는 요청에 사용 안내를 자동 주입, `REPRO_FIRST_INJECT=0`으로 끔) |
| 테스트가 가끔 실패하는지 잴 때 | `/flaky-check <명령 또는 테스트>` |
| 빨간 테스트를 코드만 고쳐 통과시킬 때 | `/test-integrity-check <과제>` |
