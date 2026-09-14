import { readFileSync } from "node:fs";
import { render, screen } from "@testing-library/react";
import { StandardsStatePresentation } from "../components/StandardsStatePresentation";

it("presents state with text and a semantic label in RTL context", () => {
  render(<div dir="rtl"><StandardsStatePresentation state="standing_acknowledgement_required" /></div>);
  const state = screen.getByLabelText("Status: standing acknowledgement required");
  expect(state).toHaveTextContent("standing acknowledgement required");
  expect(state.closest("[dir=rtl]")).not.toBeNull();
});

it("sanitizes arbitrary state tokens before using a CSS class", () => {
  render(<StandardsStatePresentation state="Not Permitted<script>" />);
  const state = screen.getByLabelText("Status: Not Permitted<script>");
  expect(state.className).toBe("standards-state standards-state-not-permitted-script-");
});

it("uses narrow-viewport rules, logical RTL properties, and isolated LTR machine text", () => {
  const css = readFileSync("src/styles.css", "utf8");
  expect(css).toContain("@media(max-width:759px)");
  expect(css).toContain("border-inline-start");
  expect(css).toContain("padding-inline-start");
  expect(css).toContain("direction:ltr");
  expect(css).toContain("unicode-bidi:isolate");

  render(<div dir="rtl"><code dir="ltr">sha256:0123456789abcdef</code></div>);
  expect(screen.getByText("sha256:0123456789abcdef")).toHaveAttribute("dir", "ltr");
});
