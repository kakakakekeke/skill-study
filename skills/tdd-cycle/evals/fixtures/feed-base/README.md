# feedparse

뉴스 사이트 RSS 2.0 피드를 읽어 기사 목록으로 바꾸는 작은 라이브러리. 표준 라이브러리만 쓴다.

## 인터페이스

- 패키지: `feedparse/` (`from feedparse import parse_feed, Item, FeedError`)
- `parse_feed(xml: str) -> list[Item]`
- `Item`: `title: str`, `link: str`, `summary: str`, `published: datetime | None`
- `FeedError(Exception)`

## 명세

1. `<channel>` 안의 `<item>`마다 `Item` 하나를 피드에 나온 순서대로 돌려준다.
2. `title`·`link`는 앞뒤 공백을 지운 값이다.
3. `link`가 없거나 비어 있는 item은 건너뛴다.
4. 같은 `link`가 두 번 이상 나오면 처음 것만 남긴다.
5. `summary`는 `<description>`의 HTML을 평문으로 바꾼 것이다.
   - 태그는 지우되 그 자리에 공백을 넣지 않는다. `OpenAI가 <b>새 모델</b>을 공개했다.` → `OpenAI가 새 모델을 공개했다.`
   - `<br>`, `<br/>`, `<br />`는 공백 하나가 된다.
   - HTML 엔티티를 푼다(`&amp;` → `&`, `&quot;` → `"`).
   - 연속 공백·줄바꿈은 공백 하나로 합치고 앞뒤 공백을 지운다.
   - `<description>`이 없으면 빈 문자열.
6. `published`는 `<pubDate>`(RFC 822)를 시간대가 있는 `datetime`으로 바꾼 것이다.
   - 시간대가 적혀 있으면 그 시각을 Asia/Seoul로 변환한다.
   - 시간대가 없으면(`Sat, 24 Oct 2026 20:38:00`) 서울 시각으로 해석한다.
   - `<pubDate>`가 없거나 해석할 수 없으면 `None`.
7. 입력이 RSS가 아니면(XML이 아니거나 루트가 `<rss>`가 아님, 예: 차단 안내 HTML 페이지) `FeedError`를 낸다. 빈 목록을 돌려주지 않는다.
8. `<rss>`이지만 item이 하나도 없으면 빈 목록이다.

## 개발

```bash
python3 -m pytest -q
```
