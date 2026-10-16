#!/usr/bin/env python3
"""Verify live bilingual pages and basic SEO endpoints. Uses only Python stdlib."""
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import sys
import time

BASE = "https://aymanesam.com"
CASES = [
    ("/en/", 'lang="en"', "text/html"),
    ("/ar/", 'lang="ar"', "text/html"),
    ("/en/contact", 'rel="canonical"', "text/html"),
    ("/ar/contact", 'rel="canonical"', "text/html"),
    ("/robots.txt", "Sitemap:", "text/plain"),
    ("/sitemap.xml", "<urlset", "xml"),
]
errors = []
for path, marker, content_type in CASES:
    url = BASE + path
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": "AymanSiteReleaseAudit/1.0"})
            with urlopen(req, timeout=20) as response:
                status = response.status
                actual_url = response.url
                mime = response.headers.get("Content-Type", "")
                body = response.read(1_500_000).decode("utf-8", "replace")
            if status != 200 or marker not in body or content_type not in mime:
                raise ValueError(f"status={status} mime={mime!r} marker_found={marker in body}")
            print(f"PASS {path} -> {actual_url} [{status}; {mime}]")
            break
        except (HTTPError, URLError, ValueError, TimeoutError) as exc:
            if attempt == 2:
                errors.append(f"{path}: {exc}")
            else:
                time.sleep(5)
if errors:
    for error in errors:
        print("FAIL", error, file=sys.stderr)
    sys.exit(1)
print("Live production smoke checks passed.")
