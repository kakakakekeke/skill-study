# skill-study

Claude Code용 스킬과 플러그인을 만들고 실험하는 작업장.

## 구조

```
skill-study/
├── .claude-plugin/marketplace.json  # 배포 목록 (게이트 통과 스킬만)
├── skills/     # 독립 스킬 (SKILL.md 단위): 제작중 + 배포
├── deprecated/ # 게이트 미통과로 폐기한 스킬 (보존, 미배포)
├── plugins/    # 플러그인 (plugin.json 단위, 스킬·커맨드·훅 번들)
├── scripts/    # 저장소 검사 (check_marketplace.py, CI에서 실행)
├── docs/       # 규칙 원본(principles.md), 백로그, 스터디 노트
├── .ref/       # 참고용 외부 저장소 클론 (git 추적 안 함)
├── CLAUDE.md   # Claude용 포인터와 저장소 규약 (규칙 본문은 docs/principles.md)
└── README.md
```

## 규칙

모든 규칙은 [docs/principles.md](docs/principles.md) 한 곳에 있다. 핵심은 **세 게이트**: 정확한 트리거, 확연한 품질 향상, 과하지 않은 토큰. 셋을 eval로 입증한 스킬만 반영한다.

## 작업 흐름

1. `docs/ideas.md`에 아이디어를 적는다.
2. `docs/principles.md` §6.3 체크리스트로 만들 가치가 있는지 본다.
3. 스킬이면 `skills/<name>/`, 플러그인이면 `plugins/<name>/`에 만든다.
4. eval(§5)을 돌려 세 게이트를 통과시킨다.
5. 로컬에서 테스트한다.
   - 스킬: `~/.claude/skills/`에 심볼릭 링크 후 호출
   - 플러그인: `claude --plugin-dir ./plugins/<name>`
6. 측정 PR에서 상태를 정한다(`docs/principles.md` §6.4): 통과 → `.claude-plugin/marketplace.json`에 등록, 미통과 → `deprecated/`로 이동.

## 설치 (마켓플레이스)

```bash
claude plugin marketplace add kakakakekeke/skill-study
```

```bash
claude plugin install repro-first@skill-study
```

배포 중인 스킬: `flaky-check`, `repro-first`. 훅 플러그인: `verify-on-stop`. 플러그인 하나에 스킬 하나라 필요한 것만 설치한다.

## 로컬 테스트용 스킬 링크

```bash
ln -s "$(pwd)/skills/<name>" ~/.claude/skills/<name>
```

## 참고 저장소 (.ref/)

다른 사람의 스킬·플러그인을 공부할 때 `.ref/` 아래에 클론한다. 이 폴더는 `.gitignore`에 등록되어 커밋되지 않는다.

| 폴더 | 원본 | 메모 |
|---|---|---|
| `.ref/mattpocock-skills` | https://github.com/mattpocock/skills | 스킬 작성 패턴 참고 |

```bash
git clone https://github.com/<owner>/<repo> .ref/<owner>-<repo>
```
