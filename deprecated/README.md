# deprecated/

세 게이트를 통과하지 못해 폐기한 스킬. 규칙은 `docs/principles.md` §6.4. 마켓플레이스에 등록하지 않는다.

삭제하지 않고 evals·fixture·scripts를 보존한다. 부활하려면 실패 사유를 겨냥한 변경을 만든 뒤 `skills/`로 되돌려 세 게이트를 전부 다시 잰다.

| 스킬 | 폐기일 | 실패한 게이트 | 근거 | 부활 조건 |
|---|---|---|---|---|
| `test-digest` | 2026-10-23 | G2 (opus Δ+2.7% ≤ 노이즈 바닥 3.1%, 비용 절감 없음) | `docs/study/gate-eval-round-1.md` 5회 재측정 | 작은 모델 전용 등 기준선이 실제로 놓치는 상황을 assertion으로 보일 때 |
| `test-integrity-check` | 2026-10-24 | G2 sonnet (개정 G2: 순Δ +9.0%, 층화 순열 p=0.108 ≥ 0.05, 셀 회귀 0; 비용 절감 없음). haiku는 품질형(+38.0%, p=0.0001). G1·G3 통과 | `docs/study/gate-eval-round-2.md` ⑨ | sonnet 기준선이 실제로 테스트를 고치는 상황(더 강한 압박·더 큰 저장소 등)을 fixture로 보이고 두 모델에서 다시 잴 때. `scripts/test_diff_audit.py`는 verify-on-stop eval이 이 경로로 쓴다 |
| `verify-before-done` | 2026-10-23 (재폐기 2026-10-23) | G1. 1차 시작 시점: haiku held-out 11/14. 재측정 수행 중 G1(§2): haiku 재현율 0%, opus 50%. G2·G3는 두 번 다 통과 | `docs/study/gate-eval-round-2.md` ①·재측정 | 부활하지 않음: Stop 훅 플러그인 `plugins/verify-on-stop`으로 대체(2026-10-23, 세 게이트 통과) |
