#!/usr/bin/env python3
"""Validate the public bilingual homepage Person structured data and SEO identity."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

DOMAIN = "https://aymanesam.com"
EXPECTED_NAMES = {"Ayman Esam", "Ayman Essam", "Ayman Isam", "Ayman Issam", "أيمن عصام", "أيمن عصام محمد عبدالسلام"}

for lang in ("en", "ar"):
    html = Path(lang, "index.html").read_text(encoding="utf-8")
    blocks = re.findall(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S)
    assert blocks, f"{lang}: missing JSON-LD"
    persons = []
    for block in blocks:
        data = json.loads(block)
        entries = data.get("@graph", []) if isinstance(data, dict) and "@graph" in data else [data]
        persons.extend(x for x in entries if isinstance(x, dict) and x.get("@type") == "Person")
    assert len(persons) == 1, f"{lang}: expected one Person schema"
    person = persons[0]
    assert person.get("@context") == "https://schema.org" or any(
        isinstance(json.loads(block), dict) and json.loads(block).get("@context") == "https://schema.org"
        for block in blocks
    ), f"{lang}: missing schema.org context"
    assert person.get("@id") == f"{DOMAIN}/#person", f"{lang}: inconsistent Person identity"
    assert person.get("name") == "Ayman Esam", f"{lang}: incorrect Person name"
    assert person.get("jobTitle") == "Group Financial Controller", f"{lang}: incorrect public job title"
    assert EXPECTED_NAMES.issubset(set(person.get("alternateName", [])) | {person["name"]}), f"{lang}: missing alternate name spellings"
    assert urlparse(person.get("url", "")).netloc == "aymanesam.com", f"{lang}: invalid Person URL"
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    assert canonical and canonical.group(1) == f"{DOMAIN}/{lang}/", f"{lang}: wrong canonical"
    for other in ("en", "ar"):
        assert f'hreflang="{other}" href="{DOMAIN}/{other}/"' in html, f"{lang}: missing {other} alternate"
    assert "SAR 700M+" not in html and "+700" not in html, f"{lang}: outdated KPI"
    print(f"{lang.upper()}: Person schema, alternate names, canonical, hreflang and KPI valid")
