#!/usr/bin/env python3
"""Diagnose production redirect chains for four Search Console article URLs."""
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit

BASE = "https://aymanesam.com"
SLUGS = (
    "working-capital-discipline",
    "finance-transformation",
    "month-end-close-discipline",
    "cash-flow-liquidity-rhythm",
)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = build_opener(NoRedirect)
errors = []
for slug in SLUGS:
    start = f"{BASE}/ar/insights/{slug}.html"
    current = start
    seen = set()
    chain = []
    for _ in range(8):
        if current in seen:
            errors.append(f"{start}: redirect loop at {current}")
            break
        seen.add(current)
        try:
            response = opener.open(Request(current, headers={"User-Agent": "AymanSiteRedirectAudit/1.0"}), timeout=20)
        except HTTPError as exc:
            response = exc
        status = response.status
        chain.append(f"{status} {current}")
        if status in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")
            if not location:
                errors.append(f"{start}: redirect without Location")
                break
            next_url = urljoin(current, location)
            if urlsplit(next_url).netloc != "aymanesam.com" or urlsplit(next_url).scheme != "https":
                errors.append(f"{start}: unexpected redirect destination {next_url}")
                break
            current = next_url
        elif status == 200:
            if not current.startswith(BASE + "/ar/insights/"):
                errors.append(f"{start}: unexpected final URL {current}")
            break
        else:
            errors.append(f"{start}: terminal HTTP {status}")
            break
    else:
        errors.append(f"{start}: more than 8 redirect hops")
    print(" -> ".join(chain), flush=True)
    if len(chain) > 4:
        errors.append(f"{start}: excessive redirect chain ({len(chain)} requests)")
for error in errors:
    print("ERROR:", error, flush=True)
raise SystemExit(bool(errors))
