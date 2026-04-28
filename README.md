# object-so

오브젝트(Object) 회사 소개 사이트 — Eleventy 기반 정적 사이트, KO·EN 다국어.

> 단일 목적의 앱과 서비스를 만드는 1인 소프트웨어 공방. 페이지는 작고, 카피는 짧고, 타이포는 단단하게.

라이브: <https://object.so>

## 기술 스택

| 영역 | 도구 |
|---|---|
| 정적 사이트 빌더 | [Eleventy](https://www.11ty.dev) 3.x (Nunjucks 템플릿) |
| 콘텐츠 모델 | front matter + `_includes/layouts` + `_data/{site,i18n,pages}.js` |
| 호스팅 | AWS S3 + CloudFront (KR ap-northeast-2) |
| 배포 | GitHub Actions OIDC (`.github/workflows/deploy.yml`) — push to `main` 시 자동 |
| 검증 | hreflang/canonical/sitemap 일관성 + JSON-LD 파싱 + html-proofer 내부 링크 |
| 폰트 | [Pretendard](https://github.com/orioncactus/pretendard) 9 weights (self-hosted OTF) |
| 컬러 | [Open Color](https://yeun.github.io/open-color/) 회색 + 단일 액센트(blue-6) |

## 폴더 구조

```
object-so/
├── _data/                       Eleventy 전역 데이터 (모든 템플릿에서 접근)
│   ├── site.js                  baseUrl · email · 사업자등록번호
│   ├── i18n.js                  KO/EN 공통 문자열 (nav 라벨 · aria-label · locale)
│   └── pages.js                 sitemap 페이지 등록부 (slug · priority · changefreq · lastmod)
├── _includes/                   Nunjucks 레이아웃 + 파셜
│   ├── layouts/
│   │   ├── base.njk             KO/EN 페이지 골격 (head + body + script)
│   │   └── redirect.njk         루트 / 페이지의 언어 분기 셸
│   └── partials/
│       ├── head-meta.njk        title · canonical · hreflang · OG · twitter · icon · css
│       ├── header.njk           nav + KO|EN 토글
│       ├── footer.njk           회사 정보 + privacy 링크 + KO|EN 토글
│       └── jsonld-{ko,en}-org.njk  index 페이지 Organization JSON-LD
├── content/legal/               privacy 페이지 source-of-truth
│   ├── privacy-policy-ko.md  →  _site/ko/privacy.html
│   └── privacy-policy-en.md  →  _site/en/privacy.html
├── ko/, en/                     index · about · contact (front matter + <main>만)
├── index.html                   루트 / — 언어 분기 redirect (noindex)
├── sitemap.njk                  _data/pages.js → _site/sitemap.xml 자동 생성
├── assets/
│   ├── css/{tokens,site}.css    디자인 토큰 + 페이지 스타일
│   ├── fonts/Pretendard-*.otf
│   └── img/{favicon*,apple-touch-icon,og-1200x630,logo,wordmark}
├── docs/HOSTING.md              호스팅·배포 상세 가이드
├── scripts/check-hreflang.py    hreflang/canonical/sitemap 일관성 검사 (_site/ 기준)
├── .github/workflows/
│   ├── ci.yml                   PR/push 검증 (build → JSON-LD/sitemap/hreflang/html-proofer)
│   └── deploy.yml               main push 시 빌드·S3 sync·CloudFront invalidate·smoke
├── eleventy.config.js
├── package.json, package-lock.json
├── robots.txt, app-ads.txt
└── _site/                       빌드 산출물 (gitignore)
```

## 빠른 시작

```bash
npm install
npm run dev      # http://localhost:8080 라이브 리로드
npm run build    # _site/ 산출
npm run clean    # _site/ 삭제
```

검증:

```bash
npm run check:hreflang   # hreflang/canonical/sitemap 일관성 (build 필요)
npm run check:json-ld    # 모든 페이지의 JSON-LD JSON 파싱 검사
```

## 콘텐츠 작업

### 새 페이지 추가

예: `/ko/works.html` 추가

1. `ko/works.html` 생성:
   ```yaml
   ---
   layout: layouts/base.njk
   permalink: /ko/works.html
   lang: ko
   slug: works
   activeNav: works           # nav에 표시할 경우, 없으면 생략
   title: "작업 · 오브젝트"
   description: "오브젝트가 만든 앱들."
   ---
     <main class="page" id="main" tabindex="-1">
       <div class="wrap">
         <h1 class="display">작업<span class="accent" aria-hidden="true">.</span></h1>
         …
       </div>
     </main>
   ```
2. `en/works.html`도 동일 패턴 (lang: en, EN 콘텐츠).
3. `_data/i18n.js`의 `nav.works`에 KO/EN 라벨 추가, `_includes/partials/header.njk`에 `<a href="works.html">…</a>` 추가.
4. `_data/pages.js`에 한 줄 추가:
   ```js
   { slug: "works", priority: "0.7", changefreq: "monthly" },
   ```
5. push → CI → Deploy → smoke test (8개 라우트 검증 자동).

`<head>`/header/footer는 layout이 처리하니 손댈 필요 없음. canonical/hreflang/OG/JSON-LD는 front matter (`slug`, `lang`, `title`, `description`)만으로 자동 생성됨.

### privacy 정책 수정

`content/legal/privacy-policy-{ko,en}.md` 한 곳만 편집. 빌드가 `/_site/{ko,en}/privacy.html`로 렌더. 시행일 갱신 시:

1. md 본문의 `<div class="privacy-meta">` (시행일/Effective)
2. `_data/pages.js`의 `privacy.lastmod`

법적 효력 기준은 **한국어** 버전. 영문은 참고용.

### 사이트 메타 변경 (이메일·주소·사업자번호)

`_data/site.js` (전역) 또는 `_data/i18n.js` (언어별 라벨) 수정. 모든 푸터·JSON-LD가 자동 반영.

### 도메인 전환 (object.so → 다른 도메인)

```bash
# baseUrl만 _data/site.js에서 바꾸면 사실상 끝
sed -i '' 's|https://object.so|https://example.com|g' _data/site.js

# JSON-LD 파셜에 absolute URL 하드코딩이 있으니 그것도 함께
grep -l 'object.so' _includes/partials/jsonld-*.njk content/legal/*.md \
  | xargs sed -i '' 's|https://object.so|https://example.com|g'
```

deploy.yml의 `S3_BUCKET`, `CF_DISTRIBUTION_ID`, `AWS_ROLE_ARN` 등 인프라 식별자도 별도 갱신 필요. 자세한 내용은 `docs/HOSTING.md`.

## 디자인 시스템

- **컬러**: [Open Color](https://yeun.github.io/open-color/) 회색 파운데이션 + 단일 액센트(blue-6 `#228be6`)
- **타이포**: [Pretendard](https://github.com/orioncactus/pretendard) (KR + Latin), `font-display: swap`. 가장 큰 LCP 후보(Regular/ExtraBold)는 preload
- **간격**: 4px 그리드, `--space-*` 토큰
- **다크 모드**: `prefers-color-scheme: dark` 자동 분기. `<body class="theme-light">` 부여 시 강제 light
- **모션**: `prefers-reduced-motion: reduce` 시 transition/animation 비활성

토큰 정의 → `assets/css/tokens.css`. 페이지 스타일 → `assets/css/site.css`.

## 페이지 메타데이터 컨벤션

레이아웃이 자동 생성하는 메타:

- `<title>`, `<meta name="description">`
- `<link rel="canonical">` = `https://object.so/{lang}/{slug}.html`
- `<link rel="alternate" hreflang="ko|en|x-default">` 트리오 (x-default는 항상 KO)
- `<meta property="og:*">` (type/site_name/locale/locale:alternate/title/description/url/image/image:width/height)
- `<meta name="twitter:card">`
- favicon, apple-touch-icon, theme-color (light/dark)
- Pretendard Regular/ExtraBold preload + tokens.css/site.css 로드

페이지별 front matter로 오버라이드 가능: `ogTitle`, `ogDescription`, `includeJsonLd`(JSON-LD 파셜 경로).

## CI · 배포

| Workflow | 트리거 | 단계 |
|---|---|---|
| `ci.yml` | PR · push | npm install → build → JSON-LD 파싱 → sitemap well-formed → hreflang 일관성 → html-proofer |
| `deploy.yml` | push to `main` | build → AWS OIDC → hreflang 검증 → S3 sync (`_site/`) → CloudFront invalidate → smoke test |

S3 / CloudFront 자세한 설정은 [`docs/HOSTING.md`](./docs/HOSTING.md).

## 접근성

- skip-to-content 링크, `aria-current="page"` (active nav · footer privacy 링크), `aria-label`, focus-visible outline 적용
- 색상 대비는 WCAG 2.1 AA 기준 axe-core 통과 (`--fg-4` 작은 텍스트 한정 디자이너 의도 유지)
- 다크 모드에서도 동일 대비 보장

## 라이선스

회사 소유 콘텐츠. 외부 사용 시 별도 문의: `contact@object.so`.

- 폰트: Pretendard — SIL Open Font License 1.1
- 컬러: Open Color — MIT
