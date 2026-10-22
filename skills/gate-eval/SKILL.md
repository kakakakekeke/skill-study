---
name: gate-eval
description: Measures a skill in this repository against the three adoption gates (trigger accuracy, with/without quality with a noise floor, token cost) on haiku and opus with repeated runs, and writes a fixed-format report under the skill's evals/results/. Invoke as /gate-eval skills/<name>.
disable-model-invocation: true
---

# gate-eval

`/gate-eval skills/<name>`로 호출된다. 이 저장소의 규칙(`docs/principles.md` §2·§5)을 **측정 절차로 고정**한 것이다. 사람이 켜는 라우터이므로 description은 평소 컨텍스트에 로드되지 않는다.

## 왜 이 절차인가

단일 실행 비교는 노이즈를 효과로 착각한다. 그래서 기준선을 자기 자신과 반복 비교해 뒤집힘률(노이즈 바닥)을 먼저 재고, 그 아래의 "회귀"는 회귀로 치지 않는다. 이득과 회귀는 쌍으로 보고한다(한쪽만 보면 선별 편향). 모델 2종(haiku, opus)으로 돌리는 이유는 작은 모델에서 효과가 크고 큰 모델에서 사라지는 스킬이 흔하기 때문이다.

## 실행

전제: 대상 스킬에 `evals/evals.json`(품질 케이스)과, model-invoked 스킬이면 `evals/trigger.json`(should/should-not 약 20개)이 있어야 한다. 없으면 먼저 그것을 쓴다. 형식은 `references/evals-format.md`. 대상이 user-invoked 스킬이면 케이스마다 `prompt`(슬래시 호출문)와 `prompt_without`(스킬 없는 사용자가 칠 같은 뜻의 문장)을 둘 다 둔다.

스크립트는 이 스킬 디렉터리의 `scripts/gate_eval.py`다 (이 저장소에서는 `skills/gate-eval/scripts/gate_eval.py`).

```bash
python3 <skill-dir>/scripts/gate_eval.py --skill skills/<name>            # 기본: haiku,opus × 3회
python3 <skill-dir>/scripts/gate_eval.py --skill skills/<name> --reps 5   # 노이즈가 크면 반복 증가
python3 <skill-dir>/scripts/gate_eval.py --skill skills/<name> --skip-trigger --only 1,2
```

- 결과: `skills/<name>/evals/results/<날짜>/report.md`, `summary.json`. 단계별 캐시가 있어 중단 후 같은 명령으로 이어서 실행한다. 다시 재고 싶으면 그날 디렉터리를 지운다.
- 실행은 임시 프로젝트에서 `claude -p`로 하며, with 설정은 `.claude/skills/<name>` 심볼릭 링크만 추가된다. 사용자 스킬·플러그인은 품질 실행에서 제외된다(트리거 측정은 실제 환경과 경쟁하도록 포함).
- 오래 걸린다(케이스 3개 기준 30~60분). 백그라운드로 돌리고 stderr 로그를 본다.

## G1은 무엇을 재는가

빈 임시 프로젝트에 이 저장소의 model-invoked 스킬을 **전부** 링크해 서로 경쟁시키고, 쿼리마다 "코드는 없다. 쓸 스킬이 있으면 Skill 도구로 호출하고 없으면 NONE"이라는 시스템 프롬프트 한 줄로 **라우팅 결정만** 묻는다(쿼리당 3회, 임계 0.5). 실제 과제 수행 중의 호출과는 다르다. 수행 중 호출 여부는 G2 표의 "with 미호출" 열이 보여준다. skill-creator의 `run_eval`(description만 커맨드 파일로 노출, 첫 도구가 Skill이어야 함)은 CLI 2.1.295에서 호출을 감지하지 못해(2026-10-22 확인) 쓰지 않는다.

## 보고서 읽는 법

| 게이트 | 판정 규칙 (report.py에 고정) | 실패 시 |
|---|---|---|
| G1 | 모델마다 held-out test에서 과잉·미발동 각 1건 이하 | description을 고치고 **train만 보고** 다시. test를 보며 고치면 과적합 |
| G2 | 회귀율 ≤ 노이즈 바닥 **그리고** 순Δ > 0 **그리고** rep 짝 비교에서 with ≥ without 과반 | 회귀 사례를 하나씩 `grading.json` evidence·`transcript.md`로 정성 검토. assertion을 통과하게 고치는 것은 금지 |
| G3 | 본문 < 200줄, 토큰 비율 > 1.5인데 G2 이득 없음이면 실패(잠정) | 공식 측정은 세션에서 `/skill-doctor`. 비싸면 라우팅(user-invoked + references/) |

G2 표의 "with 미호출"은 삼투 조건이다. 스킬이 있는데 호출되지 않은 run이 통과율을 올렸다면 description 자체가 행동을 바꾼 것이니 따로 적는다.

## 결과 처리

- 세 게이트 모두 통과 → `docs/ideas.md` 상태를 "게이트 통과"로. 아니면 "보류(사유)".
- 스킬 유무와 무관하게 항상 통과하는 assertion은 비변별이다. 다음 라운드 전에 `evals.json`에서 지운다.
- 보고서의 날짜·CLI·모델 버전 줄은 지우지 않는다. 다음 측정과 비교하는 기준이다.
