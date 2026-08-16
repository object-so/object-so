#!/usr/bin/env python3
"""Apple/Google 공식 스토어 뱃지의 벤더 규정 준수를 검사한다.

왜 필요한가
-----------
뱃지는 벤더 아트워크를 **바이트 그대로** 쓰는 것이 조건이고(Apple "Use only the badge
artwork provided" / "Don't modify"), 크기·여백·순서에도 규정이 걸려 있다. 이 조건들은
빌드도 브라우저도 알려주지 않아서, 누가 assets/에 SVG 최적화를 한 번 돌리거나
로케일을 추가하며 종횡비를 복사해 오면 조용히 위반 상태가 된다.

검사 항목
---------
1. 자산 무결성 — 커밋된 SVG가 벤더 배포본과 SHA-256까지 동일한가
2. 종횡비 동기화 — site.css의 aspect-ratio가 해당 SVG의 viewBox와 일치하는가
   (두 값을 **서로 다른 파일에서** 읽어 비교한다. 한쪽에서 계산해 되돌리는
    항등식 단언은 자산을 한 바이트도 안 보고 통과하므로 검사가 아니다.)
3. 크기 관계 — Google "same size or larger": 같은 높이에서 Play 폭 >= Apple 폭
4. 순서 — Apple "Place the App Store badge first in the lineup"
5. 상표 귀속 문구 — 벤더 공식 출력 그대로인가(축자 잠금)
6. clear space — 래퍼 패딩이 뱃지 높이의 1/4 이상인가
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BADGES = ROOT / "assets" / "img" / "badges"
CSS = ROOT / "assets" / "css" / "site.css"
SITE = ROOT / "_site"

BADGE_HEIGHT = 44  # site.css의 .badge-link img { height }

# 벤더 배포본 해시. Apple은 marketingtools 뱃지 API, Google은 파트너 마케팅 허브
# 묶음(Digital/svg)에서 받은 원본이다. 이 값이 틀리면 아트워크가 수정된 것이다.
VENDOR_SHA256 = {
    "app-store-en.svg":   "a26fc5b38380272c92e9019a2eb8b45542a66814b3e2b203772db8904b9fb99f",
    "app-store-ko.svg":   "fc82d5344d0f2919a7ae697e677fc9c62872f1ee47bd70e24a581245423de9c1",
    "google-play-en.svg": "4ffa4c7edd2f10b297ca4de2131eddaa00d03b2278d1e178fe512920d824ca34",
    "google-play-ko.svg": "14cd92c4b78a1419746cb878f74f2a9c65b8e0b5edd56160cad39e98df82a4cc",
}

# CSS 클래스 -> 자산 파일
CLASS_TO_ASSET = {
    "badge-appstore-en":   "app-store-en.svg",
    "badge-appstore-ko":   "app-store-ko.svg",
    "badge-googleplay-en": "google-play-en.svg",
    "badge-googleplay-ko": "google-play-ko.svg",
}

# 벤더 공식 출력 그대로. 손대면 «공식»이 아니라 우리 번역이 된다.
# (한국어 Google 문구의 미해결 조사 "(은)는"도 생성기 출력이라 그대로 둔다.)
LEGAL_LINES = {
    "ko/dailysudoku.html": [
        "App Store</span>는 Apple Inc.의 서비스 마크입니다.",
        "Google Play</span>(은)는 Google LLC의 상표입니다.",
    ],
    "en/dailysudoku.html": [
        "App Store is a service mark of Apple Inc.",
        "Google Play is a trademark of Google LLC.",
    ],
}

VIEWBOX_RE = re.compile(rb'viewBox="\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*"')


def svg_viewbox(name: str) -> tuple[float, float]:
    m = VIEWBOX_RE.search((BADGES / name).read_bytes())
    if not m:
        raise ValueError(f"{name}: viewBox를 찾을 수 없음")
    return float(m.group(1)), float(m.group(2))


def css_aspect_ratios(css: str) -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    for cls, w, h in re.findall(
        r"\.([\w-]+)\s*\{[^}]*?aspect-ratio:\s*([\d.]+)\s*/\s*([\d.]+)", css
    ):
        out[cls] = (float(w), float(h))
    return out


def main() -> int:
    issues: list[str] = []

    # 1. 자산 무결성
    for name, want in VENDOR_SHA256.items():
        path = BADGES / name
        if not path.exists():
            issues.append(f"{name}: 자산이 없음 ({path})")
            continue
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != want:
            issues.append(
                f"{name}: 벤더 배포본과 다름 (sha256 {got[:16]}… != {want[:16]}…) "
                f"— 아트워크 수정은 벤더 가이드라인 위반이다. 원본을 다시 받아라."
            )

    # 2. 종횡비 동기화 (SVG viewBox vs site.css — 서로 다른 출처)
    ratios = css_aspect_ratios(CSS.read_text(encoding="utf-8"))
    rendered: dict[str, float] = {}
    for cls, asset in CLASS_TO_ASSET.items():
        if not (BADGES / asset).exists():
            continue
        vb_w, vb_h = svg_viewbox(asset)
        if cls not in ratios:
            issues.append(f".{cls}: site.css에 aspect-ratio가 없음 (자산 {asset})")
            continue
        css_w, css_h = ratios[cls]
        if (css_w, css_h) != (vb_w, vb_h):
            issues.append(
                f".{cls}: aspect-ratio {css_w}/{css_h} != {asset}의 viewBox {vb_w}/{vb_h}"
            )
        rendered[cls] = BADGE_HEIGHT * vb_w / vb_h

    # 3. Google "same size or larger" — 같은 높이에서 Play 폭 >= Apple 폭
    for loc in ("en", "ko"):
        a, g = f"badge-appstore-{loc}", f"badge-googleplay-{loc}"
        if a in rendered and g in rendered and rendered[g] < rendered[a]:
            issues.append(
                f"[{loc}] Play 뱃지({rendered[g]:.2f}px)가 Apple 뱃지({rendered[a]:.2f}px)보다 작다 "
                f"— Google은 'same size or larger'를 요구한다"
            )

    # 4~6. 빌드 산출물 검사
    if not SITE.exists():
        issues.append(f"빌드 산출물이 없음: {SITE}. 먼저 `npm run build`.")
    else:
        for page, lines in LEGAL_LINES.items():
            path = SITE / page
            if not path.exists():
                issues.append(f"{page}: 페이지가 없음")
                continue
            html = path.read_text(encoding="utf-8")
            loc = page.split("/")[0]

            for line in lines:  # 5. 귀속 문구 축자 잠금
                if line not in html:
                    issues.append(f"{page}: 상표 귀속 문구 누락/변경 — {line!r}")

            # 4. Apple 먼저
            i_apple = html.find(f"badge-appstore-{loc}")
            i_play = html.find(f"badge-googleplay-{loc}")
            if i_apple < 0 or i_play < 0:
                issues.append(f"{page}: 뱃지 마크업을 찾을 수 없음")
            elif i_apple > i_play:
                issues.append(
                    f"{page}: Google Play 뱃지가 App Store 뱃지보다 먼저 나온다 "
                    f"— Apple은 'Place the App Store badge first'를 요구한다"
                )

            # 로케일에 맞는 자산을 참조하는지 (다른 로케일 자산이 새어 들어오는 사고 방지)
            for other in ("en", "ko"):
                if other != loc and f"/badges/app-store-{other}.svg" in html:
                    issues.append(f"{page}: 다른 로케일 자산 참조 — app-store-{other}.svg")

    # 6. clear space — 래퍼 패딩 >= 높이/4
    css_text = CSS.read_text(encoding="utf-8")
    m = re.search(r"\.badge-link\s*\{[^}]*?padding:\s*(\d+)px", css_text)
    if not m:
        issues.append(".badge-link: padding(clear space)을 찾을 수 없음")
    elif int(m.group(1)) < BADGE_HEIGHT / 4:
        issues.append(
            f".badge-link: padding {m.group(1)}px < 필요 clear space {BADGE_HEIGHT / 4:.0f}px "
            f"(두 벤더 모두 뱃지 높이의 1/4을 요구한다)"
        )

    if issues:
        print(f"FAIL: {len(issues)} issue(s):")
        for i in issues:
            print(f"  - {i}")
        return 1

    widths = ", ".join(f"{c.replace('badge-', '')}={w:.1f}px" for c, w in sorted(rendered.items()))
    print(f"OK: {len(VENDOR_SHA256)} badge assets verified (h={BADGE_HEIGHT}px → {widths}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
