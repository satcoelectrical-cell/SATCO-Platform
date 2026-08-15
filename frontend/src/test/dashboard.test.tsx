import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { DashboardPage } from "../pages/DashboardPage";
import { LAYOUT_KEY } from "../dashboard/layout";
import { api } from "../api/client";

vi.mock("../api/client", () => ({ api: { projects: vi.fn(), workspaces: vi.fn(), captures: vi.fn(), journal: vi.fn(), reports: vi.fn(), memory: vi.fn() } }));

describe("customizable dashboard", () => {
  beforeEach(() => { localStorage.clear(); vi.resetAllMocks(); vi.mocked(api.projects).mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 20 } }); });
  it("renders an information-rich operational default without fake counts", async () => { render(<MemoryRouter><DashboardPage /></MemoryRouter>); expect(screen.getByRole("heading", { name: /engineering priorities/i })).toBeVisible(); expect(await screen.findByText("Visible projects")).toBeVisible(); expect(screen.getByRole("heading", { name: "Active Projects" })).toBeVisible(); expect(screen.getByText("No visible active projects")).toBeVisible(); expect(screen.getByText("No visible Capture context is ready.")).toBeVisible(); expect(screen.queryByText(/99|1,000/)).not.toBeInTheDocument(); });
  it("supports keyboard-accessible reorder, resize, hide, restore and reset", async () => { const user = userEvent.setup(); render(<MemoryRouter><DashboardPage /></MemoryRouter>); await user.click(screen.getByRole("button", { name: "Customize Dashboard" })); await user.click(screen.getByRole("button", { name: "Move Active Projects later" })); await user.selectOptions(screen.getByRole("combobox", { name: "Size of Active Projects" }), "wide"); await user.click(screen.getByRole("button", { name: "Hide Active Projects" })); expect(screen.queryByRole("heading", { name: "Active Projects" })).not.toBeInTheDocument(); await user.click(screen.getByRole("button", { name: "Active Projects" })); expect(screen.getByRole("heading", { name: "Active Projects" })).toBeVisible(); expect(localStorage.getItem(LAYOUT_KEY)).toBeTruthy(); await user.click(screen.getByRole("button", { name: /reset satco default/i })); expect(localStorage.getItem(LAYOUT_KEY)).toBeNull(); });
  it("renders real bounded project, report, memory and AI-entry context", async () => {
    vi.mocked(api.projects).mockResolvedValue({ state: "success", data: { items: [{ id: 1, project_code: "SAT-1", name: "Substation Controls", description: null, customer: { id: 2, name: "North Plant" }, status: "active", priority: "high", owner: null, primary_assignee: null, progress: 62, target_completion_date: null, updated_at: "2026-08-14T00:00:00Z" }], total: 999, page: 1, size: 20 } });
    vi.mocked(api.workspaces).mockResolvedValue({ state: "success", data: { items: [{ id: 5, project_id: 1, project_code: "SAT-1", project_name: "Substation Controls", discipline: "control", display_name: "Controls", description: null, status: "active", version: 1, updated_at: "2026-08-14T00:00:00Z", allowed_actions: [] }], total: 1 } });
    vi.mocked(api.captures).mockResolvedValue({ state: "success", data: { items: [{ id: "12345678-0000-4000-8000-000000000000", project_id: 1, workspace_id: 5, discipline: "control", source_kind: "field_note", lifecycle: "active", version: 2, created_at: "2026-08-14T00:00:00Z", updated_at: "2026-08-14T00:00:00Z" }], total: 1 } });
    vi.mocked(api.journal).mockResolvedValue({ state: "success", data: { view: "inbox", availability: "available", result_state: "success", view_content: {} } });
    vi.mocked(api.reports).mockResolvedValue({ state: "success", data: { items: [{ id: "report-1", workspace_id: 5, project_id: 1, purpose: "Control philosophy", lifecycle: "accepted", version: 3, is_preliminary: false, updated_at: "2026-08-14T00:00:00Z" }], total: 1 } });
    vi.mocked(api.memory).mockResolvedValue({ state: "success", data: { outcome: "success", page: { items: [{ memory_id: "memory-1", version: 1, standing: "active", source_report_id: "report-1", purpose: "Commissioning interlock lesson", workspace_id: 5, project_id: 1, admitted_at: "2026-08-13T00:00:00Z", updated_at: "2026-08-13T00:00:00Z" }], visible_total: 1, next_continuation: null } } });
    render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    expect((await screen.findAllByText("Substation Controls"))[0]).toBeVisible();
    expect(screen.getByText("Control philosophy")).toBeVisible(); expect(screen.getByText("Commissioning interlock lesson")).toBeVisible();
    expect(screen.getByText(/Capture context is ready/i)).toBeVisible(); expect(screen.queryByText("999")).not.toBeInTheDocument();
    expect(screen.getByRole("table", { name: /authorized active project view/i })).toBeVisible();
  });
});
