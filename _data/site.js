// Site-wide metadata referenced by layouts/partials.
// Path-stable values that don't depend on language.
export default {
  baseUrl: "https://object.so",
  ogImagePath: "/assets/img/og-1200x630.png",
  email: "contact@object.so",
  bizRegNo: "113-59-00420",
  bizRegVerifyUrl: "https://www.ftc.go.kr/bizCommPop.do?wrkr_no=1135900420",
  mailOrderRegNo: "2019-부산북구-0492",
  gaMeasurementId: "G-35LJJKFE9K", // GA4 — loaded only in production builds (see partials/analytics.njk)
  // 공식 채널 — JSON-LD Organization.sameAs로 노출(엔티티 인식·지식 패널). 공개·소유 URL만.
  sameAs: [
    "https://github.com/object-so",
    "https://blog.object.so",
  ],
};
