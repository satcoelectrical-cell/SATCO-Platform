import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { MemoryPage } from "../pages/KnowledgePages";
import { ReportsPage } from "../pages/ReportPages";
import { ProjectsPage, ProjectWorkspacePage } from "../pages/ProjectsPage";

const { apiMock } = vi.hoisted(() => ({ apiMock: { customers: vi.fn(), createCustomer: vi.fn(), createProject: vi.fn(), updateProject: vi.fn(), projects: vi.fn(), project: vi.fn(), workspaces: vi.fn(), createWorkspace: vi.fn(), captures: vi.fn(), createCapture: vi.fn(), reports: vi.fn(), reportSources: vi.fn(), report: vi.fn(), createReport: vi.fn(), reviseReport: vi.fn(), acceptReport: vi.fn(), memory: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));
const project = { id: 7, project_code: "SAT-007", name: "Substation Modernization", description: "Protection and control renewal.", customer: { id: 2, name: "Grid Operations" }, status: "in_progress", priority: "high", owner: null, primary_assignee: null, progress: 42, target_completion_date: null, updated_at: "2026-08-14T00:00:00Z" };

beforeEach(() => { for (const fn of Object.values(apiMock)) fn.mockReset(); apiMock.customers.mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 100 } }); });

it("takes an engineer from the authorized Project list into a coherent workspace", async () => {
  apiMock.projects.mockResolvedValue({ state: "success", data: { items: [project], total: 1, page: 1, size: 20 } });
  render(<MemoryRouter><ProjectsPage /></MemoryRouter>);
  expect(await screen.findByRole("link", { name: /Substation Modernization/i })).toHaveAttribute("href", "/projects/7");
});

it("creates a canonical Customer then Project without Organization input", async () => {
  apiMock.projects.mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 20 } });
  apiMock.createCustomer.mockResolvedValue({ state: "success", data: { id: 12, name: "North Plant", company: null, phone: null, email: null, created_at: "2026-08-20T00:00:00Z" } });
  apiMock.createProject.mockResolvedValue({ state: "success", data: project });
  const user = userEvent.setup(); render(<MemoryRouter><ProjectsPage /></MemoryRouter>);
  await user.type(screen.getByLabelText("Customer name"), "North Plant");
  await user.click(screen.getByRole("button", { name: /create customer/i }));
  expect(apiMock.createCustomer).toHaveBeenCalledWith(expect.objectContaining({ name: "North Plant" }));
  expect(apiMock.createCustomer.mock.calls[0][0]).not.toHaveProperty("organization_id");
});

it("combines Project, Workspace and Capture context without shadow state", async () => {
  apiMock.project.mockResolvedValue({ state: "success", data: project });
  apiMock.workspaces.mockResolvedValue({ state: "success", data: { items: [{ id: 9, project_id: 7, project_code: "SAT-007", project_name: project.name, discipline: "electrical", display_name: "Electrical Engineering", description: null, status: "active", version: 2, updated_at: "2026-08-14T00:00:00Z", allowed_actions: [] }], total: 1 } });
  apiMock.captures.mockResolvedValue({ state: "success", data: { items: [{ id: "00000000-0000-0000-0000-000000000009", project_id: 7, workspace_id: 9, discipline: "electrical", source_kind: "human_observation", lifecycle: "active", version: 1, created_at: "2026-08-14T00:00:00Z", updated_at: "2026-08-14T00:00:00Z" }], total: 1 } });
  render(<MemoryRouter initialEntries={["/projects/7"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage />} /></Routes></MemoryRouter>);
  expect(await screen.findByRole("heading", { name: project.name })).toBeVisible();
  expect((await screen.findAllByText("Electrical Engineering"))[0]).toBeVisible();
  expect(await screen.findByText("human observation")).toBeVisible();
});

it("creates Workspace and Capture then exposes contextual AI navigation", async () => {
  const workspace = { id: 9, project_id: 7, project_code: "SAT-007", project_name: project.name, discipline: "electrical", display_name: "Electrical Engineering", description: null, status: "draft", version: 1, updated_at: "2026-08-14T00:00:00Z", allowed_actions: [] };
  const capture = { id: "00000000-0000-0000-0000-000000000009", project_id: 7, workspace_id: 9, discipline: "electrical", source_kind: "observation", lifecycle: "captured", version: 1, created_at: "2026-08-14T00:00:00Z", updated_at: "2026-08-14T00:00:00Z" };
  apiMock.project.mockResolvedValue({ state: "success", data: project }); apiMock.workspaces.mockResolvedValue({ state: "success", data: { items: [workspace], total: 1 } }); apiMock.captures.mockResolvedValue({ state: "success", data: { items: [capture], total: 1 } }); apiMock.createCapture.mockResolvedValue({ state: "success", data: capture });
  const user = userEvent.setup(); render(<MemoryRouter initialEntries={["/projects/7"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage />} /></Routes></MemoryRouter>);
  await user.selectOptions(await screen.findByLabelText("Workspace"), "9"); await user.type(screen.getByLabelText("Capture content"), "Observed intermittent relay chatter."); await user.click(screen.getByRole("button", { name: /create capture/i }));
  expect(apiMock.createCapture).toHaveBeenCalledWith(expect.objectContaining({ project_id: 7, workspace_id: 9, source_kind: "observation" }));
  expect(await screen.findByRole("link", { name: /create technical report from observation/i })).toHaveAttribute("href", "/reports?project_id=7&workspace_id=9&capture_id=00000000-0000-0000-0000-000000000009");
  expect(await screen.findByRole("link", { name: /open ai advice/i })).toHaveAttribute("href", expect.stringContaining("capture_id=00000000"));
});

it("loads bounded Technical Reports through authorized selectors without typed IDs", async () => {
  apiMock.projects.mockResolvedValue({ state: "success", data: { items: [project], total: 1, page: 1, size: 20 } });
  apiMock.workspaces.mockResolvedValue({ state: "success", data: { items: [{ id: 9, project_id: 7, display_name: "Electrical Engineering" }], total: 1 } });
  apiMock.reports.mockResolvedValue({ state: "success", data: { items: [], total: 0 } }); apiMock.reportSources.mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 20 } });
  const user = userEvent.setup(); render(<MemoryRouter><ReportsPage /></MemoryRouter>); await user.selectOptions(await screen.findByLabelText("Project"), "7"); await user.selectOptions(await screen.findByLabelText("Engineering Workspace"), "9"); expect(await screen.findByText("No reports yet")).toBeVisible(); expect(apiMock.reports).toHaveBeenCalledWith(9, 7); expect(screen.queryByLabelText("Project ID")).not.toBeInTheDocument();
});

it("renders protected Memory as one neutral state with no count", async () => {
  apiMock.memory.mockResolvedValue({ state: "protected" }); const user = userEvent.setup(); render(<MemoryRouter><MemoryPage /></MemoryRouter>); await user.type(screen.getByLabelText("Workspace ID"), "9"); await user.click(screen.getByRole("button", { name: "Load context" })); expect(await screen.findByText("Not available")).toBeVisible(); expect(screen.queryByText(/0 records|denied|forbidden/i)).not.toBeInTheDocument();
});
