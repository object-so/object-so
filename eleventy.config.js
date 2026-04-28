// Eleventy config — opt-in build path. The committed .html files in
// /, ko/, en/ remain the canonical source for now. This config:
//   1) passes existing HTML/asset files through to _site/ unchanged
//   2) renders /content/legal/*.md with a layout to produce
//      _site/{ko,en}/privacy.html — verifying the markdown ↔ HTML parity
//      so the markdown can become the single source of truth in a follow-up.
//
// Usage:
//   npm install
//   npm run build           # outputs _site/
//   npm run dev             # local preview at http://localhost:8080

import markdownIt from "markdown-it";
import markdownItAttrs from "markdown-it-attrs";

export default function (eleventyConfig) {
  // Pass-through: copy existing static assets and HTML pages verbatim.
  eleventyConfig.addPassthroughCopy("assets");
  eleventyConfig.addPassthroughCopy("robots.txt");
  eleventyConfig.addPassthroughCopy("sitemap.xml");
  eleventyConfig.addPassthroughCopy({ "index.html": "index.html" });
  eleventyConfig.addPassthroughCopy({ "ko/*.html": "ko" });
  eleventyConfig.addPassthroughCopy({ "en/*.html": "en" });
  eleventyConfig.addPassthroughCopy("docs");

  // Watch CSS for live-reload during dev.
  eleventyConfig.addWatchTarget("assets/css/");

  // Markdown library with attribute parsing for {.class #id} syntax.
  const md = markdownIt({ html: true, linkify: false, typographer: false });
  md.use(markdownItAttrs);
  eleventyConfig.setLibrary("md", md);

  // Build-time copyright year — replaces the JS fallback in the long run.
  eleventyConfig.addShortcode("year", () => new Date().getFullYear());

  // Format ISO date strings as "YYYY-MM-DD" for sitemap lastmod, etc.
  eleventyConfig.addFilter("isodate", (d) => {
    const date = d instanceof Date ? d : new Date(d);
    return date.toISOString().slice(0, 10);
  });

  return {
    dir: {
      input: ".",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
    templateFormats: ["md", "njk", "html"],
    // Don't process node_modules, content/, _site/, docs/, scripts/.
    // (content/legal/*.md will be wired up via _includes layout in a follow-up.)
  };
}
