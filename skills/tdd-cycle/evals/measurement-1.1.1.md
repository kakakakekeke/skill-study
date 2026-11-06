# tdd-cycle 1.1.1 결함 수정 측정 설계 (측정 전 기록, 2026-11-06)

1.1.1은 이득을 주장하지 않는다. `docs/study/gate-eval-round-3.md` ⑥·⑦에서 찾은 결함 둘을 고친다. 그래서 판정은 **회귀 없음**이다(사용자 결정, 2026-11-06).

## 변경

1. `tdd_state.is_missing`: 내장 타입 값의 속성 오류(`'NoneType' object has no attribute 'strip'` 등)를 import·이름 누락이 아니라 동작 실패로 분류한다. 1.1.0은 이를 "RED (잘못된 이유)"로 보고 스텁만 허용해, 필요한 한 줄 수정을 막았다(⑦: sonnet 1 run 구현 중단, 168 run 중 35에 등장). 모듈·클래스·사용자 객체의 속성 누락은 그대로 누락이다. 검사기(`tdd_trace.MISSING`)도 같은 규칙으로 맞춘다.
2. 상태 `unknown`: 명령 위치의 pytest 실행인데 출력을 읽지 못하면(파이프·리다이렉트로 잘림) 다음 실행까지 소스 수정을 막는다. 1.1.0은 앞의 RED가 남아 수정이 계속 허용됐다(⑤ 빈틈). `no tests ran`·인자 자리의 pytest·heredoc 안 `import pytest`는 실행으로 보지 않는다.

SKILL.md에 "pytest 출력을 자르지 않는다" 한 문장. description 불변. 단위 테스트 35개(`scripts/tests/`).

## 조건·판정

- `prev` = 1.1.0 스킬+훅(⑥의 run 42개 재사용, 같은 날·CLI 2.1.318), `both` = 1.1.1. 케이스 7개·두 모델·3회.
- **판정(모델마다)**: 셀 회귀 0 **그리고** 순Δ ≥ −5%p **그리고** 품질 저하 쪽 순열 p↓ ≥ 0.05. 비용 감소 요건은 두지 않는다(이득 주장이 아니므로). 결과 assertion(`accept`·`suite_green`·`coverage`)이 `prev` 이상이어야 한다.
- 결함 수정이 작동했는지: `both`에서 `'NoneType' object has no attribute`가 "RED (잘못된 이유)"로 찍힌 횟수 0, 훅에 막혀 구현을 중단한 run 0. unknown은 fixture에서 드물어(⑥ 21 run 중 1) 발동 수만 보고한다.
- `red_behavior`는 검사기 규칙 변경(내장 타입 속성 오류 = 동작)으로 두 조건 모두 조금 오를 수 있다. 같은 검사기로 둘 다 다시 채점한다.
