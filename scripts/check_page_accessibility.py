#!/usr/bin/env python3
"""Catch basic bilingual accessibility and mobile metadata regressions."""
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.html = {}
        self.viewport = False
        self.title = False
        self.h1 = 0
        self.images_without_alt = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html = a
        if tag == "meta" and a.get("name", "").lower() == "viewport":
            self.viewport = bool(a.get("content"))
        if tag == "title":
            self.title = True
        if tag == "h1":
            self.h1 += 1
        if tag == "img" and "alt" not in a:
            self.images_without_alt += 1

def main():
    errors = []
    count = 0
    for lang, direction in (("en", "ltr"), ("ar", "rtl")):
        for path in sorted((ROOT / lang).rglob("*.html")):
            count += 1
            page = Page()
            page.feed(path.read_text(encoding="utf-8"))
            problems = []
            if page.html.get("lang") != lang:
                problems.append(f"html lang must be {lang}")
            if page.html.get("dir") != direction:
                problems.append(f"html dir must be {direction}")
            if not page.viewport:
                problems.append("missing viewport metadata")
            if not page.title:
                problems.append("missing title")
            if page.h1 != 1:
                problems.append(f"expected exactly one h1, found {page.h1}")
            if page.images_without_alt:
                problems.append(f"{page.images_without_alt} image(s) without alt attribute")
            for problem in problems:
                errors.append(f"{path.relative_to(ROOT)}: {problem}")
    print(f"Checked {count} Arabic and English pages for basic accessibility and mobile metadata.")
    for error in errors:
        print("ERROR:", error)
    return int(bool(errors))

if __name__ == "__main__":
    sys.exit(main())
