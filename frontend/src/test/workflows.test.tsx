import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { MemoryPage, ReportsPage } from "../pages/KnowledgePages";
import { ProjectsPage, ProjectWorkspacePage } from "../pages/ProjectsPage";

const { apiMock } = vi.hoisted(() => ({ apiMock: { projects: vi.fn(), project: vi.fn(), workspaces: vi.fn(), captures: vi.fn(), reports: vi.fn(), memory: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));
const project = { id: 7, project_code: "SAT-007", name: "Substation Modernization", description: "Protection and control renewal.", customer: { id: 2, name: "Grid Operations" }, status: "in_progress", priority: "high", owner: null, primary_assignee: null, progress: 42, target_completion_date: null, updated_at: "2026-08-14T00:00:00Z" };

beforeEach(() => { for (const fn of Object.values(apiMock)) fn.mockReset(); });

it("takes an engineer from the authorized Project list into a coherent workspace", async () => {
  apiMock.projects.mockResolvedValue({ state: "success", data: { items: [project], total: 1, page: 1, size: 20 } });
  render(<MemoryRouter><ProjectsPage /></MemoryRouter>);
  expect(await screen.findByRole("link", { name: /Substation Modernization/i })).toHaveAttribute("href", "/projects/7");
});

it("combines Project, Workspace and Capture context without shadow state", async () => {
  apiMock.project.mockResolvedValue({ state: "success", data: project });
  apiMock.workspaces.mockResolvedValue({ state: "success", data: { items: [{ id: 9, project_id: 7, project_code: "SAT-007", project_name: project.name, discipline: "electrical", display_name: "Electrical Engineering", description: null, status: "active", version: 2, updated_at: "2026-08-14T00:00:00Z", allowed_actions: [] }], total: 1 } });
  apiMock.captures.mockResolvedValue({ state: "success", data: { items: [{ id: "00000000-0000-0000-0000-000000000009", project_id: 7, workspace_id: 9, discipline: "electrical", source_kind: "human_observation", lifecycle: "active", version: 1, created_at: "2026-08-14T00:00:00Z", updated_at: "2026-08-14T00:00:00Z" }], total: 1 } });
  render(<MemoryRouter initialEntries={["/projects/7"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage />} /></Routes></MemoryRouter>);
  expect(await screen.findByRole("heading", { name: project.name })).toBeVisible();
  expect(await screen.findByText("Electrical Engineering")).toBeVisible();
  expect(await screen.findByText("human observation")).toBeVisible();
});

it("loads bounded Technical Reports only after explicit Workspace context", async () => {
  apiMock.reports.mockResolvedValue({ state: "success", data: { items: [{ id: "00000000-0000-0000-0000-000000000010", workspace_id: 9, project_id: 7, purpose: "design_basis", lifecycle: "accepted", version: 3, is_preliminary: false, updated_at: "2026-08-14T00:00:00Z" }], total: 1 } });
  const user = userEvent.setup(); render(<MemoryRouter><ReportsPage /></MemoryRouter>); await user.type(screen.getByLabelText("Project ID"), "7"); await user.type(screen.getByLabelText("Workspace ID"), "9"); await user.click(screen.getByRole("button", { name: "Load context" })); expect(await screen.findByText("Report 00000000")).toBeVisible(); expect(apiMock.reports).toHaveBeenCalledWith(9, 7);
});

it("renders protected Memory as one neutral state with no count", async () => {
  apiMock.memory.mockResolvedValue({ state: "protected" }); const user = userEvent.setup(); render(<MemoryRouter><MemoryPage /></MemoryRouter>); await user.type(screen.getByLabelText("Workspace ID"), "9"); await user.click(screen.getByRole("button", { name: "Load context" })); expect(await screen.findByText("Not available")).toBeVisible(); expect(screen.queryByText(/0 records|denied|forbidden/i)).not.toBeInTheDocument();
});
