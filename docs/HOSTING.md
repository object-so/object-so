# 호스팅 가이드

이 사이트는 **Eleventy 3.x로 빌드되어 AWS S3 + CloudFront로 서빙**됩니다. 빌드·배포·검증 전 과정이 GitHub Actions에서 자동 실행됩니다.

## 배포 파이프라인

```
git push (main)
   │
   ▼
.github/workflows/deploy.yml  (~60-90초)
   │
   ├─ Checkout
   ├─ Set up Node.js 20
   ├─ npm ci || npm install
   ├─ npm run build              → _site/ 생성 (29 files)
   ├─ Configure AWS via OIDC
   ├─ python3 scripts/check-hreflang.py   _site/ 기준 hreflang/canonical/sitemap 검증
   ├─ S3 sync (5 분리 단계, 자산별 cache-control 차등)
   ├─ CloudFront create-invalidation /*
   ├─ Wait for invalidation completion
   └─ Smoke test (8 routes via apex IP, 2xx/3xx 검증)
```

## AWS 리소스

| 자원 | 식별자 |
|---|---|
| S3 버킷 | `object-so-200247611510-ap-northeast-2-an` |
| CloudFront 배포 | `E3GUZ9POF885VR` |
| AWS 리전 | `ap-northeast-2` (서울) |
| 배포용 IAM 역할 | `arn:aws:iam::200247611510:role/object-so-deploy` (GitHub OIDC trust) |

식별자는 `.github/workflows/deploy.yml`의 `env` 블록에서 일괄 관리. 도메인/계정 변경 시 그 한 곳만 갱신.

## 캐시 정책

deploy.yml이 자산 종류별로 다른 `Cache-Control`을 설정합니다.

| 자산 | max-age | 비고 |
|---|---:|---|
| `assets/fonts/*.otf` | 1년 (immutable) | 파일명 변경 거의 없음 |
| `assets/img/*` | 30일 | favicon/OG/로고 |
| `assets/css/*` | 7일 | 변경 잦으면 query-string 버스팅 검토 |
| `*.html` (KO/EN/index) | 1시간 | 콘텐츠 즉시 반영을 위해 비교적 짧게 |
| `robots.txt`, `sitemap.xml`, `app-ads.txt` | no-cache | 검색엔진/크롤러 즉시 반영 |

매 배포마다 CloudFront `/*` invalidation이 트리거되므로 사용자는 다음 첫 요청에서 신규 콘텐츠를 받음.

## 루트 `/` 분기

`index.html`이 클라이언트에서 `navigator.languages`를 보고 `/ko/index.html` 또는 `/en/index.html`로 `location.replace`. JS 비활성 환경은 `<meta http-equiv="refresh">`로 KO 폴백.

서버 사이드 redirect(CloudFront Function)는 도입하지 않음 — 빈도가 낮은 라우트라 코드/운영 복잡도가 비용 대비 가치 적음.

## OIDC 설정 (참고)

GitHub Actions가 AWS에 접근할 때 long-lived access key 대신 OIDC token을 사용합니다.

1. AWS IAM → Identity providers에 `token.actions.githubusercontent.com` 추가
2. `object-so-deploy` 역할에 trust policy 작성 — `repo:object-so/object-so:ref:refs/heads/main` 만 신뢰
3. 역할 권한:
   - `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` on `object-so-200247611510-ap-northeast-2-an`
   - `cloudfront:CreateInvalidation`, `cloudfront:GetInvalidation` on `E3GUZ9POF885VR`

`deploy.yml`의 `aws-actions/configure-aws-credentials@v4` 액션이 자동으로 OIDC token을 받아 임시 자격증명으로 교환.

## smoke 테스트

deploy.yml 마지막 단계가 `dig @8.8.8.8`으로 apex IP를 받아 `--resolve`로 직접 요청 (CI runner DNS 캐시 우회). 검증 라우트:

