# object-so

오브젝트(Object) 회사 소개 사이트 — 정적 HTML/CSS, KO·EN 다국어.

> 단일 목적의 앱과 서비스를 만드는 1인 소프트웨어 공방. 페이지는 작고, 카피는 짧고, 타이포는 단단하게.

## 폴더 구조

```
object-so/
├── index.html                루트 라우터 (JS+meta refresh로 KO/EN 자동 분기, noindex)
├── ko/{index,about,contact,privacy}.html
├── en/{index,about,contact,privacy}.html
├── assets/
│   ├── css/
│   │   ├── tokens.css        Open Color 팔레트 + Pretendard + 시맨틱 토큰 + dark mode 분기
│   │   └── site.css          페이지 스타일 + reduce-motion 분기
│   ├── fonts/                Pretendard 9 weights (Thin~Black)
│   └── img/                  favicon.svg, favicon-32.png, apple-touch-icon.png, og-1200x630.png, logo.svg, wordmark.svg
├── content/
│   └── legal/                개인정보처리방침 마크다운 원본 (single source of truth)
│       ├── privacy-policy-ko.md
│       └── privacy-policy-en.md
├── docs/
│   └── HOSTING.md            정적 호스팅 환경별 redirect rule 가이드
├── scripts/
│   └── check-hreflang.py     hreflang/canonical/sitemap 일관성 점검
├── .github/workflows/ci.yml  PR/Push 시 자동 점검
├── eleventy.config.js        빌드 도구 베이스 (옵트인)
├── package.json              npm scripts (dev/build/check)
├── robots.txt
└── sitemap.xml               8개 콘텐츠 페이지 + hreflang trio
```

## 디자인 시스템

- **컬러**: [Open Color](https://yeun.github.io/open-color/) 회색 파운데이션 + 단일 액센트(blue-6 #228be6)
- **타이포**: [Pretendard](https://github.com/orioncactus/pretendard) (KR + Latin), `font-display: swap`, 가장 큰 LCP 후보(Regular/ExtraBold)는 preload
- **간격**: 4px 그리드, `--space-*` 토큰
- **다크 모드**: `prefers-color-scheme: dark` 자동 적용. `<body class="theme-light">` 부여 시 강제 light
- **모션**: `prefers-reduced-motion: reduce` 시 transition/animation 비활성

토큰 정의 → `assets/css/tokens.css`. 페이지 스타일 → `assets/css/site.css`.

## 페이지 콘텐츠 명세

- 모든 콘텐츠 페이지는 `<head>`에 canonical · hreflang(ko/en/x-default) · OG · Twitter · favicon · theme-color(light/dark) 메타 포함
- KO 홈/EN 홈에 `Organization` JSON-LD 구조화 데이터
- 헤더·푸터는 모든 페이지 공통. 새 페이지 만들 때 기존 페이지에서 그대로 복사하고 다음만 변경:
  - **헤더**: `nav-links` 안에서 `.active aria-current="page"` 위치를 현재 페이지로 (단, privacy는 nav 항목이 아니므로 active 없음)
  - **헤더 + 푸터**: KO/EN 토글의 EN(또는 KO) `href`를 같은 페이지의 영문(또는 한국어) 짝으로 — 두 군데에 등장하니 둘 다 갱신
  - **EN 페이지**: nav 텍스트(홈/소개/문의 → Home/About/Contact), `aria-label`, footer 키 라벨, lang-pair `.on` 위치 모두 영문화

자세한 가이드는 `ko/contact.html` 상단의 `<!-- BEGIN HEADER -->` 코멘트 블록 참고.

## 개발

### 즉시 미리보기 (빌드 도구 없이)

```bash
python3 -m http.server 8765
# http://localhost:8765/ 에서 확인 (루트 진입 시 자동으로 /ko/ 또는 /en/으로 분기)
```

### Eleventy로 빌드

```bash
npm install
npm run build       # → _site/
npm run dev         # http://localhost:8080 + 라이브 리로드
```

현재 `eleventy.config.js`는 기존 HTML을 passthrough로만 처리합니다. 마크다운 → HTML 빌드 자동화는 follow-up 작업.

## 점검

```bash
# hreflang/canonical/sitemap 일관성 점검 (CI에서도 동일하게 돌아감)
python3 scripts/check-hreflang.py
# or
npm run check:hreflang
```

CI(GitHub Actions)는 PR/Push 시 다음을 자동 검증:

1. 모든 HTML의 JSON-LD JSON 파싱 valid 여부
2. sitemap.xml well-formed XML
3. hreflang/canonical/sitemap 일관성 (`scripts/check-hreflang.py`)
4. Eleventy 빌드 성공
5. html-proofer로 빌드 결과의 내부 링크·HTML 유효성·favicon 존재 점검

## 배포

### 정적 호스팅 (권장)

`docs/HOSTING.md`에 Cloudflare Pages / Netlify / Vercel / GitHub Pages / S3+CloudFront / nginx 별 redirect rule 패턴이 정리되어 있습니다.

**중요**: 운영 도메인을 결정하면 다음 위치를 일괄 치환해야 합니다.

```bash
find . -type f \( -name '*.html' -o -name '*.xml' -o -name '*.txt' \) \
  -not -path './node_modules/*' -not -path './_site/*' \
  -exec sed -i '' 's|https://object\.so|https://YOUR_DOMAIN|g' {} +
```

치환 대상: `<link rel="canonical">`, `<link rel="alternate" hreflang>`, OG `<meta>`, JSON-LD url/logo, sitemap.xml `<loc>`, robots.txt `Sitemap:`.

## 콘텐츠 업데이트

### 개인정보처리방침

법적 효력 기준은 **한국어** 버전입니다. 영문은 참고용 (영문 정책 상단에 명시).

1. `content/legal/privacy-policy-ko.md` 또는 `privacy-policy-en.md` 수정
2. 마크다운 변경분을 `ko/privacy.html` 또는 `en/privacy.html` 본문에 반영
3. 시행일이 바뀌면 다음도 함께 갱신:
   - HTML의 `시행일`/`Effective` 박스
   - `sitemap.xml`의 `<lastmod>`
4. `python3 scripts/check-hreflang.py` 통과 확인

> **마크다운 → HTML 자동 빌드는 follow-up.** 현재는 마크다운이 source of truth로 보관되지만 HTML은 수동 동기화. 자동화 도입 시 누락 방지.

### 저작권 연도

- 런타임: HTML의 `[data-year]` 자리에 JS가 `new Date().getFullYear()`를 자동 주입
- 빌드 타임: Eleventy `{% year %}` shortcode가 같은 값을 정적으로 주입 (현재는 활용 안 함)

## 접근성

- WCAG 2.1 AA 기준 axe-core 점검: **color-contrast** 외 0 violation
- color-contrast는 `--fg-4` (gray-6 #868e96) 작은 텍스트 한정 — 디자이너 의도 유지로 결정 (Lighthouse a11y 95-96점)
- skip-to-content 링크, `aria-current`, `aria-label`, focus-visible outline 모두 적용

## 라이선스

회사 소유 콘텐츠. 외부 사용 시 별도 문의: `contact@object.so`.

폰트: Pretendard (Open Font License 1.1, [github.com/orioncactus/pretendard](https://github.com/orioncactus/pretendard))
컬러: Open Color (MIT, [yeun.github.io/open-color](https://yeun.github.io/open-color/))
