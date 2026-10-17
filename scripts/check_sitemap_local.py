#!/usr/bin/env python3
"""Validate local sitemap links, canonical URLs, and bilingual page files."""
from pathlib import Path
from urllib.parse import urlparse
import re
import sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
base = "https://aymanesam.com"
tree = ET.parse(root / "sitemap.xml")
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
urls = [n.text or "" for n in tree.findall(".//s:url/s:loc", ns)]
errors = []
if not urls:
    errors.append("Sitemap has no URLs")
if len(urls) != len(set(urls)):
    errors.append("Sitemap contains duplicate URLs")
for url in urls:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "aymanesam.com":
        errors.append(f"Invalid sitemap host: {url}")
        continue
    route = parsed.path
    if not (route.startswith("/en/") or route.startswith("/ar/")):
        errors.append(f"Unexpected language route: {url}")
        continue
    file = root / route.lstrip("/") / "index.html" if route.endswith("/") else root / (route.lstrip("/") + ".html")
    if not file.is_file():
        errors.append(f"Missing file for {url}: {file.relative_to(root)}")
        continue
    html = file.read_text(encoding="utf-8")
    match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)
    if not match or match.group(1) != url:
        errors.append(f"Canonical mismatch: {url}")
    lang = route.split("/")[1]
    if not re.search(r'<html\s+[^>]*lang="' + lang + r'"', html):
        errors.append(f"Incorrect HTML language: {url}")
for error in errors:
    print("FAIL", error, file=sys.stderr)
print(f"Checked {len(urls)} sitemap URLs; {len(errors)} errors")
sys.exit(1 if errors else 0)