- `/`, `/ko/`, `/en/`
- `/ko/contact.html`, `/en/contact.html`
- `/sitemap.xml`, `/robots.txt`, `/app-ads.txt`

각 응답이 2xx/3xx가 아니면 워크플로 fail.

## 로컬 빌드 검증

```bash
npm run clean && npm run build
npm run check:hreflang   # _site/ 기준 hreflang/canonical/sitemap 일관성
npm run check:json-ld    # 모든 _site/*.html JSON-LD JSON 파싱

# diff 검증 (이전 빌드와 비교)
diff -wB <(git show HEAD~1:ko/index.html) _site/ko/index.html
```

## 도메인 전환

운영 도메인이 `object.so`가 아니면 다음 두 곳을 갱신:

```bash
# 1) Eleventy 데이터의 baseUrl
sed -i '' 's|https://object.so|https://example.com|g' _data/site.js

# 2) JSON-LD 파셜과 privacy md 본문에 절대 URL 하드코딩
grep -l 'object.so' _includes/partials/jsonld-*.njk content/legal/*.md \
  | xargs sed -i '' 's|https://object.so|https://example.com|g'
```

확인:

```bash
npm run build
grep -r 'object.so' _site/    # 결과가 비어 있어야 함
```

GitHub Actions 인프라 변경 (S3 버킷·CloudFront 배포·OIDC role)은 `deploy.yml`의 `env` 블록과 IAM trust policy를 함께 갱신.

## 다른 호스팅 플랫폼

S3+CloudFront 외 환경에서 같은 `_site/` 산출물을 쓸 때 참고할 패턴 (운영은 안 함, 인수용):

### Cloudflare Pages

```
# _redirects (프로젝트 루트)
/  /ko/index.html  302
```

Accept-Language 분기는 Pages Functions로:

```ts
export const onRequest: PagesFunction = async ({ request, next }) => {
  const url = new URL(request.url);
  if (url.pathname === "/" || url.pathname === "/index.html") {
    const accept = (request.headers.get("accept-language") || "").toLowerCase();
    return Response.redirect(new URL(accept.startsWith("ko") ? "/ko/index.html" : "/en/index.html", request.url), 302);
  }
  return next();
};
```

### Netlify

```
# _redirects
/  /ko/index.html  302  Language=ko
/  /en/index.html  302  Language=en
/  /ko/index.html  302
```

### Vercel

```json
{
  "redirects": [
    { "source": "/", "destination": "/ko/index.html", "permanent": false }
  ]
}
```

### nginx (직접 운영)

```nginx
server {
  listen 443 ssl http2;
  server_name object.so;
  root /var/www/object-so/_site;
  index index.html;

  types {
    image/svg+xml svg;
    font/otf otf;
  }

  location /assets/fonts/ { expires 1y; add_header Cache-Control "public, immutable"; }
  location /assets/img/   { expires 30d; }
  location /assets/css/   { expires 7d; }

  location = / {
    if ($http_accept_language ~* "^ko") { return 302 /ko/index.html; }
    return 302 /en/index.html;
  }

  location / { try_files $uri $uri/ =404; }

  location = /robots.txt  { add_header Cache-Control "no-cache"; }
  location = /sitemap.xml { add_header Cache-Control "no-cache"; }
}
```

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| Deploy workflow 실패: `AccessDenied: assume role` | OIDC trust policy의 `sub` 패턴이 ref를 허용하는지 확인 (현재는 `refs/heads/main`만 허용) |
| Smoke test에서 일부 라우트 5xx | CloudFront origin path 설정·S3 버킷 정책 확인. invalidation 완료 전 캐시 mismatch 가능 |
| 라이브 콘텐츠가 갱신되지 않음 | 브라우저 cache 또는 CDN edge 캐시. 강제 새로고침 또는 `aws cloudfront create-invalidation` 수동 실행 |
| `npm run check:hreflang` 실패 | 빌드 산출물(`_site/`) 부재. `npm run build` 먼저 |
