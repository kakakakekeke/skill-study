# articlestore

크롤러가 가져온 기사를 메모리에 저장하고, 새 글·갱신 글을 구분해 주는 작은 저장소. 표준 라이브러리만 쓴다.

## 인터페이스

- 패키지: `articlestore/` (`from articlestore import Article, ArticleStore`)
- `Article`: `url: str`, `title: str`, `body: str`, `fetched_at: datetime` (dataclass)
- `ArticleStore()`
  - `upsert(article: Article) -> str` — `"new"`, `"updated"`, `"unchanged"` 중 하나
  - `get(url: str) -> Article | None`
  - `__len__()` — 저장된 기사 수

## 명세

1. 처음 보는 기사는 저장하고 `"new"`를 돌려준다.
2. 기사의 키는 **정규화한 URL**이다. 정규화 규칙:
   - scheme과 host는 소문자로 바꾼다. 경로는 대소문자를 그대로 둔다.
   - 쿼리에서 `utm_`으로 시작하는 파라미터를 지운다. 나머지 파라미터는 순서를 유지한다. 남은 파라미터가 없으면 `?`도 지운다.
   - `#` 뒤 프래그먼트를 지운다.
   - 경로 끝의 `/` 하나를 지운다. 단, 경로가 `/` 하나뿐이면 그대로 둔다.
3. 같은 키의 기사가 이미 있고 `title` 또는 `body`가 다르면 새 내용으로 바꾸고 `"updated"`를 돌려준다.
4. `title`·`body` 비교는 앞뒤 공백을 지운 값으로 한다. 공백만 다르면 바뀐 것이 아니다.
5. `title`과 `body`가 같으면 `fetched_at`이 달라도 `"unchanged"`이고, 저장된 기사는 바꾸지 않는다.
6. `get`은 정규화 전 URL로 물어도 찾는다. 없으면 `None`.
7. `title`이 비어 있거나 공백뿐이면 `ValueError`를 내고 저장하지 않는다.

## 개발

```bash
python3 -m pytest -q
```
