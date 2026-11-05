# money

금액 표시·세금·분할 계산용 작은 패키지. 표준 라이브러리만 쓴다. 반올림은 전부 `ROUND_HALF_UP`이다.

- `money.format_money(amount, currency="KRW") -> str` — KRW는 정수로 반올림해 `1,235원`, USD는 소수 둘째 자리로 `$1,234.57`
- `money.apply_tax(amount, rate=0.1) -> float` — 세후 금액, 소수 둘째 자리
- `money.split_bill(total, n) -> list[float]` — n등분, 소수 둘째 자리. 나머지는 첫 사람에게 얹어 합이 `total`과 같게 한다

```bash
python3 -m pytest -q
```
