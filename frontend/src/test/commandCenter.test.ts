import { api } from "../api/client";
import { commandMetrics, loadCommandCenter, orderedProjectWork } from "../dashboard/commandCenter";
import type { Project } from "../api/types";

vi.mock("../api/client", () => ({ api: {
  projects: vi.fn(), workspaces: vi.fn(), captures: vi.fn(), journal: vi.fn(), reports: vi.fn(), memory: vi.fn(),
} }));

const project = (id: number, priority = "medium", updated_at = "2026-08-14T00:00:00Z"): Project => ({
  id, project_code: `P-${id}`, name: `Project ${id}`, description: null, customer: { id, name: `Customer ${id}` }, status: "active", priority,
  owner: null, primary_assignee: null, progress: 40, target_completion_date: null, updated_at,
});

describe("bounded Command Center composition", () => {
  beforeEach(() => vi.resetAllMocks());
  it("fails closed after a protected project read without downstream calls", async () => {
    vi.mocked(api.projects).mockResolvedValue({ state: "protected" });
    expect(await loadCommandCenter()).toEqual({ state: "protected" });
    expect(api.workspaces).not.toHaveBeenCalled(); expect(api.captures).not.toHaveBeenCalled();
  });
  it("uses at most six calls and retains bounded visible records", async () => {
    vi.mocked(api.projects).mockResolvedValue({ state: "success", data: { items: Array.from({ length: 12 }, (_, i) => project(i + 1)), total: 99, page: 1, size: 20 } });
    vi.mocked(api.workspaces).mockResolvedValue({ state: "success", data: { items: [{ id: 2, project_id: 1, project_code: "P-1", project_name: "Project 1", discipline: "control", display_name: "Control", description: null, status: "active", version: 1, updated_at: "2026-08-14T00:00:00Z", allowed_actions: [] }], total: 50 } });
    vi.mocked(api.captures).mockResolvedValue({ state: "success", data: { items: [], total: 50 } });
    vi.mocked(api.journal).mockResolvedValue({ state: "success", data: { view: "inbox", availability: "available", result_state: "success", view_content: {} } });
    vi.mocked(api.reports).mockResolvedValue({ state: "success", data: { items: [], total: 50 } });
    vi.mocked(api.memory).mockResolvedValue({ state: "success", data: { outcome: "success", page: { items: [], visible_total: 0, next_continuation: null } } });
    const result = await loadCommandCenter();
    expect(result.state).toBe("success"); if (result.state === "success") expect(result.data.projects).toHaveLength(8);
    expect([api.projects, api.workspaces, api.captures, api.journal, api.reports, api.memory].reduce((n, fn) => n + vi.mocked(fn).mock.calls.length, 0)).toBe(6);
  });
  it("does not request scoped sources without a visible workspace", async () => {
    vi.mocked(api.projects).mockResolvedValue({ state: "success", data: { items: [project(1)], total: 1, page: 1, size: 20 } });
    vi.mocked(api.workspaces).mockResolvedValue({ state: "protected" }); vi.mocked(api.captures).mockResolvedValue({ state: "protected" }); vi.mocked(api.journal).mockResolvedValue({ state: "protected" });
    const result = await loadCommandCenter(); expect(result.state).toBe("success");
    expect(api.reports).not.toHaveBeenCalled(); expect(api.memory).not.toHaveBeenCalled();
  });
});

describe("truthful visible-item derivation", () => {
  it("ignores hidden totals and derives exact visible counts", () => {
    const data = { projects: [project(1, "high"), project(2, "low", "2026-07-01T00:00:00Z")], workspaces: [], captures: [], reports: [], memory: [], journalState: "success" as const, sourceStates: { projects: "success", workspaces: "success", captures: "success", reports: "not_requested", memory: "not_requested" } as const };
    expect(commandMetrics(data, new Date("2026-08-15T00:00:00Z")).map((m) => m.value)).toEqual([2, 1, 1, 0]);
  });
  it("orders priority then update deterministically", () => expect(orderedProjectWork([project(2, "low"), project(3, "high", "2026-08-13T00:00:00Z"), project(1, "high")]).map((p) => p.id)).toEqual([1, 3, 2]));
});
