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
├── ko/, en/                         # 언어별 index/about/contact 페이지
├── content/legal/                   # privacy markdown source
├── _data/
│   ├── site.js                      # baseUrl, 연락처, 사업자 정보, GA, sameAs
│   ├── i18n.js                      # 언어별 UI 문자열
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
├── scripts/
│   ├── check-hreflang.py            # sitemap 기반 canonical/hreflang 검증
│   └── check-json-ld.py             # sitemap 기반 JSON-LD 파싱 검증
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
2. sitemap에 등재된 HTML 페이지의 JSON-LD 파싱
3. sitemap, canonical, HTML hreflang 상호 일관성 검증

개별 실행도 가능합니다.

```bash
npm run check:json-ld
npm run check:hreflang
```

내부 링크/이미지/favicon 검증은 CI의 html-proofer가 담당합니다. 외부 링크 검사는 `.github/workflows/link-check.yml`에서 주 1회 별도 실행합니다.

## 페이지 추가

새 공개 페이지를 추가할 때는 KO/EN 쌍을 같이 추가합니다.

1. `ko/<slug>.html`, `en/<slug>.html` 생성
2. front matter에 `layout`, `permalink`, `lang`, `slug`, `title`, `description` 지정
3. navigation에 필요하면 `_data/i18n.js`, `_includes/partials/header.njk`, `_includes/partials/footer.njk` 수정
4. sitemap 대상이면 `_data/pages.js`에 `{ slug, priority, changefreq, lastmod? }` 추가
5. `npm run check:seo`

`head-meta.njk`가 canonical, hreflang, OG/Twitter, icon, CSS preload를 생성합니다. `jsonld.njk`는 Organization/WebSite와 하위 페이지 BreadcrumbList를 생성합니다.

## Privacy 정책 수정

소스는 Markdown입니다.

```text
content/legal/privacy-policy-ko.md
content/legal/privacy-policy-en.md
```

시행일을 바꾸면 본문과 함께 `_data/pages.js`의 `privacy.lastmod`도 갱신합니다. 법적 효력 기준은 한국어 버전입니다.

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
