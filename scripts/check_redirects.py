#!/usr/bin/env python3
"""Audit public redirects without following them; run after Cloudflare deployment."""
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
import sys

BASE = "https://aymanesam.com"
PATHS = [
    ("/", "/en/"),
    ("/ar/insights/working-capital-discipline.html", "/ar/insights/working-capital-discipline"),
    ("/ar/insights/finance-transformation.html", "/ar/insights/finance-transformation"),
    ("/ar/insights/month-end-close-discipline.html", "/ar/insights/month-end-close-discipline"),
    ("/ar/insights/cash-flow-liquidity-rhythm.html", "/ar/insights/cash-flow-liquidity-rhythm"),
]
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = build_opener(NoRedirect)
failed = False
for path, target in PATHS:
    try:
        response = opener.open(Request(BASE + path, headers={"User-Agent": "AymanSiteRedirectAudit/1.0"}), timeout=20)
        status, location = response.status, response.headers.get("Location", "")
    except HTTPError as exc:
        status, location = exc.code, exc.headers.get("Location", "")
    except (URLError, TimeoutError) as exc:
        print(f"FAIL {path}: request failed: {exc}")
        failed = True
        continue
    # A 301 must go directly to the clean canonical URL, without an intermediate hop.
    good = status == 301 and location in (BASE + target, target)
    print(f"{'PASS' if good else 'FAIL'} {path}: HTTP {status}, Location={location!r}, expected={BASE + target}")
    failed |= not good
sys.exit(1 if failed else 0)
