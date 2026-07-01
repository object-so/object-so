#!/usr/bin/env python3
"""Validate JSON-LD blocks in the Eleventy build output."""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent / "_site"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
SCRIPT_RE = re.compile(
    r'<script\s+type=["\']application/ld\+json["\']>\s*(.*?)\s*</script>',
    re.I | re.S,
)


def sitemap_pages() -> tuple[list[str], list[str]]:
    issues: list[str] = []
    try:
        tree = ET.parse(ROOT / "sitemap.xml")
    except ET.ParseError as exc:
        return [], [f"sitemap.xml is invalid XML: {exc}"]

    pages: list[str] = []
    for url in tree.getroot().findall(f"{SITEMAP_NS}url"):
        loc_el = url.find(f"{SITEMAP_NS}loc")
        loc = (loc_el.text or "").strip() if loc_el is not None else ""
        parsed = urlparse(loc)
        if parsed.scheme != "https" or parsed.netloc != "object.so":
            issues.append(f"sitemap.xml <loc> is not on https://object.so: {loc}")
            continue
        path = parsed.path.lstrip("/")
        if not path.endswith(".html"):
            issues.append(f"sitemap.xml <loc> is not an HTML page: {loc}")
            continue
        pages.append(path)

    if not pages:
        issues.append("sitemap.xml has no HTML page entries")
    return pages, issues


def main() -> int:
    if not ROOT.exists():
        print(f"FAIL: build output not found at {ROOT}. Run `npm run build` first.")
        return 2

    pages, issues = sitemap_pages()
    checked = 0

    for page in pages:
        path = ROOT / page
        if not path.exists():
            issues.append(f"{page}: missing page")
            continue

        blocks = SCRIPT_RE.findall(path.read_text(encoding="utf-8"))
        if len(blocks) != 1:
            issues.append(f"{page}: JSON-LD block count = {len(blocks)} (expected 1)")
            continue

        try:
            json.loads(blocks[0])
        except json.JSONDecodeError as exc:
            issues.append(f"{page}: invalid JSON-LD: {exc}")
            continue

        checked += 1

    if issues:
        print(f"FAIL: {len(issues)} issue(s):")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print(f"OK: {checked} JSON-LD blocks parsed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
