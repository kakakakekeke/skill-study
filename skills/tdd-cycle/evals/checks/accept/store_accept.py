"""store-base 명세 수용 테스트. 모델에게 보이지 않는다."""
from datetime import datetime

import pytest

from articlestore import Article, ArticleStore

T0 = datetime(2026, 10, 24, 9, 0)
T1 = datetime(2026, 10, 24, 10, 0)


def art(url="https://news.example/a/1", title="제목", body="본문", at=T0):
    return Article(url=url, title=title, body=body, fetched_at=at)


def test_s1_new():
    s = ArticleStore()
    assert s.upsert(art()) == "new"
    assert len(s) == 1


@pytest.mark.parametrize("variant", [
    "HTTPS://News.Example/a/1",
    "https://news.example/a/1?utm_source=rss&utm_medium=x",
    "https://news.example/a/1#comments",
    "https://news.example/a/1/",
])
def test_s2_same_key(variant):
    s = ArticleStore()
    s.upsert(art())
    assert s.upsert(art(url=variant)) == "unchanged"
    assert len(s) == 1


def test_s2_path_case_kept():
    s = ArticleStore()
    s.upsert(art(url="https://news.example/A/1"))
    assert s.upsert(art(url="https://news.example/a/1")) == "new"


def test_s2_other_params_kept_in_order():
    s = ArticleStore()
    s.upsert(art(url="https://news.example/v?id=3&utm_source=x&p=2"))
    assert s.get("https://news.example/v?id=3&p=2") is not None
    assert s.get("https://news.example/v?p=2&id=3") is None


def test_s2_root_slash_kept():
    s = ArticleStore()
    s.upsert(art(url="https://news.example/"))
    assert s.get("https://news.example/") is not None


def test_s3_updated():
    s = ArticleStore()
    s.upsert(art())
    assert s.upsert(art(body="고친 본문", at=T1)) == "updated"
    assert s.get("https://news.example/a/1").body == "고친 본문"


def test_s4_whitespace_only_change():
    s = ArticleStore()
    s.upsert(art())
    assert s.upsert(art(title="  제목 ", body="본문\n")) == "unchanged"


def test_s5_fetched_at_only():
    s = ArticleStore()
    s.upsert(art(at=T0))
    assert s.upsert(art(at=T1)) == "unchanged"
    assert s.get("https://news.example/a/1").fetched_at == T0


def test_s6_get_raw_url_and_missing():
    s = ArticleStore()
    s.upsert(art())
    assert s.get("https://NEWS.example/a/1/?utm_campaign=z#top").title == "제목"
    assert s.get("https://news.example/none") is None


@pytest.mark.parametrize("title", ["", "   "])
def test_s7_empty_title(title):
    s = ArticleStore()
    with pytest.raises(ValueError):
        s.upsert(art(title=title))
    assert len(s) == 0
