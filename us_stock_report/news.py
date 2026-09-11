"""미국 증시 관련 최신 뉴스 헤드라인을 공개 RSS 피드에서 수집한다.

LLM이 "왜 그렇게 움직였는지"를 근거 없이 지어내지 않도록, 실제 헤드라인을 함께
프롬프트에 제공하기 위한 용도다. 특정 피드가 실패해도 나머지 피드로 계속 진행한다.
"""
from __future__ import annotations

from typing import Any

import feedparser

FEEDS = [
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("CNBC Markets", "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("MarketWatch Top Stories", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
]


def fetch_headlines(max_per_feed: int = 8, max_total: int = 25) -> list[dict[str, Any]]:
    headlines: list[dict[str, Any]] = []
    for source, url in FEEDS:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:max_per_feed]:
                headlines.append(
                    {
                        "source": source,
                        "title": entry.get("title", "").strip(),
                        "published": entry.get("published", ""),
                    }
                )
        except Exception:  # noqa: BLE001 - 뉴스 피드 실패는 리포트를 막지 않는다
            continue
        if len(headlines) >= max_total:
            break
    return headlines[:max_total]


if __name__ == "__main__":
    import json
    import sys

    json.dump(fetch_headlines(), sys.stdout, ensure_ascii=False, indent=2)
