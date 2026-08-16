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


HOME_NAMES = {"홈", "Home"}


def check_breadcrumb(page: str, graph: list[dict]) -> list[str]:
    """BreadcrumbList의 항목명이 실제 페이지 이름인지 검사한다.

    jsonld.njk는 i18n.pageNames[slug]로 이름을 조회한다. 새 페이지를 추가하면서
    pageNames에 slug를 빠뜨리면 fallback인 `title`("소개 · 오브젝트")이 들어가거나,
    과거 if-체인 구조에서는 조용히 "홈"으로 찍혔다. 파싱만 해서는 둘 다 통과하므로
    여기서 잡는다.
    """
    issues: list[str] = []
    crumbs = [n for n in graph if n.get("@type") == "BreadcrumbList"]
    if page.endswith("index.html"):
        if crumbs:
            issues.append(f"{page}: index page should not emit a BreadcrumbList")
        return issues
    if not crumbs:
        issues.append(f"{page}: non-index page is missing a BreadcrumbList")
        return issues

    items = crumbs[0].get("itemListElement", [])
    if len(items) < 2:
        issues.append(f"{page}: BreadcrumbList has {len(items)} item(s), expected >= 2")
        return issues

    for item in items[1:]:
        name = item.get("name", "")
        # pageNames 누락 → 과거 if-체인에서는 "홈"으로 폴백됐다.
        if name in HOME_NAMES:
            issues.append(
                f"{page}: breadcrumb item {item.get('position')} is named {name!r} "
                f"— add this slug to i18n.pageNames"
            )
        # pageNames 누락 → 현재 fallback은 title이라 사이트명이 딸려 들어온다.
        if "·" in name:
            issues.append(
                f"{page}: breadcrumb item {item.get('position')} name {name!r} looks like "
                f"a page <title>, not a page name — add this slug to i18n.pageNames"
            )
    return issues


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
            data = json.loads(blocks[0])
        except json.JSONDecodeError as exc:
            issues.append(f"{page}: invalid JSON-LD: {exc}")
            continue

        issues.extend(check_breadcrumb(page, data.get("@graph", [])))
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
