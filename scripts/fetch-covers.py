#!/usr/bin/env python3
"""
Fetch each memo's cover image from its Substack URL and write it into the
markdown frontmatter as `cover: "https://..."`.

Usage:
  python3 scripts/fetch-covers.py
"""
import re
import sys
import time
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from bs4 import BeautifulSoup

REPO = Path(__file__).resolve().parent.parent
MEMOS_DIR = REPO / "src" / "content" / "memos"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def parse_frontmatter(text: str):
    """Return (frontmatter_dict_simple, raw_frontmatter_block, body)."""
    if not text.startswith("---\n"):
        return None, None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, None, text
    block = text[4:end]
    body = text[end + 5 :]
    fm = {}
    for line in block.splitlines():
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            fm[key] = val
    return fm, block, body


def fetch_og_image(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        # Substack uses og:image
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]
        # Fallback: twitter:image
        tw = soup.find("meta", attrs={"name": "twitter:image"})
        if tw and tw.get("content"):
            return tw["content"]
    except Exception as e:
        print(f"  ! fetch error for {url}: {e}")
    return None


def update_frontmatter_with_cover(text: str, cover_url: str, alt: str) -> str:
    """Insert cover: and coverAlt: into frontmatter, replacing if already present."""
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    block = text[4:end]
    body = text[end + 5 :]

    lines = block.splitlines()
    # Remove any existing cover / coverAlt lines
    lines = [l for l in lines if not l.startswith("cover:") and not l.startswith("coverAlt:")]
    # Append the new ones
    lines.append(f'cover: "{cover_url}"')
    lines.append(f'coverAlt: "{alt}"')
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def process_one(path: Path) -> tuple[str, bool, str]:
    text = path.read_text(encoding="utf-8")
    fm, _, _ = parse_frontmatter(text)
    if not fm or "substackUrl" not in fm:
        return path.name, False, "no substackUrl"
    if "cover" in fm and fm.get("cover"):
        return path.name, False, "already has cover"

    cover = fetch_og_image(fm["substackUrl"])
    if not cover:
        return path.name, False, "no og:image found"

    title = fm.get("title", "").strip('"\\"')
    new_text = update_frontmatter_with_cover(text, cover, title)
    path.write_text(new_text, encoding="utf-8")
    return path.name, True, cover


def main():
    files = sorted(MEMOS_DIR.glob("*.md"))
    print(f"Found {len(files)} memos.")
    print()

    updated = 0
    skipped = 0
    failed = 0

    # 8 threads — Substack handles parallel requests fine
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(process_one, p): p for p in files}
        for fut in as_completed(futures):
            name, ok, info = fut.result()
            if ok:
                updated += 1
                print(f"  + {name} → {info[:70]}")
            elif info == "already has cover":
                skipped += 1
            else:
                failed += 1
                print(f"  ✗ {name} ({info})")

    print()
    print(f"Updated: {updated}   Skipped: {skipped}   Failed: {failed}")


if __name__ == "__main__":
    main()
