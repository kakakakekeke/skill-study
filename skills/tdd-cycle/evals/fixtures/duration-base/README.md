# durations

설정 파일의 기간 문자열(`1h30m` 같은 것)을 초로 바꾸고, 초를 다시 문자열로 바꾸는 작은 라이브러리. 표준 라이브러리만 쓴다.

## 인터페이스

- 패키지: `durations/` (`from durations import parse_duration, format_duration`)
- `parse_duration(text: str) -> int` — 초
- `format_duration(seconds: int) -> str`

## 명세

### parse_duration

1. 단위는 `d`(86400초), `h`(3600), `m`(60), `s`(1). `1h30m` → 5400, `2d` → 172800.
2. 단위 없는 정수만 있으면 초다. `90` → 90.
3. 단위 사이 공백은 허용한다. 앞뒤 공백은 무시한다. `" 1h 30m "` → 5400.
4. 단위는 큰 것부터 한 번씩만 나온다. `30m1h`, `1h1h`는 `ValueError`.
5. 단위는 소문자만 받는다. `1H`는 `ValueError`.
6. 빈 문자열, 공백뿐인 문자열, 음수(`-5m`), 소수(`1.5h`), 숫자 없는 단위(`h`), 알 수 없는 단위(`1w`)는 `ValueError`.
7. 값이 0인 단위도 허용한다. `0s` → 0, `1h0m` → 3600.

### format_duration

8. 큰 단위부터 0이 아닌 단위만 이어 붙인다. 5400 → `1h30m`, 3600 → `1h`, 90061 → `1d1h1m1s`.
9. 0 → `0s`.
10. 음수는 `ValueError`.
11. `parse_duration(format_duration(n)) == n` (0 이상의 모든 정수 n).

## 개발

```bash
python3 -m pytest -q
```
