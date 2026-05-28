#!/usr/bin/env python3
"""
Convert Substack export -> Astro content collection markdown.

Usage:
  python3 scripts/convert-substack.py <path-to-substack-export-dir>

Writes one .md per published post into src/content/memos/.
"""
import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify as md_convert

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "src" / "content" / "memos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Skip Substack stock posts that ship with every publication
SKIP_SLUGS = {
    "how-to-use-the-substack-editor",
    "coming-soon",
}

# Substack-specific CSS classes / data attributes we should strip from posts.
JUNK_SELECTORS = [
    'p.cta-caption',                          # "Thanks for reading..."
    'div.captioned-button-wrap',              # share button wrappers
    'p.button-wrapper',                       # comment / share buttons
    'div.subscription-widget-wrap',           # in-post subscribe widgets
    'div.subscription-widget',                # ditto
    'div.pencraft',                           # author bylines
    'div[data-component-name="SubscribeWithCaptionToDOM"]',
    'div[data-component-name="ButtonCreateButton"]',
    'div[data-component-name="CaptionedButtonToDOM"]',
]

# Phrases that, if they show up in a paragraph at the end of a post, mean it's a Substack CTA.
TRAILING_PHRASES = [
    "thanks for reading memos by tutu",
    "leave a comment",
    "subscribe to memos by tutu",
]


def slug_from_post_id(post_id: str) -> str:
    """post_id is 'NUMBER.slug-with-dashes' — return just the slug."""
    parts = post_id.split(".", 1)
    return parts[1] if len(parts) == 2 else post_id


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Strip the obvious junk
    for sel in JUNK_SELECTORS:
        for el in soup.select(sel):
            el.decompose()

    # Strip trailing CTA paragraphs by text content
    for p in list(soup.find_all(["p", "div"])):
        text = (p.get_text() or "").strip().lower()
        if any(phrase in text for phrase in TRAILING_PHRASES) and len(text) < 120:
            p.decompose()

    # Remove dangling empty paragraphs
    for p in list(soup.find_all("p")):
        if not p.get_text(strip=True) and not p.find(["img", "iframe"]):
            p.decompose()

    # Strip Substack class attributes — they don't mean anything in markdown
    for el in soup.find_all(True):
        if "class" in el.attrs:
            del el.attrs["class"]
        for attr in ("data-attrs", "data-component-name", "data-callout"):
            if attr in el.attrs:
                del el.attrs[attr]

    return str(soup)


def html_to_markdown(html: str) -> str:
    cleaned = clean_html(html)
    md = md_convert(
        cleaned,
        heading_style="ATX",
        bullets="-",
        strong_em_symbol="*",
        escape_asterisks=False,
        escape_underscores=False,
        wrap=False,
    )
    # Collapse runs of blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def first_paragraph(html: str, max_len: int = 160) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for p in soup.find_all(["p", "blockquote"]):
        text = p.get_text(strip=True)
        if text:
            if len(text) > max_len:
                text = text[: max_len - 1].rstrip() + "…"
            return text
    return ""


def yaml_escape(s: str) -> str:
    """Wrap in double quotes, escape inner double quotes + backslashes."""
    if s is None:
        return '""'
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def main(export_dir: str):
    export = Path(export_dir)
    posts_csv = export / "posts.csv"
    if not posts_csv.exists():
        sys.exit(f"posts.csv not found in {export}")

    written = 0
    skipped_drafts = 0
    skipped_stock = 0

    with posts_csv.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            post_id = row["post_id"]
            slug = slug_from_post_id(post_id)

            if slug in SKIP_SLUGS:
                skipped_stock += 1
                continue

            if row.get("is_published", "").lower() != "true":
                skipped_drafts += 1
                continue

            html_path = export / "posts" / f"{post_id}.html"
            if not html_path.exists():
                print(f"  ! missing HTML for {post_id}")
                continue

            html = html_path.read_text(encoding="utf-8")
            title = row.get("title", "").strip() or slug.replace("-", " ").title()
            subtitle = row.get("subtitle", "").strip()
            description = subtitle if subtitle else first_paragraph(html)

            pub_iso = row.get("post_date", "")
            try:
                pub = datetime.fromisoformat(pub_iso.replace("Z", "+00:00"))
                pub_date = pub.strftime("%Y-%m-%d")
            except Exception:
                pub_date = "2024-01-01"

            substack_url = f"https://tutuadetunmbi.substack.com/p/{slug}"
            body = html_to_markdown(html)

            frontmatter = (
                "---\n"
                f"title: {yaml_escape(title)}\n"
                f"description: {yaml_escape(description)}\n"
                f"pubDate: {pub_date}\n"
                f"substackUrl: {yaml_escape(substack_url)}\n"
                "---\n\n"
            )

            out_path = OUT_DIR / f"{slug}.md"
            out_path.write_text(frontmatter + body, encoding="utf-8")
            written += 1
            print(f"  + {slug}.md ({pub_date}) — {title[:60]}")

    print()
    print(f"Wrote {written} memos to {OUT_DIR}")
    print(f"Skipped {skipped_drafts} drafts and {skipped_stock} Substack stock posts")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: convert-substack.py <path-to-export-dir>")
    main(sys.argv[1])
