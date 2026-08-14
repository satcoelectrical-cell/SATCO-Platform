export const widgetIds = ["projects", "engineering-work", "reports", "memory", "assistant"] as const;
export type WidgetId = typeof widgetIds[number];
export type WidgetSize = "compact" | "standard" | "wide";
export interface WidgetLayout { id: WidgetId; size: WidgetSize; hidden: boolean }
export interface DashboardLayout { version: 1; widgets: WidgetLayout[] }
export const LAYOUT_KEY = "satco.dashboard.layout.v1";
export const defaultLayout: DashboardLayout = { version: 1, widgets: [
  { id: "projects", size: "standard", hidden: false }, { id: "engineering-work", size: "standard", hidden: false },
  { id: "reports", size: "compact", hidden: false }, { id: "memory", size: "compact", hidden: false },
  { id: "assistant", size: "compact", hidden: false },
] };

export function validateLayout(value: unknown): DashboardLayout {
  if (!value || typeof value !== "object" || (value as { version?: unknown }).version !== 1) return structuredClone(defaultLayout);
  const widgets = (value as { widgets?: unknown }).widgets;
  if (!Array.isArray(widgets) || widgets.length !== widgetIds.length) return structuredClone(defaultLayout);
  const ids = widgets.map((w) => (w as { id?: unknown })?.id);
  if (new Set(ids).size !== widgetIds.length || !widgetIds.every((id) => ids.includes(id))) return structuredClone(defaultLayout);
  if (!widgets.every((w) => w && typeof w === "object" && Object.keys(w).every((k) => ["id", "size", "hidden"].includes(k)) && ["compact", "standard", "wide"].includes(String((w as WidgetLayout).size)) && typeof (w as WidgetLayout).hidden === "boolean")) return structuredClone(defaultLayout);
  return { version: 1, widgets: widgets as WidgetLayout[] };
}
export function loadLayout(storage: Pick<Storage, "getItem"> = localStorage): DashboardLayout { try { return validateLayout(JSON.parse(storage.getItem(LAYOUT_KEY) ?? "null")); } catch { return structuredClone(defaultLayout); } }
export function saveLayout(layout: DashboardLayout, storage: Pick<Storage, "setItem"> = localStorage) { storage.setItem(LAYOUT_KEY, JSON.stringify(validateLayout(layout))); }
