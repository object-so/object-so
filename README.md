# object-so

오브젝트(Object) 회사 소개 사이트. Eleventy 기반 정적 사이트이며 한국어와 영어 페이지를 `https://object.so`에서 제공합니다.

## 현재 구성

| 영역 | 내용 |
|---|---|
| 사이트 빌더 | Eleventy 3.x, Nunjucks, Markdown |
| 런타임 | 정적 HTML/CSS/이미지/폰트 |
| 언어 | `ko`, `en` |
| 호스팅 | AWS S3 + CloudFront |
| 배포 | `main` push 시 GitHub Actions OIDC로 자동 배포 |
| 검색/공유 | canonical, hreflang, sitemap, robots, Open Graph, Twitter Card, JSON-LD, `llms.txt` |
| 폰트 | self-hosted `PretendardStdVariable.woff2` |

## 주요 파일

```text
.
├── 404.html                         # noindex, follow 404 fallback
├── index.html                       # root language redirect shell, noindex
├── ko/, en/                         # 언어별 index/about/contact/products/dailysudoku 페이지
├── content/legal/                   # privacy·terms 소스 (확장자는 .md지만 내용은 HTML)
├── _data/
│   ├── site.js                      # baseUrl, 연락처, 사업자 정보, GA, sameAs
│   ├── i18n.js                      # 언어별 UI 문자열 + pageNames(breadcrumb 항목명)
│   ├── pages.js                     # sitemap 대상 페이지 registry
│   └── values.js                    # 홈 value 카드 데이터
├── _includes/
│   ├── layouts/base.njk             # 일반 페이지 layout
│   ├── layouts/redirect.njk         # root redirect layout
│   └── partials/
│       ├── head-meta.njk            # title, description, canonical, hreflang, OG/Twitter
│       ├── jsonld.njk               # Organization, WebSite, BreadcrumbList
│       ├── header.njk
│       ├── footer.njk
│       └── analytics.njk
├── assets/css/                      # tokens.css, site.css
├── assets/fonts/                    # Pretendard variable font
├── assets/img/                      # favicon, logo, OG image
├── assets/img/badges/               # Apple·Google 공식 스토어 뱃지 (수정 금지, 아래 참고)
├── assets/img/products/             # 제품 아이콘·스크린샷 (WebP)
├── scripts/
│   ├── check-hreflang.py            # sitemap 기반 canonical/hreflang 검증
│   ├── check-json-ld.py             # JSON-LD 파싱 + BreadcrumbList 항목명 검증
│   ├── check-badges.py              # 스토어 뱃지 벤더 규정 검증
│   └── check-nav-overflow.py        # nav 오버플로 불변식 + 햄버거 마크업 검증
├── sitemap.njk                      # _data/pages.js -> /sitemap.xml
├── robots.txt
├── app-ads.txt
├── llms.txt
└── docs/HOSTING.md                  # AWS 배포 상세
```

`_site/`는 빌드 산출물이며 git에 커밋하지 않습니다.

## 빠른 시작

```bash
npm install
npm run dev
```

로컬 서버는 기본적으로 `http://localhost:8080`입니다.

## 빌드와 검증

```bash
npm run build
npm run check:seo
```

`check:seo`는 다음을 한 번에 실행합니다.

1. Eleventy build
2. sitemap에 등재된 HTML 페이지의 JSON-LD 파싱 + BreadcrumbList 항목명 검증
3. sitemap, canonical, HTML hreflang 상호 일관성 검증
4. 스토어 뱃지 벤더 규정 검증 (자산 무결성·종횡비·순서·귀속 문구·clear space)
5. nav 오버플로 불변식 + 햄버거 마크업 + noscript 폴백 검증

개별 실행도 가능합니다.

```bash
npm run check:json-ld
npm run check:hreflang
npm run check:badges
npm run check:nav
```

> ⚠️ `check:seo`는 **레이아웃 오버플로를 잡지 못합니다.** 헤더나 폭에 영향을 주는 변경을 했다면 브라우저로 **폭을 훑어야** 합니다 — 320·360·375·390·414px 와 600~900px를 20px 간격으로, 14개 페이지 전부. 과거에 390px와 1440px 두 지점만 확인했다가 601~726px 구간 오버플로가 라이브로 나갔습니다. `check:nav`는 그 대신 «넘치더라도 문서가 아니라 링크 목록만 스크롤된다»는 CSS 불변식을 잠급니다.

내부 링크/이미지/favicon 검증은 CI의 html-proofer가 담당합니다. 외부 링크 검사는 `.github/workflows/link-check.yml`에서 주 1회 별도 실행합니다.

