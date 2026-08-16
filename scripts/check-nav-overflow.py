#!/usr/bin/env python3
"""헤더 내비게이션이 문서를 가로로 밀어내지 못하게 하는 구조적 불변식을 검사한다.

왜 필요한가
-----------
nav 오버플로는 레이아웃 버그라 정적 검사로는 «넘치는지»를 알 수 없다. 브라우저로
폭을 훑어야 잡히는데, 그걸 CI 에 넣으려면 Playwright 의존성이 생긴다. 대신
**넘치더라도 페이지가 아니라 링크 목록만 스크롤되게 하는 CSS 불변식**을 잠근다.
이게 있으면 nav 항목이 몇 개로 늘든 실패 모드가 «내부 스크롤»(보기 아쉬움)이지
«문서 가로 스크롤»(레이아웃 붕괴)이 되지 않는다.

실제로 이 두 줄이 @media 블록 안에 들어가 있어서 601~726px 구간이 무방비였고
`/en/index.html` 이 그 상태로 라이브에 나갔다. 폭 두 지점만 샘플링해서 놓쳤다.

같이 잠그는 것
--------------
`container-type: inline-size` 가 사라지면 `@container` 블록이 **영원히 매칭되지
않아** 햄버거가 조용히 죽고 모바일에서 데스크톱 nav 가 그대로 나온다. 빌드도
브라우저도 오류를 내지 않는 종류의 실패라 여기서 막는다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "assets" / "css" / "site.css"
SITE = ROOT / "_site"

COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)


AT_BLOCK_RE = re.compile(r"@(?:media|container|supports)[^{]*\{")


def strip_at_blocks(css: str) -> str:
    """@media / @container / @supports 블록을 본문째 제거해 «상시 적용» CSS 만 남긴다.

    중괄호를 직접 세며 규칙을 훑는 방식은 중첩에서 쉽게 어긋난다(실제로 한 번 틀렸다).
    조건부 블록을 통째로 도려내고 나면 남은 것이 정의상 최상위 규칙이다.
    """
    out: list[str] = []
    i = 0
    while True:
        m = AT_BLOCK_RE.search(css, i)
        if not m:
            out.append(css[i:])
            return "".join(out)
        out.append(css[i:m.start()])
        depth = 0
        j = m.end() - 1  # 여는 중괄호 위치
        while j < len(css):
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        i = j + 1


def top_level_rule(css: str, selector: str) -> str | None:
    """조건부 블록 밖에 있는 selector 규칙들의 본문을 합쳐서 돌려준다.

    불변식은 «상시 적용»이어야 의미가 있다. 이 두 줄이 미디어쿼리 안으로 들어간
    순간이 정확히 601~726px 버그가 생긴 순간이었다.
    """
    flat = strip_at_blocks(css)
    bodies = [
        m.group(2)
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", flat)
        if selector in [s.strip() for s in m.group(1).split(",")]
    ]
    return "\n".join(bodies) if bodies else None


def main() -> int:
    issues: list[str] = []
    css = COMMENT_RE.sub("", CSS.read_text(encoding="utf-8"))

    # 1. 컨테이너 쿼리의 전제
    nav = top_level_rule(css, ".nav")
    if nav is None:
        issues.append(".nav: 최상위 규칙을 찾을 수 없음")
    elif not re.search(r"container-type\s*:\s*inline-size", nav):
        issues.append(
            ".nav: `container-type: inline-size` 가 없다 — @container 블록이 영원히 "
            "매칭되지 않아 모바일 햄버거가 조용히 죽는다"
        )

    # 2. 오버플로 안전망이 상시 적용인지
    links = top_level_rule(css, ".nav-links")
    if links is None:
        issues.append(".nav-links: 최상위 규칙을 찾을 수 없음 (미디어쿼리 안으로 들어갔나?)")
    else:
        for prop, pattern in (("min-width: 0", r"min-width\s*:\s*0"),
                              ("overflow-x: auto", r"overflow-x\s*:\s*auto")):
            if not re.search(pattern, links):
                issues.append(
                    f".nav-links: base 규칙에 `{prop}` 가 없다 — nav 가 넘칠 때 링크 목록이 "
                    f"아니라 문서 전체가 가로 스크롤된다"
                )

    # 3. 햄버거 마크업 (빌드 산출물)
    # header.njk 의 두 분기를 모두 검사한다. 토글은 if/else «밖»이라 오늘은 갈릴 수 없지만,
    # 가드의 목적이 미래의 편집을 잡는 것이므로 index 만 보면 else 분기 수정이 그냥 통과한다.
    # 실제 배포 페이지 14개 중 12개가 non-index 분기다.
    for rel in ("ko/index.html", "ko/dailysudoku.html"):
        page = SITE / rel
        if not page.exists():
            issues.append(f"빌드 산출물이 없음: {page}. 먼저 `npm run build`.")
            continue
        html = page.read_text(encoding="utf-8")
        if 'class="nav-toggle"' not in html:
            issues.append(f"{rel}: .nav-toggle 버튼이 없다")
        if 'aria-controls="nav-panel"' not in html:
            issues.append(f'{rel}: 토글에 aria-controls="nav-panel" 이 없다')
        if 'id="nav-panel"' not in html:
            issues.append(f'{rel}: aria-controls 가 가리키는 id="nav-panel" 이 없다')
        if "aria-expanded" not in html:
            issues.append(f"{rel}: 토글에 aria-expanded 가 없다")
        # 4. JS 없을 때의 탈출구
        if "<noscript>" not in html or ".nav-toggle" not in html.split("<noscript>")[-1][:800]:
            issues.append(
                f"{rel}: <noscript> 폴백이 없다 — JS 가 없으면 토글이 죽은 버튼이 되고 "
                f"내비게이션 전체에 도달할 수 없게 된다"
            )

    if issues:
        print(f"FAIL: {len(issues)} issue(s):")
        for i in issues:
            print(f"  - {i}")
        return 1

    print("OK: nav overflow invariants + hamburger markup + noscript fallback.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
