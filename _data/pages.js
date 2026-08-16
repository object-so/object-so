// Page registry for sitemap.xml generation.
// Add a new entry when adding a new page; sitemap auto-updates on next build.
//
// Each entry is rendered for both languages (ko + en). hreflang alternates
// (ko / en / x-default) and the canonical loc are derived from {slug, lang}.
export default [
  { slug: "index",   priority: "1.0", changefreq: "monthly" },
  { slug: "about",   priority: "0.8", changefreq: "monthly" },
  { slug: "contact", priority: "0.6", changefreq: "monthly" },
  { slug: "products",    priority: "0.8", changefreq: "monthly" },
  { slug: "dailysudoku", priority: "0.8", changefreq: "monthly" },
  { slug: "privacy", priority: "0.3", changefreq: "yearly", lastmod: "2026-04-01" },
  { slug: "terms",   priority: "0.3", changefreq: "yearly", lastmod: "2026-08-16" },
];
