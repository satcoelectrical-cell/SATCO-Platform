import { readFileSync } from "node:fs";
const css = readFileSync("src/styles.css", "utf8");

describe("responsive and accessibility-critical styling", () => {
  it("defines a twelve-column primary surface with a desktop AI rail and safe collapse", () => { expect(css).toContain("grid-template-columns:repeat(12"); expect(css).toContain('data-default-composition="true"'); expect(css).toContain("grid-template-areas"); expect(css).toContain("assistant assistant assistant assistant"); expect(css).toContain("@media (max-width:1199px)"); expect(css).toContain("grid-template-areas:none"); expect(css).toContain("@media (max-width:759px)"); expect(css).toContain("grid-template-columns:1fr"); });
  it("preserves visible focus, reduced motion and contained narrow navigation", () => { expect(css).toContain(":focus-visible"); expect(css).toContain("prefers-reduced-motion"); expect(css).toContain("translateX(-102%)"); });
  it("stacks the Customer-to-Capture bootstrap without horizontal workflow overflow", () => { expect(css).toContain(".bootstrap-grid"); expect(css).toMatch(/\.bootstrap-grid \{ display:grid; grid-template-columns:repeat\(2/); expect(css).toMatch(/\.bootstrap-grid \{ grid-template-columns:1fr/); });
  it("does not depend on remote visual assets or fonts", () => { expect(css).not.toMatch(/@import|url\(['\"]?https?:/); });
  it("stacks Project Context and related records direction-neutrally",()=>{expect(css).toContain(".project-context-grid");expect(css).toMatch(/\.project-context-grid\{grid-template-columns:1fr/);expect(css).toContain(".related-context");expect(css).not.toMatch(/\.project-context[^}]*\b(left|right):/);});
});
