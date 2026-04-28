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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "_site"
if not ROOT.exists():
    print(f"FAIL — build output not found at {ROOT}. Run `npm run build` first.")
    sys.exit(2)
PAGES = [
    "ko/index.html", "ko/about.html", "ko/contact.html", "ko/privacy.html",
    "en/index.html", "en/about.html", "en/contact.html", "en/privacy.html",
]
EXPECTED_HREFLANG = {"ko", "en", "x-default"}
ABSOLUTE_PREFIX = "https://object.so/"

issues: list[str] = []


def check_page(p: str) -> None:
    html = (ROOT / p).read_text(encoding="utf-8")
    canonicals = re.findall(r'<link rel="canonical" href="([^"]+)"', html)
    hreflangs = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html)

    if len(canonicals) != 1:
        issues.append(f"{p}: canonical count = {len(canonicals)} (expected 1)")

    langs = {l for l, _ in hreflangs}
    missing = EXPECTED_HREFLANG - langs
    if missing:
        issues.append(f"{p}: missing hreflang {sorted(missing)}")

    own_lang = "ko" if p.startswith("ko/") else "en"
    own_hreflang_url = next((u for l, u in hreflangs if l == own_lang), None)
    if canonicals and canonicals[0] != own_hreflang_url:
        issues.append(f"{p}: canonical {canonicals[0]!r} != self hreflang {own_hreflang_url!r}")

    x_default = next((u for l, u in hreflangs if l == "x-default"), None)
    ko_url = next((u for l, u in hreflangs if l == "ko"), None)
    if x_default != ko_url:
        issues.append(f"{p}: x-default {x_default!r} != ko {ko_url!r}")

    for l, u in hreflangs:
        if not u.startswith(ABSOLUTE_PREFIX):
            issues.append(f"{p}: hreflang {l} is not absolute on object.so: {u}")


def check_sitemap() -> None:
    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = set(re.findall(r"<loc>([^<]+)</loc>", sm))

    canonicals: set[str] = set()
    for p in PAGES:
        html = (ROOT / p).read_text(encoding="utf-8")
        m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        if m:
            canonicals.add(m.group(1))

    only_in_sitemap = locs - canonicals
    only_in_html = canonicals - locs
    if only_in_sitemap:
        issues.append(f"sitemap.xml has URLs not in HTML canonicals: {sorted(only_in_sitemap)}")
    if only_in_html:
        issues.append(f"HTML canonicals not in sitemap.xml: {sorted(only_in_html)}")


def main() -> int:
    for p in PAGES:
        if not (ROOT / p).exists():
            issues.append(f"missing page: {p}")
            continue
        check_page(p)
    check_sitemap()

    if issues:
        print(f"FAIL — {len(issues)} issue(s):")
        for i in issues:
            print(f"  ✗ {i}")
        return 1

    print(f"OK — {len(PAGES)} pages + sitemap.xml all consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
