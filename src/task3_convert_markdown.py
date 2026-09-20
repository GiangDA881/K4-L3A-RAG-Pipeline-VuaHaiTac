"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Giữ cấu trúc legal/ và news/. Chạy lại ghi đè file cùng stem, không nhân bản.
"""

from __future__ import annotations

import json
from pathlib import Path

from markitdown import MarkItDown

from .task1_collect_legal_docs import LEGAL_DOCUMENTS


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"
LEGAL_BY_FILENAME = {item["filename"]: item for item in LEGAL_DOCUMENTS}


def _write_markdown(path: Path, content: str) -> None:
    text = content.strip() + "\n"
    if len(text) < 200:
        raise RuntimeError(f"Standardized markdown too short: {path.name}")
    path.write_text(text, encoding="utf-8")


def convert_legal_docs() -> None:
    """Convert PDF/DOCX vào standardized/legal."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = MarkItDown()
    converted_names: list[str] = []
    for path in sorted(legal_dir.iterdir()):
        if path.name.startswith(".") or path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue
        result = converter.convert(str(path))
        body = (result.text_content or "").strip()
        meta = LEGAL_BY_FILENAME.get(path.name, {})
        title = meta.get("title") or path.stem
        source = meta.get("page_url") or meta.get("file_url") or path.name
        header = (
            f"# {title}\n\n"
            f"**Source:** {source}\n\n"
            f"**Landing:** `{path.name}`\n\n"
            "---\n\n"
        )
        _write_markdown(output_dir / f"{path.stem}.md", header + body)
        converted_names.append(f"{path.stem}.md")
        print(f"Legal: {path.name} -> {path.stem}.md")

    for stale in output_dir.glob("*.md"):
        if stale.name not in converted_names:
            stale.unlink()

    if len(converted_names) < 3:
        raise RuntimeError(f"Need at least 3 legal markdown files, got {len(converted_names)}")


def convert_news_articles() -> None:
    """Convert JSON vào standardized/news."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    converted_names: list[str] = []
    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        required = ("url", "title", "date_crawled", "content_markdown")
        missing = [key for key in required if not str(data.get(key, "")).strip()]
        if missing:
            raise RuntimeError(f"{path.name} missing {missing}")
        header = (
            f"# {data['title']}\n\n"
            f"**Source:** {data['url']}\n\n"
            f"**Crawled:** {data['date_crawled']}\n\n"
            f"**Landing:** `{path.name}`\n\n"
            "---\n\n"
        )
        _write_markdown(output_dir / f"{path.stem}.md", header + str(data["content_markdown"]))
        converted_names.append(f"{path.stem}.md")
        print(f"News: {path.name} -> {path.stem}.md")

    for stale in output_dir.glob("*.md"):
        if stale.name not in converted_names:
            stale.unlink()

    if len(converted_names) < 5:
        raise RuntimeError(f"Need at least 5 news markdown files, got {len(converted_names)}")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
