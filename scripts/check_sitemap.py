#!/usr/bin/env python3
"""Validate XML sitemap URLs against deployed static HTML source files."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree as ET
import sys

ROOT = Path(__file__).resolve().parents[1]
HOST = "aymanesam.com"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

def main():
    errors = []
    try:
        tree = ET.parse(ROOT / "sitemap.xml")
    except (ET.ParseError, OSError) as exc:
        print(f"ERROR: cannot read sitemap: {exc}")
        return 1
    root = tree.getroot()
    urls = [node.text.strip() for node in root.findall(".//s:url/s:loc", NS) if node.text]
    if not urls:
        errors.append("No sitemap URLs found")
    seen = set()
    for url in urls:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != HOST:
            errors.append(f"Unexpected sitemap domain or protocol: {url}")
            continue
        if url in seen:
            errors.append(f"Duplicate sitemap URL: {url}")
        seen.add(url)
        if parsed.query or parsed.fragment:
            errors.append(f"Sitemap URL has query or fragment: {url}")
        path = unquote(parsed.path).lstrip("/")
        target = ROOT / path
        if not path or parsed.path.endswith("/"):
            target = target / "index.html"
        elif not target.is_file():
            target = target.with_suffix(".html")
        if not target.resolve().is_relative_to(ROOT.resolve()) or not target.is_file():
            errors.append(f"Missing sitemap target: {url}")
    for lang in ("en", "ar"):
        if f"https://{HOST}/{lang}/" not in seen:
            errors.append(f"Missing {lang} homepage in sitemap")
    print(f"Checked {len(urls)} sitemap URLs.")
    for error in errors:
        print("ERROR:", error)
    return int(bool(errors))

if __name__ == "__main__":
    sys.exit(main())
