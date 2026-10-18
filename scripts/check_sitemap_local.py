#!/usr/bin/env python3
"""Validate local sitemap links, canonical URLs, and bilingual page files."""
from pathlib import Path
from urllib.parse import urlparse
import re
import json
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
    # Detect missing and duplicated search-result titles/descriptions.
    titles = re.findall(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    descriptions = re.findall(
        r'<meta\\s+name="description"\\s+content="([^"]+)"', html, flags=re.I
    )
    if len(titles) != 1 or not titles[0].strip():
        errors.append(f"Expected exactly one nonempty page title: {url}")
    if len(descriptions) != 1 or not descriptions[0].strip():
        errors.append(f"Expected exactly one nonempty meta description: {url}")
    if not re.search(r"<h1\\b[^>]*>.*?</h1>", html, flags=re.I | re.S):
        errors.append(f"Missing main H1 heading: {url}")
    # Validate every embedded JSON-LD block, not just page metadata.
    blocks = re.findall(r'<script[^>]*type="application/ld[+]json"[^>]*>(.*?)</script>', html, flags=re.I | re.S)
    for number, block in enumerate(blocks, 1):
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON-LD in {url} (block {number}): {exc.msg}")
    if route in ("/ar/", "/en/"):
        people = []
        for block in blocks:
            try:
                obj = json.loads(block)
                people.extend(obj if isinstance(obj, list) else [obj])
            except json.JSONDecodeError:
                pass
        if not any(isinstance(item, dict) and item.get("@type") == "Person"
                   and item.get("@id") == base + "/#person" for item in people):
            errors.append(f"Missing canonical Person schema: {url}")
    if route in ("/ar/about", "/en/about"):
        profiles = []
        for block in blocks:
            try:
                obj = json.loads(block)
                profiles.extend(obj if isinstance(obj, list) else [obj])
            except json.JSONDecodeError:
                pass
        if not any(isinstance(item, dict) and item.get("@type") == "ProfilePage"
                   and item.get("mainEntity", {}).get("@id") == base + "/#person"
                   for item in profiles):
            errors.append(f"Missing linked ProfilePage schema: {url}")
    # Reciprocal hreflang signals should match the bilingual sitemap pair.
    lang = route.split("/")[1]
    other_lang = "ar" if lang == "en" else "en"
    counterpart = base + "/" + other_lang + "/" + route.split("/", 2)[2]
    alternates = dict(re.findall(
        r'<link[^>]*rel="alternate"[^>]*hreflang="([^"]+)"[^>]*href="([^"]+)"',
        html, flags=re.I
    ))
    if alternates.get(lang) != url:
        errors.append(f"Missing or incorrect self hreflang: {url}")
    if alternates.get(other_lang) != counterpart:
        errors.append(f"Missing or incorrect {other_lang} hreflang: {url}")
    if not re.search(r'<html\s+[^>]*lang="' + lang + r'"', html):
        errors.append(f"Incorrect HTML language: {url}")
# Every indexed route should have an equivalent route in the other language.
url_set = set(urls)
for url in urls:
    if url.startswith(base + "/en/"):
        alternate = base + "/ar/" + url.split("/en/", 1)[1]
    elif url.startswith(base + "/ar/"):
        alternate = base + "/en/" + url.split("/ar/", 1)[1]
    else:
        continue
    if alternate not in url_set:
        errors.append(f"Missing alternate-language sitemap URL for {url}: {alternate}")

robots = root / "robots.txt"
if not robots.is_file():
    errors.append("Missing robots.txt")
elif "Sitemap: " + base + "/sitemap.xml" not in robots.read_text(encoding="utf-8"):
    errors.append("robots.txt does not reference the canonical sitemap")

for error in errors:
    print("FAIL", error, file=sys.stderr)
print(f"Checked {len(urls)} sitemap URLs; {len(errors)} errors")
sys.exit(1 if errors else 0)
