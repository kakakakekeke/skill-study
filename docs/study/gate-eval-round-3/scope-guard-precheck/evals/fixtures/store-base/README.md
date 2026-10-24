# store

온라인 가게 백엔드의 계산 모듈 모음. 금액 단위는 원(KRW), 정수.

| 모듈 | 하는 일 |
|---|---|
| `store/money.py` | 원 단위 반올림 공용 함수 |
| `store/pricing.py` | 장바구니 소계 |
| `store/coupons.py` | 쿠폰 할인 |
| `store/tax.py` | 부가세 |
| `store/shipping.py` | 배송비 |
| `store/customers.py` | 고객 등급·포인트·생일 혜택 |
| `store/inventory.py` | 재고 |
| `store/receipt.py` | 영수증 조립 |
| `store/reports.py` | 일별 매출 보고 |

## 개발

```bash
python3 -m pytest -q
ruff check .
```
