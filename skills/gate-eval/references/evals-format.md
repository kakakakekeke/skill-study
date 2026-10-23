# evals 형식

## evals/evals.json (G2 품질)

```json
{
  "skill_name": "test-digest",
  "evals": [
    {
      "id": 1,
      "name": "pytest-two-failures",
      "prompt": "사용자가 실제로 칠 문장",
      "fixture": "evals/fixtures/pyproj",
      "files": [],
      "expected_output": "사람이 읽는 성공 기준",
      "expectations": ["LLM grader가 판정할 자연어 assertion"],
      "checks": [
        {"text": "결정적 검사 이름", "type": "regex_final", "pattern": "test_parse_range"},
        {"text": "...", "type": "regex_transcript", "pattern": "..."},
        {"text": "...", "type": "regex_outputs", "pattern": "..."},
        {"text": "...", "type": "script", "cmd": "python3 /abs/or/rel/check.py", "negate": false}
      ]
    }
  ]
}
```

- `prompt_without`(선택): without 설정에서 대신 쓸 프롬프트. user-invoked 스킬은 `/name …` 호출문이 스킬 없는 쪽에서 무의미하므로 같은 뜻의 자연어를 여기 둔다.
- `fixture`: 스킬 디렉터리 기준 경로. 내용이 임시 프로젝트 루트로 복사된다.
- `files`: 스킬 디렉터리 기준 파일·디렉터리. 프로젝트 루트에 같은 이름으로 복사.
- `checks.type`
  - `regex_final`: 최종 응답 텍스트에 패턴.
  - `regex_transcript`: 압축 트랜스크립트(`transcript.md`)에 패턴.
  - `regex_outputs`: 실행 후 프로젝트 사본(`outputs/`)의 텍스트 파일 전체에 패턴.
  - `script`: `cwd`=run 디렉터리, 환경변수 `RUN_DIR`. exit 0이면 통과. `outputs/`에서 실제 동작을 검증하는 데 쓴다(예: 고친 함수 import 후 assert). 상대 경로는 run 디렉터리 기준이므로 보통 절대 경로나 `$GATE_EVAL_SKILL`을 쓴다.
- 결정적으로 검사할 수 있으면 `checks`, 아니면 `expectations`. 둘 다 `grading.json`에 같은 형식(text/passed/evidence)으로 들어간다.
- grader에게는 with/without을 알려주지 않는다.

## evals/trigger.json (G1)

```json
[
  {"query": "구체적이고 현실적인 사용자 문장", "should_trigger": true},
  {"query": "키워드는 겹치지만 다른 도구가 맞는 근접 사례", "should_trigger": false}
]
```

- 10개/10개 안팎. should-not은 명백히 무관한 것이 아니라 **근접 사례**로.
- 60/40 train/test 분할은 skill-creator의 `split_eval_set(seed=42)`를 그대로 쓴다.

## evals/trigger-intask.json (수행 중 G1, 선택)

```json
{
  "reason": "요청 문장에 발동 조건이 없다는 근거. 측정 전에 적는다",
  "items": [
    {"query": "fixture 저장소에서 실제로 수행할 과제", "should_trigger": true, "fixture": "evals/fixtures/<이름>"}
  ]
}
```

- 있으면 판정은 이것으로 한다(원칙 §2 "G1 측정 시점"). 문항 수·분할·판정 기준은 `trigger.json`과 같다.
- should-not도 같은 fixture에서 수행하는 근접 과제로(설명, 테스트 작성, 설정 변경, 형제 스킬의 일).
- run별 턴 수·시간·결과 종류가 `trigger/<model>.json`의 `detail`에 남는다. 발동하면 그 자리에서 끝나므로 발동 run은 턴 수가 작다.

## 결과 디렉터리

```
evals/results/<날짜>/
├── trigger/<model>.json, summary.json     # 수행 중 G1이 있으면 그것
├── trigger-router/                          # 수행 중 G1일 때 시작 시점 참고치
├── quality/configs.json                      # 조건 이름 → 구성요소 (기준선 = [])
├── quality/<eval>/<model>/<조건>/rep-<k>/     # 조건: with_skill, without_skill, 또는 --configs의 이름(hook, both …)
│   ├── run.json        # 토큰·시간·호출 여부·최종 응답
│   ├── transcript.md   # grader용 압축 트랜스크립트
│   ├── stream.jsonl    # 원본 이벤트
│   ├── outputs/        # 실행 후 프로젝트 사본
│   └── grading.json
├── report.md
└── summary.json
```
