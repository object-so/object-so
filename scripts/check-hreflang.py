#!/usr/bin/env python3
"""
hreflang/canonical/sitemap consistency checker.

Reads from the Eleventy build output (_site/), so `npm run build` must run first.

Run via:  npm run check:hreflang   (or)   python3 scripts/check-hreflang.py

Exits non-zero if any of the following fail:
  - each content page has exactly 1 canonical
  - each content page has hreflang ko + en + x-default
  - x-default points at the KO version (per spec: KO is the legal master)
  - canonical URL == self hreflang
  - all hreflang URLs are absolute https://object.so/...
  - sitemap.xml <loc> set == HTML canonical set
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent / "_site"
if not ROOT.exists():
    print(f"FAIL — build output not found at {ROOT}. Run `npm run build` first.")
    sys.exit(2)
EXPECTED_HREFLANG = {"ko", "en", "x-default"}
ABSOLUTE_PREFIX = "https://object.so/"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
XHTML_NS = "{http://www.w3.org/1999/xhtml}"

issues: list[str] = []


def sitemap_entries() -> list[tuple[str, dict[str, str]]]:
    sitemap = ROOT / "sitemap.xml"
    try:
        tree = ET.parse(sitemap)
    except ET.ParseError as exc:
        issues.append(f"sitemap.xml is invalid XML: {exc}")
        return []

    entries: list[tuple[str, dict[str, str]]] = []
    seen: set[str] = set()
    for url in tree.getroot().findall(f"{SITEMAP_NS}url"):
        loc_el = url.find(f"{SITEMAP_NS}loc")
        loc = (loc_el.text or "").strip() if loc_el is not None else ""
        if not loc:
            issues.append("sitemap.xml has <url> without <loc>")
            continue
        if loc in seen:
            issues.append(f"sitemap.xml has duplicate <loc>: {loc}")
        seen.add(loc)

        alternates: dict[str, str] = {}
        for link in url.findall(f"{XHTML_NS}link"):
            if link.attrib.get("rel") == "alternate" and link.attrib.get("hreflang"):
                alternates[link.attrib["hreflang"]] = link.attrib.get("href", "")
        entries.append((loc, alternates))

    if not entries:
        issues.append("sitemap.xml has no URL entries")
    return entries


def page_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "object.so":
        issues.append(f"sitemap.xml <loc> is not on https://object.so: {url}")
        return None
    path = parsed.path.lstrip("/")
    if not path.endswith(".html"):
        issues.append(f"sitemap.xml <loc> is not an HTML page: {url}")
        return None
    return path


def check_page(p: str, loc: str, sitemap_alternates: dict[str, str]) -> None:
    html = (ROOT / p).read_text(encoding="utf-8")
    canonicals = re.findall(r'<link rel="canonical" href="([^"]+)"', html)
    hreflangs = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html)
    hreflang_map = dict(hreflangs)

    if len(canonicals) != 1:
        issues.append(f"{p}: canonical count = {len(canonicals)} (expected 1)")
    elif canonicals[0] != loc:
        issues.append(f"{p}: canonical {canonicals[0]!r} != sitemap loc {loc!r}")

    if len(hreflang_map) != len(hreflangs):
        issues.append(f"{p}: duplicate hreflang entries")

    langs = set(hreflang_map)
    missing = EXPECTED_HREFLANG - langs
    if missing:
        issues.append(f"{p}: missing hreflang {sorted(missing)}")

    own_lang = "ko" if p.startswith("ko/") else "en"
    own_hreflang_url = hreflang_map.get(own_lang)
    if canonicals and canonicals[0] != own_hreflang_url:
        issues.append(f"{p}: canonical {canonicals[0]!r} != self hreflang {own_hreflang_url!r}")

    x_default = hreflang_map.get("x-default")
    ko_url = hreflang_map.get("ko")
    if x_default != ko_url:
        issues.append(f"{p}: x-default {x_default!r} != ko {ko_url!r}")

    for l, u in hreflangs:
        if not u.startswith(ABSOLUTE_PREFIX):
            issues.append(f"{p}: hreflang {l} is not absolute on object.so: {u}")

    if set(sitemap_alternates) != EXPECTED_HREFLANG:
        issues.append(f"{p}: sitemap alternates are {sorted(sitemap_alternates)} (expected {sorted(EXPECTED_HREFLANG)})")
    for lang in EXPECTED_HREFLANG:
        if sitemap_alternates.get(lang) != hreflang_map.get(lang):
            issues.append(f"{p}: sitemap hreflang {lang} {sitemap_alternates.get(lang)!r} != HTML {hreflang_map.get(lang)!r}")


def main() -> int:
    checked = 0
    for loc, alternates in sitemap_entries():
        p = page_from_url(loc)
        if p is None:
            continue
        if not (ROOT / p).exists():
            issues.append(f"missing page: {p}")
            continue
        check_page(p, loc, alternates)
        checked += 1

    if issues:
        print(f"FAIL — {len(issues)} issue(s):")
        for i in issues:
            print(f"  ✗ {i}")
        return 1

    print(f"OK — {checked} sitemap pages, canonicals, and hreflang alternates are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
