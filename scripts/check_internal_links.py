#!/usr/bin/env python3
"""Validate internal links in static HTML pages before deployment."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "node_modules", ".venv"}
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag in {"a", "link", "script", "img", "source"}:
            for key in ("href", "src", "srcset"):
                if a.get(key):
                    values = a[key].split(",") if key == "srcset" else [a[key]]
                    for value in values:
                        self.links.append((key, value.strip().split()[0]))

def main():
    pages = [p for p in ROOT.rglob("*.html") if not any(x in SKIP for x in p.relative_to(ROOT).parts)]
    parsers = {}
    for page in pages:
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        parsers[page.resolve()] = parser
    errors = []
    checked = 0
    for page, parser in parsers.items():
        for key, url in parser.links:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or url.startswith(("mailto:", "tel:", "data:", "//")):
                continue
            path = unquote(parsed.path)
            if not path and not parsed.fragment:
                continue
            if path.startswith("/"):
                target = ROOT / path.lstrip("/")
            else:
                target = page.parent / path if path else page
            if path.endswith("/") or target.is_dir():
                target = target / "index.html"
            elif not target.exists() and not target.suffix:
                if target.with_suffix(".html").exists():
                    target = target.with_suffix(".html")
                elif (target / "index.html").exists():
                    target = target / "index.html"
            target = target.resolve()
            checked += 1
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                errors.append(f"{page.relative_to(ROOT)}: missing {key}={url}")
            elif parsed.fragment and target.suffix == ".html" and target in parsers and parsed.fragment not in parsers[target].ids:
                errors.append(f"{page.relative_to(ROOT)}: missing anchor {url}")
    print(f"Checked {checked} local links across {len(pages)} HTML pages.")
    for error in errors:
        print("ERROR:", error)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
