---
name: flaky-check
description: Measures whether a test or command fails intermittently by running it N times with a deterministic script that reports pass/fail counts, failure rate, distinct failure signatures, and timing in a few dozen lines. Use when the user says a test or step "fails sometimes", "is flaky", "passes locally but fails in CI", "fails randomly", or asks how often something fails or whether a failure is deterministic. Any named test, suite, script, or CI step the user can run again qualifies, even if they describe it loosely. Not for a test that fails every time (that's a plain bug), not for fixing the flake once the cause is known, and not for general questions about why tests can be flaky when there is nothing specific to run.
---

# flaky-check

"가끔 실패한다"는 보고는 한 번 돌려서는 판정할 수 없다. 한 번 통과하면 "재현 안 됨", 한 번 실패하면 "항상 실패"로 착각한다. 필요한 것은 **반복 실행의 실패율과 실패 종류**다. 그걸 손으로 for 루프 돌리고 출력을 눈으로 세면 토큰이 터지고 숫자가 틀린다. 스크립트가 세고, 모델은 요약만 읽는다.

## 사용

```bash
python3 <skill-dir>/scripts/flaky.py -n 20 -- python3 -m pytest tests/test_cache.py::test_cache_hit -q
python3 <skill-dir>/scripts/flaky.py -n 12 --timeout 60 -- bash scripts/fetch.sh
python3 <skill-dir>/scripts/flaky.py -n 20 --keep-logs .flaky-logs -- npm test -- -t "coupon"
```

- `-n`: 반복 횟수. 실패율이 10~30% 수준이면 20회가 최소다(10회에선 0회 실패도 흔하다). 시간이 길면 `-n 10`으로 시작해 실패가 보이면 늘린다.
- `--timeout`: 한 번 실행의 제한 시간. 걸리면 그 run은 `TIMEOUT` 시그니처로 센다.
- `--keep-logs DIR`: **실패한** run의 stdout/stderr만 남긴다. 시그니처만으로 원인이 모자랄 때 출력 마지막 줄이 가리키는 파일 **하나만** 읽는다. 디렉터리를 `ls`하거나 전부 `cat`하면 요약으로 아낀 토큰을 그대로 되돌려준다.

출력은 30줄 안이다: 횟수·통과·실패·실패율(95% Wilson 구간), 시간 min/median/max, **시그니처별 묶음**(숫자·해시·경로 줄번호를 정규화해 같은 원인을 한 줄로), 처음 실패한 run 번호.

## 해석

- 실패 0/20: 이 환경에서는 재현 안 됨. CI와의 차이(병렬 실행, 타임존, 네트워크, 순서)를 의심하고 그 조건을 넣어 다시 돈다. "플레이키 아님"이라고 단정하지 않는다.
- 실패 20/20: 플레이키가 아니라 결정적 버그다. 그렇게 보고하고 수정은 버그 수정 절차로 넘긴다.
- 시그니처가 둘 이상: 원인이 둘 이상이다. 각각 따로 보고한다. 하나로 뭉개면 고친 뒤에도 남는다.
- 시그니처 한 줄로 보통 충분하다. 더 필요하면 `--keep-logs`가 가리킨 파일 하나를 `tail -30`으로 본다.

## 보고

사용자에게 숫자(n, 실패 수, 구간)와 시그니처별 원인 후보를 말한다. 수정 제안은 요청받았을 때만.
