import { defaultLayout, LAYOUT_KEY, loadLayout, saveLayout, validateLayout } from "../dashboard/layout";

describe("dashboard layout contract", () => {
  beforeEach(() => localStorage.clear());
  it("accepts the exact default registry", () => expect(validateLayout(defaultLayout)).toEqual(defaultLayout));
  it.each([null, {}, { version: 2, widgets: [] }, { version: 1, widgets: [] }, { version: 1, widgets: [...defaultLayout.widgets, defaultLayout.widgets[0]] }])("recovers malformed or stale state", (value) => expect(validateLayout(value)).toEqual(defaultLayout));
  it("rejects unknown fields and sizes", () => expect(validateLayout({ version: 1, widgets: defaultLayout.widgets.map((w, index) => index ? w : { ...w, size: "giant", secret: "x" }) })).toEqual(defaultLayout));
  it("persists only validated presentation state", () => { const next = { ...defaultLayout, widgets: [...defaultLayout.widgets].reverse() }; saveLayout(next); const stored = localStorage.getItem(LAYOUT_KEY)!; expect(JSON.parse(stored)).toEqual(next); expect(stored).not.toMatch(/accessToken|organization_id|project_id|workspace_id|content/i); });
  it("recovers invalid JSON", () => { localStorage.setItem(LAYOUT_KEY, "{"); expect(loadLayout()).toEqual(defaultLayout); });
});
