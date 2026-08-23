import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ReportsPage } from "../pages/ReportPages";

const { apiMock } = vi.hoisted(() => ({ apiMock: { projects: vi.fn(), workspaces: vi.fn(), reports: vi.fn(), reportSources: vi.fn(), reportEvidenceSources: vi.fn(), report: vi.fn(), createReport: vi.fn(), reviseReport: vi.fn(), acceptReport: vi.fn(), admitMemory: vi.fn(), downloadHistoricalSupportingFile: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));

const organization = "7e7c9d7a-7693-4f75-9bc5-3ef7bf528281";
const reportId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
const revisionId = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";
const provenance = { entry_id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd", ordinal: 0, source_class: "canonical_material", source_type: "universal_capture", is_material: true, owning_capability: "universal_capture", reliance_role: "source_capture", verification_status: "verified", availability_status: "available", origin_attribution: "Universal Engineering Capture", limitations: [], locator: { source_category: "universal_capture" }, integrity_algorithm: "sha256", integrity_digest: "a".repeat(64) };
const content = { engineering_scope: "Relay panel X1", technical_content: "Observed intermittent loss and verified terminal torque.", assumptions: [], uncertainty: "Intermittent behavior remains under observation.", limitations: [], conclusions: "Loose terminal is the probable cause.", recommendations: ["Retorque and trend voltage."] };
const qualification = { is_preliminary: false, evidence_deficiencies: [], unresolved_issues: [], follow_up_requirements: [] };
const summary = { id: reportId, organization_id: organization, workspace_id: 9, project_id: 7, owner_id: 11, purpose: "engineering_analysis", lifecycle: "draft" as const, version: 1, draft_revision_id: revisionId, is_preliminary: false, predecessor_report_id: null, created_at: "2026-08-20T09:00:00Z", updated_at: "2026-08-20T09:00:00Z", allowed_actions: ["revise", "accept"] };
const draft = { ...summary, content, qualification, provenance: [provenance] };
const accepted = { ...summary, lifecycle: "accepted" as const, version: 2, accepted_by_id: 11, accepted_at: "2026-08-20T10:00:00Z", accepted_draft_revision_id: revisionId, accepted_aggregate_version: 2, accepted_snapshot: { report_id: reportId, purpose: summary.purpose, organization_id: organization, workspace_id: 9, project_id: 7, content, qualification, provenance: [provenance], accepted_draft_revision_id: revisionId, accepted_aggregate_version: 2, accepted_by_id: 11, accepted_at: "2026-08-20T10:00:00Z", predecessor_report_id: null, integrity_digest: "b".repeat(64) } };

beforeEach(() => {
  for (const fn of Object.values(apiMock)) fn.mockReset();
  apiMock.projects.mockResolvedValue({ state: "success", data: { items: [{ id: 7, project_code: "SAT-007", name: "Substation", customer: { id: 2, name: "Plant" }, status: "active", priority: "high", owner: null, primary_assignee: null, progress: 20, description: null, target_completion_date: null, updated_at: "2026-08-20T09:00:00Z" }] } });
  apiMock.workspaces.mockResolvedValue({ state: "success", data: { items: [{ id: 9, project_id: 7, display_name: "Electrical Engineering" }], total: 1 } });
  apiMock.reports.mockResolvedValue({ state: "success", data: { items: [], total: 0 } });
  apiMock.report.mockResolvedValue({ state: "success", data: draft });
  apiMock.reportSources.mockResolvedValue({ state: "success", data: { items: [{ capture_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", project_id: 7, workspace_id: 9, source_kind: "observation", version: 3, created_at: "2026-08-20T09:00:00Z", preview: "Observed intermittent voltage loss.", provenance }], total: 1, page: 1, size: 20 } });
  apiMock.reportEvidenceSources.mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 20 } });
});

it("creates a Human-authored draft with server-composed Capture provenance", async () => {
  apiMock.createReport.mockResolvedValue({ state: "success", data: draft });
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={["/reports?project_id=7&workspace_id=9&capture_id=aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"]}><Routes><Route path="/reports" element={<ReportsPage />} /><Route path="/reports/:reportId" element={<ReportsPage />} /></Routes></MemoryRouter>);
  await waitFor(() => expect(apiMock.reportSources).toHaveBeenCalledWith(7, 9));
  expect(await screen.findByRole("radio")).toBeChecked();
  expect(screen.queryByLabelText(/Capture ID/i)).not.toBeInTheDocument();
  await user.type(await screen.findByLabelText("Engineering scope"), content.engineering_scope);
  await user.type(screen.getByLabelText("Technical content"), content.technical_content);
  await user.type(screen.getByLabelText("Uncertainty"), content.uncertainty);
  await user.type(screen.getByLabelText("Conclusions"), content.conclusions);
  await user.click(screen.getByRole("button", { name: "Create Human-authored draft" }));
  await waitFor(() => expect(apiMock.createReport).toHaveBeenCalled());
  const payload = apiMock.createReport.mock.calls[0][0];
  expect(payload).not.toHaveProperty("organization_id");
  expect(payload.provenance).toEqual([provenance]);
  expect(payload.workspace_id).toBe(9);
});

it("revises only the exact loaded draft with explicit Human rationale", async () => {
  apiMock.report.mockResolvedValue({ state: "success", data: draft });
  apiMock.reviseReport.mockResolvedValue({ state: "conflict" });
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={[`/reports/${reportId}?project_id=7&workspace_id=9`]}><Routes><Route path="/reports/:reportId" element={<ReportsPage />} /></Routes></MemoryRouter>);
  await user.type(await screen.findByLabelText("Human revision rationale"), "Corrected conclusion after Human review");
  await user.click(screen.getByRole("button", { name: "Save new exact revision" }));
  await waitFor(() => expect(apiMock.reviseReport).toHaveBeenCalledWith(reportId, expect.objectContaining({ expected_version: 1, expected_draft_revision_id: revisionId, rationale: "Corrected conclusion after Human review", provenance: [provenance] })));
  expect(await screen.findByText(/draft changed/i)).toBeVisible();
});

it("collapses a protected report to a neutral disclosure state", async () => {
  apiMock.report.mockResolvedValue({ state: "protected" });
  render(<MemoryRouter initialEntries={[`/reports/${reportId}`]}><Routes><Route path="/reports/:reportId" element={<ReportsPage />} /></Routes></MemoryRouter>);
  expect(await screen.findByText("Not available")).toBeVisible();
  expect(screen.queryByText(reportId)).not.toBeInTheDocument();
});

it("requires explicit Human rationale and confirmation for the exact revision", async () => {
  apiMock.report.mockResolvedValueOnce({ state: "success", data: draft }).mockResolvedValue({ state: "success", data: accepted });
  apiMock.acceptReport.mockResolvedValue({ state: "success", data: accepted });
  const user = userEvent.setup(); render(<MemoryRouter initialEntries={[`/reports/${reportId}?project_id=7&workspace_id=9`]}><Routes><Route path="/reports/:reportId" element={<ReportsPage />} /></Routes></MemoryRouter>);
  const button = await screen.findByRole("button", { name: "Accept exact revision" });
  expect(button).toBeDisabled();
  await user.type(screen.getByLabelText("Human acceptance rationale"), "Reviewed provenance and engineering conclusion");
  await user.click(screen.getByLabelText(/explicitly accept this exact revision/i));
  await user.click(button);
  await waitFor(() => expect(apiMock.acceptReport).toHaveBeenCalledWith(reportId, { expected_version: 1, exact_draft_revision_id: revisionId, confirmed: true, rationale: "Reviewed provenance and engineering conclusion" }));
  expect(await screen.findByText("Accepted and immutable")).toBeVisible();
  expect(screen.queryByRole("button", { name: "Accept exact revision" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Save new exact revision" })).not.toBeInTheDocument();
});

it("renders accepted authority from the immutable snapshot only", async () => {
  apiMock.report.mockResolvedValue({ state: "success", data: accepted });
  render(<MemoryRouter initialEntries={[`/reports/${reportId}`]}><Routes><Route path="/reports/:reportId" element={<ReportsPage />} /></Routes></MemoryRouter>);
  expect(await screen.findByRole("heading", { name: "Immutable accepted content" })).toBeVisible();
  expect(screen.queryByLabelText("Human revision rationale")).not.toBeInTheDocument();
  expect(screen.queryByLabelText("Human acceptance rationale")).not.toBeInTheDocument();
});

it("requires explicit Human Memory admission and uses only the exact accepted server-bound source", async () => {
  apiMock.report.mockResolvedValue({ state: "success", data: accepted });
  apiMock.admitMemory.mockResolvedValue({ state: "success", data: { outcome: "success", memory_id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee", version: 1, standing: "active" } });
  const user = userEvent.setup(); render(<MemoryRouter initialEntries={[`/reports/${reportId}?project_id=7&workspace_id=9`]}><Routes><Route path="/reports/:reportId" element={<ReportsPage />} /></Routes></MemoryRouter>);
  const button = await screen.findByRole("button", { name: "Admit exact accepted Report" }); expect(button).toBeDisabled();
  await user.type(screen.getByLabelText("Human admission rationale"), "Preserve verified terminal finding for consultation"); await user.type(screen.getByLabelText("Human authority rationale"), "I own this accepted report and approve bounded admission"); await user.click(screen.getByLabelText(/explicitly admit this exact accepted report/i)); await user.click(button);
  await waitFor(() => expect(apiMock.admitMemory).toHaveBeenCalledWith({ report_id: reportId, accepted_aggregate_version: 2, accepted_snapshot_digest: "b".repeat(64), workspace_id: 9, project_id: 7, admission_rationale: "Preserve verified terminal finding for consultation", authority_rationale: "I own this accepted report and approve bounded admission", reuse_restrictions: [] }));
  expect(screen.queryByLabelText(/report id|workspace id|project id|organization id/i)).not.toBeInTheDocument(); expect(await screen.findByRole("link", { name: "Open governed Memory detail" })).toHaveAttribute("href", expect.stringContaining("/memory/eeeeeeee"));
});