## 페이지 추가

새 공개 페이지를 추가할 때는 KO/EN 쌍을 같이 추가합니다.

1. `ko/<slug>.html`, `en/<slug>.html` 생성 — **반드시 쌍으로**. 헤더·푸터의 언어 토글이 `../{lang}/{slug}.html`을 무조건 만들어서 한쪽만 있으면 404가 납니다.
2. front matter에 `layout`, `permalink`, `lang`, `slug`, `title`, `description` 지정. 3단계 breadcrumb이 필요하면 `parent: <상위 slug>`도 지정합니다.
3. **`_data/i18n.js`의 `pageNames`에 slug 추가** — 빠뜨리면 breadcrumb 항목명이 page `<title>`로 채워집니다. `check:json-ld`가 이걸 잡습니다.
4. navigation에 필요하면 `_data/i18n.js`의 `nav`, `_includes/partials/header.njk`(**index 분기와 non-index 분기 양쪽**), `_includes/partials/footer.njk` 수정
5. sitemap 대상이면 `_data/pages.js`에 `{ slug, priority, changefreq, lastmod? }` 추가
6. `llms.txt`에 KO/EN 한 줄씩 추가 (passthrough라 수동)
7. `npm run check:seo`

`head-meta.njk`가 canonical, hreflang, OG/Twitter, icon, CSS preload를 생성합니다. `jsonld.njk`는 Organization/WebSite와 하위 페이지 BreadcrumbList를 생성하고, front matter에 `app:` 블록이 있으면 `SoftwareApplication` 노드도 냅니다.

## 법무 문서 수정 (privacy · terms)

```text
content/legal/privacy-policy-ko.md   content/legal/terms-of-service-ko.md
content/legal/privacy-policy-en.md   content/legal/terms-of-service-en.md
```

> **본문은 Markdown이 아니라 HTML입니다.** front matter의 `templateEngineOverride: njk` 때문에 markdown-it 파이프라인을 타지 않습니다. `##` 같은 마크다운 문법을 쓰면 **빌드도 `check:seo`도 통과한 채** 페이지에 원문 그대로 찍힙니다. `.priv-section` 구조를 그대로 따라 쓰세요.

이용약관은 공정거래위원회 「전자상거래(인터넷사이버몰) 표준약관」 제10023호(2015. 6. 26. 개정)를 준용하며 조 번호·제목 체계를 유지합니다. 시행일을 바꾸면 본문과 함께 `_data/pages.js`의 `lastmod`도 갱신합니다. 법적 효력 기준은 한국어 버전입니다.

## 헤더 내비게이션

`767px` 이하에서 헤더 링크가 햄버거 뒤로 접힙니다. **모바일 전용 마크업은 없습니다** — 같은 DOM을 CSS로 재배치합니다.

- 브레이크포인트는 `@media`가 아니라 **`@container (max-width: 767px)`** 입니다. 운영에서 `.nav`는 뷰포트 전체 폭이라 둘이 같은 지점에서 켜지지만, Claude Design 캔버스는 항상 넓게 렌더돼 미디어쿼리로는 모바일 헤더를 프로토타입에서 볼 방법이 없습니다. 컨테이너 기준이면 헤더를 390px 상자에 넣는 것만으로 같은 CSS가 재현되어, 스펙 화면용 규칙을 복제하지 않아도 됩니다. `.nav`의 `container-type: inline-size`가 이 전제입니다 — 지우면 `@container`가 영원히 매칭되지 않아 **햄버거가 조용히 죽습니다**(`check:nav`가 막습니다).
- 브레이크포인트 767px의 근거는 실측입니다: `/en/index.html`의 nav가 데스크톱 규칙에서 **726px**를 요구합니다.
- `.nav-links`의 `min-width: 0` / `overflow-x: auto`는 **미디어쿼리 밖에** 있어야 합니다. 이게 안전망이라 브레이크포인트 위에서 항목이 늘어도 실패 모드가 «문서 가로 스크롤»이 아니라 «링크 목록 내부 스크롤»이 됩니다.
- 언어 토글은 패널로 들어가지 않고 바에 남습니다. 메뉴를 열지 않아도 전환이 보이고, 모바일 바는 ≈222px라 320px에서도 여유가 있습니다.
- JS가 없으면 `base.njk` head의 `<noscript><style>`이 기존 가로 스크롤 nav로 되돌립니다. 토글만 죽고 내비게이션 전체에 도달할 수 없게 되는 상태를 만들지 않습니다.

