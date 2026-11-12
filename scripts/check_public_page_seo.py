#!/usr/bin/env python3
"""Check canonical, title, description and language on public bilingual HTML pages."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://aymanesam.com"
class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.html = {}
        self.links = []
        self.meta = []
        self.title = ""
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html": self.html = a
        elif tag == "link": self.links.append(a)
        elif tag == "meta": self.meta.append(a)
        elif tag == "title": self.in_title = True
    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.title += data

sitemap = ET.parse(ROOT / "sitemap.xml")
sitemap_urls = {node.text.strip() for node in sitemap.iter() if node.tag.endswith("}loc") and node.text}
robots_txt = (ROOT / "robots.txt").read_text(encoding="utf-8")
errors = []
if "Sitemap: https://aymanesam.com/sitemap.xml" not in robots_txt:
    errors.append("robots.txt: missing canonical sitemap declaration")
if "Disallow: /" in robots_txt.splitlines():
    errors.append("robots.txt: site-wide crawl disallow detected")
checked = 0
for lang in ("en", "ar"):
    for page in sorted((ROOT / lang).rglob("*.html")):
        parser = MetaParser()
        parser.feed(page.read_text(encoding="utf-8"))
        rel = page.relative_to(ROOT).as_posix()
        if page.name == "index.html" and page.parent == ROOT / lang:
            expected = f"{BASE}/{lang}/"
        else:
            expected = f"{BASE}/{rel}"
            if expected.endswith(".html") and expected[:-5] in sitemap_urls: expected = expected[:-5]
        canonicals = [x.get("href") for x in parser.links if x.get("rel") == "canonical"]
        if expected not in sitemap_urls:
            errors.append(f"{rel}: expected canonical absent from sitemap: {expected}")
        if len(canonicals) != 1 or canonicals[0] != expected:
            errors.append(f"{rel}: canonical {canonicals} expected {expected}")
        if parser.html.get("lang") != lang:
            errors.append(f"{rel}: wrong html lang")
        if not parser.title.strip():
            errors.append(f"{rel}: missing title")
        robots = [x.get("content", "").lower() for x in parser.meta if x.get("name", "").lower() == "robots"]
        if any("noindex" in value or "none" in value for value in robots):
            errors.append(f"{rel}: public page marked noindex")
        og = {x.get("property"): x.get("content", "") for x in parser.meta if x.get("property", "").startswith("og:")}
        for required in ("og:title", "og:description", "og:image", "og:url"):
            if not og.get(required):
                errors.append(f"{rel}: missing {required} social preview metadata")
        if og.get("og:url") and og["og:url"] != expected:
            errors.append(f"{rel}: og:url differs from canonical")
        if og.get("og:image"):
            image = urlsplit(og["og:image"])
            if image.scheme != "https" or image.netloc != "aymanesam.com":
                errors.append(f"{rel}: invalid og:image URL")
            elif not image.path or not (ROOT / unquote(image.path).lstrip("/")).is_file():
                errors.append(f"{rel}: missing social preview image file {image.path}")
        descriptions = [x.get("content", "") for x in parser.meta if x.get("name") == "description"]
        if len(descriptions) != 1 or not descriptions[0].strip():
            errors.append(f"{rel}: missing/duplicate meta description")
        for x in parser.links:
            if x.get("rel") == "alternate" and x.get("hreflang") in ("en", "ar", "x-default"):
                href = x.get("href", "")
                if urlsplit(href).scheme != "https" or urlsplit(href).netloc != "aymanesam.com":
                    errors.append(f"{rel}: invalid hreflang URL {href}")
        checked += 1
for error in errors: print("ERROR:", error)
print(f"Audited {checked} bilingual HTML pages; {len(errors)} SEO metadata issues")
raise SystemExit(bool(errors))
