# 호스팅 가이드

이 사이트는 빌드 도구 없이 정적 HTML로 동작합니다. 어떤 정적 호스팅에서도 작동하지만, **루트(`/`) 진입 시 언어 분기**는 호스팅에 따라 처리 방법이 다릅니다.

## 폴더 구조

```
/
├── index.html        ← 루트 라우터 (JS + meta refresh 폴백)
├── ko/{index,about,contact,privacy}.html
├── en/{index,about,contact,privacy}.html
├── assets/{css,fonts,img}/...
├── robots.txt
└── sitemap.xml
```

## 루트 분기 전략

기본 동작: `/index.html`이 클라이언트에서 `navigator.languages`를 보고 `/ko/` 또는 `/en/`으로 `location.replace`. JS 비활성 환경은 `<meta http-equiv="refresh">`로 KO 폴백.

**서버 사이드 redirect를 권장하는 이유:**
- 빠름 (HTML 한 라운드트립 절약)
- SEO 친화 (검색엔진이 301/302를 더 잘 이해)
- `Accept-Language` 헤더로 정확한 분기 (클라 JS는 한국 사용자가 영어 시스템 쓸 때 EN으로 보내질 수 있음 — KO 우선이면 일부러 KO 폴백 가능)

서버 사이드 redirect를 켜도 `/index.html`은 그대로 두세요. 일부 봇/오프라인 환경의 안전망입니다.

---

## 호스팅별 패턴

### Cloudflare Pages

#### 단순 분기 — KO만 기본
프로젝트 루트에 `_redirects` 파일 생성:
```
/  /ko/index.html  302
```

#### Accept-Language 분기 (Pages Functions)
`functions/_middleware.ts`:
```ts
export const onRequest: PagesFunction = async ({ request, next }) => {
  const url = new URL(request.url);
  if (url.pathname === "/" || url.pathname === "/index.html") {
    const accept = (request.headers.get("accept-language") || "").toLowerCase();
    const target = accept.startsWith("ko") ? "/ko/index.html" : "/en/index.html";
    return Response.redirect(new URL(target, request.url), 302);
  }
  return next();
};
```

### Netlify

`_redirects` (Netlify는 Language 매처 지원):
```
/  /ko/index.html  302  Language=ko
/  /en/index.html  302  Language=en
/  /ko/index.html  302
```
또는 단순 분기:
```
/  /ko/index.html  302
```

### Vercel

`vercel.json`:
```json
{
  "redirects": [
    { "source": "/", "destination": "/ko/index.html", "permanent": false }
  ]
}
```

Edge Middleware로 Accept-Language 분기 (`middleware.ts`):
```ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export const config = { matcher: ["/", "/index.html"] };

export function middleware(req: NextRequest) {
  const accept = (req.headers.get("accept-language") || "").toLowerCase();
  const target = accept.startsWith("ko") ? "/ko/index.html" : "/en/index.html";
  return NextResponse.redirect(new URL(target, req.url), 302);
}
```

### GitHub Pages

서버 redirect 미지원. 루트 `index.html`의 JS+meta refresh 그대로 사용. 추가 작업 없음.

### AWS S3 + CloudFront

CloudFront Function (Viewer Request) 또는 Lambda@Edge. 단순 분기:
```js
function handler(event) {
  var req = event.request;
  if (req.uri === "/" || req.uri === "/index.html") {
    var accept = (req.headers["accept-language"] && req.headers["accept-language"].value || "").toLowerCase();
    var target = accept.indexOf("ko") === 0 ? "/ko/index.html" : "/en/index.html";
    return {
      statusCode: 302,
      statusDescription: "Found",
      headers: { location: { value: target } }
    };
  }
  return req;
}
```

S3 단독 호스팅 시 redirect rule (S3 콘솔 → Properties → Static website hosting → Redirection rules):
```xml
<RoutingRules>
  <RoutingRule>
    <Condition><KeyPrefixEquals>index.html</KeyPrefixEquals></Condition>
    <Redirect><ReplaceKeyWith>ko/index.html</ReplaceKeyWith><HttpRedirectCode>302</HttpRedirectCode></Redirect>
  </RoutingRule>
</RoutingRules>
```

### nginx (직접 운영)

```nginx
server {
  listen 443 ssl http2;
  server_name object.so;
  root /var/www/object-so;
  index index.html;

  # MIME (svg/otf 누락 방지)
  types {
    image/svg+xml svg;
    font/otf otf;
  }

  # 폰트·이미지 long-cache
  location /assets/fonts/ { expires 1y; add_header Cache-Control "public, immutable"; }
  location /assets/img/   { expires 30d; add_header Cache-Control "public"; }
  location /assets/css/   { expires 7d;  add_header Cache-Control "public"; }

  # 루트 분기
  location = / {
    if ($http_accept_language ~* "^ko") { return 302 /ko/index.html; }
    return 302 /en/index.html;
  }

  # 콘텐츠 페이지
  location / {
    try_files $uri $uri/ =404;
  }

  # robots / sitemap (cache 없이)
  location = /robots.txt  { add_header Cache-Control "no-cache"; }
  location = /sitemap.xml { add_header Cache-Control "no-cache"; }
}
```

---

## 도메인 전환 시 주의사항

운영 도메인이 `object.so`가 아니면 다음 위치를 일괄 치환해야 합니다:

```bash
# 모든 페이지의 절대 URL (canonical, OG, hreflang)
grep -rl 'https://object.so' . --include='*.html' --include='*.xml' --include='*.txt'

# 일괄 치환 예시 (object.so → example.com)
find . -type f \( -name '*.html' -o -name '*.xml' -o -name '*.txt' \) \
  -exec sed -i '' 's|https://object\.so|https://example.com|g' {} +
```

치환 대상:
- `<link rel="canonical">`, `<link rel="alternate" hreflang="...">`
- `<meta property="og:url">`, `<meta property="og:image">`
- `sitemap.xml`의 `<loc>`, `<xhtml:link>`
- `robots.txt`의 `Sitemap:`

---

## 캐시 정책 권장

| 자산 | 권장 max-age | 비고 |
|---|---|---|
| `assets/fonts/*.otf` | 1년 (immutable) | 폰트 변경 거의 없음 |
| `assets/img/*` | 30일 | favicon/OG는 자주 바뀌지 않음 |
| `assets/css/*` | 7일 | 변경 잦으면 query-string 버스팅 |
| `*.html` | 1시간 또는 no-cache | 콘텐츠 즉시 반영 우선 |
| `robots.txt`, `sitemap.xml` | no-cache | 검색엔진 즉시 반영 |
