#!/usr/bin/env python3
"""Verify live bilingual pages and basic SEO endpoints. Uses only Python stdlib."""
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import sys
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET

BASE = "https://aymanesam.com"
CASES = [
    ("/en/", 'lang="en"', "text/html"),
    ("/ar/", 'lang="ar"', "text/html"),
    ("/", "https://aymanesam.com/en/", "text/html"),
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
            if path in ("/en/", "/ar/"):
                # Detect skipped or stale Cloudflare Pages deployments.
                language = path.strip("/")
                local_html = (Path(__file__).resolve().parent.parent / language / "index.html").read_text(encoding="utf-8")
                for pattern, label in (
                    (r'<div class="float-card float-one"><strong>(.*?)</strong>', "hero metric"),
                    (r'<div class="wrap stats"><div class="stat"><b>(.*?)</b>', "stats metric"),
                ):
                    expected_match = re.search(pattern, local_html, re.S)
                    actual_match = re.search(pattern, body, re.S)
                    if not expected_match or not actual_match:
                        raise ValueError(f"Missing {label} on {language} homepage")
                    if expected_match.group(1) != actual_match.group(1):
                        raise ValueError(
                            f"Stale production {language} {label}: "
                            f"expected {expected_match.group(1)!r}, got {actual_match.group(1)!r}"
                        )
                # Verify the current-oversight KPI on the deployed page, not only in source.
                expected_count = "4 Companies" if language == "en" else "4 شركات"
                if not re.search(r"<b>\s*" + re.escape(expected_count) + r"\s*</b>", body):
                    raise ValueError(f"Live {language} homepage does not show {expected_count!r}")
                # Ensure the deployed social preview image is actually reachable.
                if language == "en":
                    preview_url = BASE + "/assets/ayman-hero.jpg"
                    with urlopen(Request(preview_url, headers={"User-Agent": "AymanSiteReleaseAudit/1.0"}), timeout=20) as preview:
                        preview_mime = preview.headers.get("Content-Type", "")
                        if preview.status != 200 or not preview_mime.startswith("image/") or not preview.read(32):
                            raise ValueError(f"Live social preview image unavailable: {preview_url} ({preview_mime})")
                    print(f"PASS social preview image {preview_url}")
                canonical = BASE + path
                if 'rel="canonical" href="' + canonical + '"' not in body:
                    raise ValueError("Incorrect homepage canonical: " + canonical)
            if path == "/sitemap.xml":
                root = ET.fromstring(body)
                ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                urls = [n.text for n in root.findall("s:url/s:loc", ns)]
                if not urls or len(urls) != len(set(urls)):
                    raise ValueError("Empty sitemap or duplicate URLs")
                if BASE + "/en/" not in urls or BASE + "/ar/" not in urls:
                    raise ValueError("Missing bilingual home URLs")
                xhtml = "{http://www.w3.org/1999/xhtml}link"
                local_sitemap = Path(__file__).resolve().parent.parent / "sitemap.xml"
                local_root = ET.parse(local_sitemap).getroot()
                expected_urls = [n.text for n in local_root.findall("s:url/s:loc", ns)]
                if set(urls) != set(expected_urls) or len(urls) != len(expected_urls):
                    missing = sorted(set(expected_urls) - set(urls))
                    extra = sorted(set(urls) - set(expected_urls))
                    raise ValueError(f"Production sitemap differs from repository: missing={missing}, extra={extra}")
                for entry in root.findall("s:url", ns):
                    loc = entry.findtext("s:loc", namespaces=ns)
                    if not loc or not (loc.startswith(BASE + "/en/") or loc.startswith(BASE + "/ar/")):
                        raise ValueError(f"Unexpected sitemap URL: {loc}")
                    suffix = loc.split("/", 4)[-1]
                    alternates = {node.get("hreflang"): node.get("href") for node in entry.findall(xhtml)}
                    for lang in ("en", "ar"):
                        expected_url = BASE + "/" + lang + "/" + suffix
                        if alternates.get(lang) != expected_url:
                            raise ValueError(f"Missing {lang} alternate for {loc}")
                # Check that every published clean URL resolves to HTML.
                # Keep these checks separate from the local file audit:
                # successful repository checks do not prove deployment.
                for page_url in urls:
                    try:
                        page_req = Request(page_url, headers={"User-Agent": "AymanSiteReleaseAudit/1.0"})
                        with urlopen(page_req, timeout=15) as page_response:
                            page_mime = page_response.headers.get("Content-Type", "")
                            page_body = page_response.read(350_000).decode("utf-8", "replace")
                            # Indexing can be blocked by HTTP headers even when HTML metadata is valid.
                            x_robots = page_response.headers.get("X-Robots-Tag", "").lower()
                            if re.search(r"(?<![a-z])(?:noindex|none)(?![a-z])", x_robots):
                                raise ValueError(f"Indexing blocked by X-Robots-Tag: {x_robots}")
                            if page_response.status != 200 or "text/html" not in page_mime:
                                raise ValueError(f"Unexpected response {page_response.status} ({page_mime})")
                            if '<link rel="canonical" href="' + page_url + '"' not in page_body:
                                raise ValueError("Published canonical differs from sitemap URL")
                        print(f"PASS indexed page {page_url}")
                    except (HTTPError, URLError, ValueError, TimeoutError) as page_error:
                        errors.append(f"Indexed page {page_url}: {page_error}")
                print(f"PASS sitemap entries: {len(urls)}")
            print(f"PASS {path} -> {actual_url} [{status}; {mime}]")
            break
        except (HTTPError, URLError, ValueError, ET.ParseError, TimeoutError) as exc:
            if attempt == 2:
                errors.append(f"{path}: {exc}")
            else:
                time.sleep(5)
if errors:
    for error in errors:
        print("FAIL", error, file=sys.stderr)
    sys.exit(1)
print("Live production smoke checks passed.")
