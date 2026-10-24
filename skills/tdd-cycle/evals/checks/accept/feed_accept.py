"""feed-base 명세 수용 테스트. 모델에게 보이지 않는다. 명세 번호를 테스트 이름에 붙인다."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from feedparse import FeedError, parse_feed

SEOUL = ZoneInfo("Asia/Seoul")


def rss(items: str) -> str:
    return f'<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>{items}</channel></rss>'


def item(title="제목", link="https://n.example/a", desc=None, pub=None) -> str:
    parts = [f"<title>{title}</title>"]
    if link is not None:
        parts.append(f"<link>{link}</link>")
    if desc is not None:
        parts.append(f"<description>{desc}</description>")
    if pub is not None:
        parts.append(f"<pubDate>{pub}</pubDate>")
    return "<item>" + "".join(parts) + "</item>"


def test_s1_order():
    out = parse_feed(rss(item("A", "https://n.example/1") + item("B", "https://n.example/2")))
    assert [i.title for i in out] == ["A", "B"]


def test_s2_strip():
    out = parse_feed(rss(item("  A  ", "  https://n.example/1 \n")))
    assert (out[0].title, out[0].link) == ("A", "https://n.example/1")


def test_s3_skip_missing_link():
    out = parse_feed(rss(item("A", None) + item("B", "  ") + item("C", "https://n.example/3")))
    assert [i.title for i in out] == ["C"]


def test_s4_dedupe_first():
    out = parse_feed(rss(item("A", "https://n.example/1") + item("B", "https://n.example/1")))
    assert [i.title for i in out] == ["A"]


def test_s5_inline_tag_no_space():
    desc = "OpenAI가 &lt;b&gt;새 모델&lt;/b&gt;을 공개했다."
    assert parse_feed(rss(item(desc=desc)))[0].summary == "OpenAI가 새 모델을 공개했다."


def test_s5_inline_tag_no_space_cdata():
    desc = "<![CDATA[OpenAI가 <b>새 모델</b>을 <a href='x'>공개</a>했다.]]>"
    assert parse_feed(rss(item(desc=desc)))[0].summary == "OpenAI가 새 모델을 공개했다."


def test_s5_br_is_space():
    desc = "<![CDATA[첫 줄<br>둘째 줄<br/>셋째<br />넷째]]>"
    assert parse_feed(rss(item(desc=desc)))[0].summary == "첫 줄 둘째 줄 셋째 넷째"


def test_s5_entities():
    desc = "<![CDATA[A &amp; B &quot;C&quot;]]>"
    assert parse_feed(rss(item(desc=desc)))[0].summary == 'A & B "C"'


def test_s5_whitespace_collapse():
    desc = "<![CDATA[  가\n\n  나   다  ]]>"
    assert parse_feed(rss(item(desc=desc)))[0].summary == "가 나 다"


def test_s5_missing_description():
    assert parse_feed(rss(item()))[0].summary == ""


def test_s6_tz_converted_to_seoul():
    p = parse_feed(rss(item(pub="Sat, 24 Oct 2026 11:38:00 +0000")))[0].published
    assert p == datetime(2026, 10, 24, 20, 38, tzinfo=SEOUL)
    assert p.utcoffset().total_seconds() == 9 * 3600


def test_s6_naive_is_seoul():
    p = parse_feed(rss(item(pub="Sat, 24 Oct 2026 20:38:00")))[0].published
    assert p is not None and p.utcoffset() is not None
    assert p == datetime(2026, 10, 24, 20, 38, tzinfo=SEOUL)


def test_s6_missing_or_bad():
    out = parse_feed(rss(item("A", "https://n.example/1") + item("B", "https://n.example/2", pub="어제")))
    assert [i.published for i in out] == [None, None]


def test_s7_html_page_raises():
    page = "<!DOCTYPE html><html><body><h1>Access Denied</h1></body></html>"
    with pytest.raises(FeedError):
        parse_feed(page)


def test_s7_not_xml_raises():
    with pytest.raises(FeedError):
        parse_feed("Too Many Requests")


def test_s7_wrong_root_raises():
    with pytest.raises(FeedError):
        parse_feed('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>')


def test_s8_empty_channel():
    assert parse_feed(rss("")) == []
