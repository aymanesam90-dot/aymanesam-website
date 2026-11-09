#!/usr/bin/env python3
"""Check local HTML links, asset references, fragment targets and sitemap URLs.

Run from repository root: python3 scripts/check_site_integrity.py
This is a source audit, not a deployed-URL or browser test.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = "aymanesam.com"
SKIP = {"mailto", "tel", "javascript", "data"}
EXCLUDED = {"admin"}

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        for key in ("href", "src", "poster"):
            if a.get(key):
                self.refs.append((key, a[key]))
        if a.get("srcset"):
            for candidate in a["srcset"].split(","):
                self.refs.append(("srcset", candidate.strip().split()[0]))

def resolve(path):
    if path.is_file():
        return path
    if path.is_dir() and (path / "index.html").is_file():
        return path / "index.html"
    if not path.suffix and path.with_suffix(".html").is_file():
        return path.with_suffix(".html")
    return None

def main():
    pages = sorted(p for p in ROOT.rglob("*.html") if not any(x in EXCLUDED for x in p.relative_to(ROOT).parts))
    parsed = {p: PageParser() for p in pages}
    for p, parser in parsed.items():
        parser.feed(p.read_text(encoding="utf-8"))
    errors = []
    count = 0
    for page, parser in parsed.items():
        for key, ref in parser.refs:
            if ref.startswith("//"):
                continue
            url = urlsplit(ref)
            if url.scheme in SKIP or (url.scheme and url.scheme not in ("http", "https")):
                continue
            if url.netloc and url.netloc.lower() not in (SITE, "www." + SITE):
                continue
            if url.scheme and url.scheme != "https":
                errors.append(f"{page.relative_to(ROOT)}: insecure local URL {ref}")
            if not url.path and not url.fragment:
                continue
            raw = unquote(url.path)
            target = (ROOT / raw.lstrip("/")) if raw.startswith("/") else (page.parent / raw)
            target = resolve(target.resolve()) if raw else page
            count += 1
            if target is None or not target.is_relative_to(ROOT):
                errors.append(f"{page.relative_to(ROOT)}: missing local target {ref}")
            elif url.fragment and target.suffix == ".html":
                target_parser = parsed.get(target)
                if target_parser is None:
                    target_parser = PageParser()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                if unquote(url.fragment) not in target_parser.ids:
                    errors.append(f"{page.relative_to(ROOT)}: missing fragment {ref}")
    tree = ET.parse(ROOT / "sitemap.xml")
    locs = [e.text for e in tree.iter() if e.tag.endswith("}loc") or e.tag == "loc"]
    for url in locs:
        parsed_url = urlsplit(url)
        if parsed_url.scheme != "https" or parsed_url.netloc != SITE:
            errors.append(f"sitemap: unexpected URL {url}")
            continue
        target = resolve(ROOT / unquote(parsed_url.path).lstrip("/"))
        if target is None:
            errors.append(f"sitemap: missing target {url}")
    if len(locs) != len(set(locs)):
        errors.append("sitemap: duplicate loc URLs")
    for error in errors:
        print("FAIL", error)
    print(f"Checked {len(pages)} HTML pages, {count} local references and {len(locs)} sitemap URLs; {len(errors)} issues.")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
