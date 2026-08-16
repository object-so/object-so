#!/usr/bin/env python3
"""빌드된 페이지의 CSS 링크에 내용 해시가 붙어 있는지 검사한다.

왜 필요한가
-----------
deploy.yml 이 CSS 에 `max-age=604800`(7일), HTML 에 `max-age=3600`(1시간)을 준다.
파일명이나 URL 에 지문이 없으면 재방문자는 **새 HTML + 옛 CSS** 를 최대 7일간 본다.
CloudFront invalidation 은 엣지 캐시만 비우고 방문자 브라우저 캐시는 못 건드린다.

가설이 아니라 실제로 겪었다. 햄버거 배포(#19) 직후 브라우저가 직전 배포의 CSS 를
들고 있어서 데스크톱에 토글이 튀어나오고 620~780px 에서 nav 가 문서를 밀어냈다.
`curl` 로는 새 CSS 가 내려오는데 브라우저가 파싱한 CSSOM 에는 `@container` 룰이
0개였던 것이 결정적 증거였다.

`| bust` 필터를 한 번 빠뜨리면 이 상태가 소리 없이 돌아온다. 빌드도 브라우저도
오류를 내지 않는다 — 그래서 여기서 막는다.

검사 항목
---------
1. 모든 페이지의 모든 `<link rel="stylesheet">` 에 `?v=<8자리 hex>` 가 있는가
2. 그 해시가 **실제 파일 내용의 sha1 앞 8자리와 일치**하는가
   (하드코딩하거나 옛 값이 남은 경우를 잡는다 — 존재 여부만 보면 통과해버린다)
3. 같은 자산은 모든 페이지에서 같은 해시인가 (일부 페이지만 갱신되는 상황 방지)
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"

STYLESHEET_RE = re.compile(r'<link\s+rel="stylesheet"\s+href="([^"]+)"', re.I)
BUST_RE = re.compile(r"^(/assets/[^?]+)\?v=([0-9a-f]{8})$")


def content_hash(url_path: str) -> str | None:
    src = ROOT / url_path.lstrip("/")
    if not src.exists():
        return None
    return hashlib.sha1(src.read_bytes()).hexdigest()[:8]


def main() -> int:
    if not SITE.exists():
        print(f"FAIL: 빌드 산출물이 없음: {SITE}. 먼저 `npm run build`.")
        return 2

    pages = sorted(SITE.glob("ko/*.html")) + sorted(SITE.glob("en/*.html"))
    if not pages:
        print("FAIL: 검사할 페이지를 찾지 못했다 (_site/ko, _site/en 이 비었다)")
        return 1

    issues: list[str] = []
    seen: dict[str, str] = {}   # asset -> hash (페이지 간 일관성 확인용)
    checked = 0

    for page in pages:
        rel = page.relative_to(SITE)
        for href in STYLESHEET_RE.findall(page.read_text(encoding="utf-8")):
            checked += 1
            m = BUST_RE.match(href)
            if not m:
                issues.append(
                    f"{rel}: 스타일시트에 내용 해시가 없다 — {href!r}. "
                    f"head-meta.njk 에서 `| bust` 필터가 빠졌는지 확인하라"
                )
                continue
            asset, got = m.group(1), m.group(2)
            want = content_hash(asset)
            if want is None:
                issues.append(f"{rel}: {asset} 원본 파일을 찾을 수 없다")
                continue
            if got != want:
                issues.append(
                    f"{rel}: {asset} 해시 불일치 — HTML={got} 실제={want}. "
                    f"값이 하드코딩됐거나 오래된 빌드 산출물이다"
                )
            prev = seen.setdefault(asset, got)
            if prev != got:
                issues.append(f"{rel}: {asset} 해시가 페이지마다 다르다 ({prev} != {got})")

    if issues:
        print(f"FAIL: {len(issues)} issue(s):")
        for i in issues:
            print(f"  - {i}")
        return 1

    fingerprints = ", ".join(f"{a.split('/')[-1]}={h}" for a, h in sorted(seen.items()))
    print(f"OK: {checked} stylesheet links across {len(pages)} pages fingerprinted ({fingerprints}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