nav 항목을 추가할 때는 `_data/i18n.js`의 `nav`, `header.njk`의 **양쪽 분기**, 그리고 위 폭 스윕을 함께 봅니다.

## 스토어 뱃지 (Apple · Google)

`assets/img/badges/`의 SVG는 **벤더 공식 아트워크를 바이트 그대로** 보관합니다. SVG 최적화·리사이즈·재인코딩은 전부 벤더 가이드라인 위반이며, `check:badges`가 SHA-256으로 막습니다.

- 출처 — Apple: [뱃지 API](https://toolbox.marketingtools.apple.com/api/v2/badges/download-on-the-app-store/black/ko-kr) (공식 다운로드 묶음과 바이트 동일) · Google: [파트너 마케팅 허브](https://partnermarketinghub.withgoogle.com/brands/google-play/google-play/lockups-icons-badges/) 묶음의 `Digital/svg`
- 규격 — 높이 44px(Apple 최소 40) + 로케일별 `aspect-ratio`(= 각 SVG의 viewBox), clear space는 래퍼 패딩 11px(= 높이 ÷ 4), 뱃지 간 `gap: 8px`
- 규정 — App Store 뱃지가 **먼저**, Play 뱃지는 Apple과 **같거나 크게**, 상표 귀속 문구는 사이트에 **한 번만**
- 벤더 CDN 핫링크 금지 — 방문자 IP·UA·Referer가 페이지 로드 시점에 Apple/Google로 나갑니다

`gap`은 0일 수 없습니다. 포커스 아웃라인이 보더 박스 바깥 4px에 그려져서, 0이면 포커스할 때마다 옆 뱃지의 clear space를 침범합니다. `.badge-link`에 배경색을 주는 것도 같은 이유로 금지입니다(배경은 패딩 박스를 칠합니다).

## SEO와 crawler-facing 산출물

- `/ko/*.html`, `/en/*.html`: indexable content pages
- `/index.html`: 언어 분기용 root shell, `noindex`
- `/404.html`: fallback page, `noindex, follow`, sitemap 제외
- `/sitemap.xml`: `_data/pages.js`에서 생성, KO/EN alternate 포함
- `/robots.txt`: sitemap 위치 안내, root shell `/index.html` disallow
- `/llms.txt`: LLM/agent용 사이트 요약과 핵심 링크
- `naver*.html`: 검색 소유권 확인 파일, root로 passthrough
- `/app-ads.txt`: 광고 생태계 확인 파일

canonical URL은 `https://object.so/{lang}/{slug}.html` 형식입니다. `x-default`는 한국어 URL을 가리킵니다.

## CI와 배포

| Workflow | Trigger | 역할 |
|---|---|---|
| `ci.yml` | push, PR, manual | install, `npm run check:seo`, html-proofer internal check |
| `deploy.yml` | `main` push, manual | build, AWS OIDC, S3 sync, CloudFront invalidation, live smoke test |
| `link-check.yml` | weekly, manual | 외부 링크 health check, 실패 시 issue 생성 |

배포 리소스는 `.github/workflows/deploy.yml`의 `env` 블록에서 관리합니다.

- AWS region: `ap-northeast-2`
- S3 bucket: `object-so-200247611510-ap-northeast-2-an`
- CloudFront distribution: `E3GUZ9POF885VR`

더 자세한 운영 메모는 [docs/HOSTING.md](./docs/HOSTING.md)를 봅니다.

## 변경 전 체크리스트

```bash
git status -sb
npm run check:seo
git diff --check
```

`main`에 push하면 CI와 배포가 모두 실행됩니다. 배포 완료 후 라이브 확인이 필요하면 다음 표면을 우선 봅니다.

```bash
curl -I https://object.so/404.html
curl -I https://object.so/sitemap.xml
curl -I https://object.so/robots.txt
curl -I https://object.so/llms.txt
```

## Git ignore 정책

커밋 대상은 소스와 운영 설정입니다. 아래는 로컬 생성물로 취급합니다.

- `_site/`
- `node_modules/`
- `.claude/`, `.codex/`, `.serena/`, `.codegraph/`, `graphify-out/`
- Python cache (`__pycache__/`, `*.pyc`)
- editor, OS, log, env 파일

## 라이선스

사이트 콘텐츠는 오브젝트 소유입니다. 외부 사용 문의: `contact@object.so`

외부 자산 라이선스:

- Pretendard: SIL Open Font License 1.1
- Open Color 기반 색상 토큰: MIT
