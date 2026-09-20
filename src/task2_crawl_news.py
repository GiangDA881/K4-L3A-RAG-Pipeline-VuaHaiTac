"""
Task 2 — Crawl bài viết/thông báo về Du lịch Việt Nam.

Nguồn: trang chính thức vietnam.travel (lịch trình, địa điểm, ẩm thực, visa).
Mỗi lần chạy ghi đè article_01.json… theo đúng thứ tự ARTICLE_URLS.
"""

from __future__ import annotations

import asyncio
import json
import re
import tempfile
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

ARTICLE_URLS = [
    "https://vietnam.travel/plan-your-trip/visa-requirements",
    "https://vietnam.travel/plan-your-trip/official-vietnam-evisa-application",
    "https://www.vietnam.travel/node/156",
    "https://vietnam.travel/things-to-do",
    "https://vietnam.travel/things-to-do/food",
    "https://vietnam.travel/plan-your-trip",
]


def _title_from_html(html: str, fallback: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return fallback
    title = unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return title or fallback


def _clean_markdown(markdown: str) -> str:
    lines = []
    for line in markdown.splitlines():
        if "javascript:void" in line:
            continue
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _markdown_from_html(html: str, url: str) -> tuple[str, str]:
    from markitdown import MarkItDown

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as handle:
        handle.write(html.encode("utf-8"))
        temp_path = Path(handle.name)
    try:
        converted = MarkItDown().convert(str(temp_path))
        markdown = (converted.text_content or "").strip()
    finally:
        temp_path.unlink(missing_ok=True)
    return _title_from_html(html, url), markdown


def _fetch_with_requests(url: str) -> tuple[str, str]:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en,vi;q=0.8"},
        timeout=45,
    )
    response.raise_for_status()
    html = response.text
    title, markdown = _markdown_from_html(html, url)
    if len(markdown) < 200:
        raise RuntimeError(f"Extracted markdown too short for {url}")
    return title, markdown


async def crawl_article(url: str) -> dict:
    """Crawl một URL công khai, fallback sang requests + MarkItDown nếu bị chặn."""
    title = ""
    markdown = ""
    try:
        from crawl4ai import AsyncWebCrawler

        async with AsyncWebCrawler() as crawler:
            result = await asyncio.wait_for(crawler.arun(url=url), timeout=45)
        markdown = str(getattr(result, "markdown", "") or "").strip()
        metadata = getattr(result, "metadata", None) or {}
        title = str(metadata.get("title") or "").strip()
    except Exception:
        markdown = ""

    if len(markdown) < 200:
        title, markdown = await asyncio.to_thread(_fetch_with_requests, url)

    markdown = _clean_markdown(markdown)
    if len(markdown) < 200:
        raise RuntimeError(f"Extracted markdown too short for {url}")

    return {
        "url": url,
        "title": title or url,
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": markdown,
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON, ghi đè theo index."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if len(ARTICLE_URLS) < 5:
        raise RuntimeError("ARTICLE_URLS must contain at least 5 public URLs")

    for stale in DATA_DIR.glob("article_*.json"):
        stale.unlink()

    saved = 0
    for index, url in enumerate(ARTICLE_URLS, 1):
        article = await crawl_article(url)
        output = DATA_DIR / f"article_{index:02d}.json"
        output.write_text(
            json.dumps(article, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        saved += 1
        print(f"Saved: {output} — {article['title']}")

    if saved < 5:
        raise RuntimeError(f"Need at least 5 articles, saved {saved}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
