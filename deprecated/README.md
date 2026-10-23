# deprecated/

세 게이트를 통과하지 못해 폐기한 스킬. 규칙은 `docs/principles.md` §6.4. 마켓플레이스에 등록하지 않는다.

삭제하지 않고 evals·fixture·scripts를 보존한다. 부활하려면 실패 사유를 겨냥한 변경을 만든 뒤 `skills/`로 되돌려 세 게이트를 전부 다시 잰다.

| 스킬 | 폐기일 | 실패한 게이트 | 근거 | 부활 조건 |
|---|---|---|---|---|
| `test-digest` | 2026-10-23 | G2 (opus Δ+2.7% ≤ 노이즈 바닥 3.1%, 비용 절감 없음) | `docs/study/gate-eval-round-1.md` 5회 재측정 | 작은 모델 전용 등 기준선이 실제로 놓치는 상황을 assertion으로 보일 때 |
| `verify-before-done` | 2026-10-23 | G1 (haiku held-out 11/14, 평범한 변경 요청에 미발동). G2·G3는 통과, opus·sonnet은 세 게이트 통과 | `docs/study/gate-eval-round-2.md` ① | haiku 미발동 해소, 또는 끝-시점 스킬의 G1 측정법이 원칙에서 바뀔 때 |
