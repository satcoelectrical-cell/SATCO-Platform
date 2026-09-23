import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { MemoryPage } from "../pages/KnowledgePages";
import { ReportsPage } from "../pages/ReportPages";
import { ProjectsPage, ProjectWorkspacePage } from "../pages/ProjectsPage";
import { ControlAutomationPackagePanel } from "../disciplinePackages/ControlAutomationPackagePanel";
import { ProjectPackageConfigurationPanel } from "../components/ProjectPackageConfigurationPanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: { customers: vi.fn(), createCustomer: vi.fn(), createProject: vi.fn(), updateProject: vi.fn(), projects: vi.fn(), project: vi.fn(), projectFoundation: vi.fn(), putProjectFoundation: vi.fn(), createProjectInput: vi.fn(), updateProjectInput: vi.fn(), reorderProjectInputs: vi.fn(), transitionProjectInput: vi.fn(), transitionProjectStage: vi.fn(), projectInputSources: vi.fn(), executionPlan: vi.fn(), deliverables: vi.fn(), createDeliverable: vi.fn(), workspaces: vi.fn(), createWorkspace: vi.fn(), captures: vi.fn(), createCapture: vi.fn(), reports: vi.fn(), reportSources: vi.fn(), reportEvidenceSources: vi.fn(), report: vi.fn(), createReport: vi.fn(), reviseReport: vi.fn(), acceptReport: vi.fn(), admitMemory: vi.fn(), memory: vi.fn(), memoryDetail: vi.fn(), supportingFiles: vi.fn(), evidence: vi.fn(), uploadSupportingFile: vi.fn(), linkSupportingFiles: vi.fn(), downloadSupportingFile: vi.fn(), projectControls: vi.fn(), projectControlHistory: vi.fn(), createProjectControl: vi.fn(), transitionProjectControl: vi.fn(), createChangeImpact: vi.fn(), confirmChangeImpact: vi.fn(), projectCompleteness: vi.fn(), engineeringGuidance: vi.fn(), effectiveDisciplinePackages: vi.fn(), workspacePackageApplicability: vi.fn(), createElectricalObject: vi.fn(), evaluateElectricalRule: vi.fn(), projectPackageConfiguration: vi.fn(), supportedPackages: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));
const projectContextMock=vi.fn();
const relatedContextMock=vi.fn();
const projectStandardsMock=vi.fn();
const projectStandardCandidatesMock=vi.fn();
Object.assign(apiMock,{projectContext:projectContextMock,relatedContext:relatedContextMock,projectStandards:projectStandardsMock,projectStandardCandidates:projectStandardCandidatesMock});
const performanceIndicatorsMock = vi.fn();
const performanceHealthMock = vi.fn();
const performanceActionsMock = vi.fn();
const performanceTrendsMock = vi.fn();
const performanceDrillDownMock = vi.fn();
Object.assign(apiMock, {
  engineeringPerformanceIndicators: performanceIndicatorsMock,
  engineeringPerformanceHealth: performanceHealthMock,
  engineeringPerformanceActions: performanceActionsMock,
  engineeringPerformanceTrends: performanceTrendsMock,
  engineeringPerformanceDrillDown: performanceDrillDownMock,
});
const engineeringObjectOptionsMock=vi.fn(),packageContextBindingOptionsMock=vi.fn(),bindControlAutomationContextMock=vi.fn(),bindControlAutomationEvidenceMock=vi.fn(),createControlAutomationRelationshipMock=vi.fn(),createControlAutomationDeliverableMock=vi.fn(),controlAutomationReadinessMock=vi.fn(),evaluateControlAutomationRuleMock=vi.fn(),compatibilityProfilesMock=vi.fn(),replaceProjectPackageConfigurationMock=vi.fn(),removeProjectPackageConfigurationMock=vi.fn();
Object.assign(apiMock,{engineeringObjectOptions:engineeringObjectOptionsMock,packageContextBindingOptions:packageContextBindingOptionsMock,bindControlAutomationContext:bindControlAutomationContextMock,bindControlAutomationEvidence:bindControlAutomationEvidenceMock,createControlAutomationRelationship:createControlAutomationRelationshipMock,createControlAutomationDeliverable:createControlAutomationDeliverableMock,controlAutomationReadiness:controlAutomationReadinessMock,evaluateControlAutomationRule:evaluateControlAutomationRuleMock,compatibilityProfiles:compatibilityProfilesMock,replaceProjectPackageConfiguration:replaceProjectPackageConfigurationMock,removeProjectPackageConfiguration:removeProjectPackageConfigurationMock});
const project = { id: 7, project_code: "SAT-007", name: "Substation Modernization", description: "Protection and control renewal.", customer: { id: 2, name: "Grid Operations" }, status: "in_progress", priority: "high", owner: null, primary_assignee: null, progress: 42, target_completion_date: null, updated_at: "2026-08-14T00:00:00Z" };

beforeEach(() => { for (const fn of Object.values(apiMock)) fn.mockReset(); apiMock.workspacePackageApplicability.mockResolvedValue({ state: "success", data: { operational_state: "UNAVAILABLE", component_key: null, allowed_actions: [], effective_package: null } }); apiMock.customers.mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 100 } }); apiMock.projectFoundation.mockResolvedValue({ state: "success", data: { outcome: "success", availability: "basis_not_established", project_id: 7, allowed_actions: ["establish"] } }); apiMock.executionPlan.mockResolvedValue({ state: "success", data: { outcome: "success", availability: "plan_not_established", project_id: 7, allowed_actions: [] } }); apiMock.deliverables.mockResolvedValue({ state: "success", data: { outcome: "success", items: [], visible_count: 0, continuation: null } }); apiMock.supportingFiles.mockResolvedValue({ state: "success", data: { outcome: "success", items: [], visible_count: 0, continuation: null } }); apiMock.evidence.mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 100 } }); apiMock.reportEvidenceSources.mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 20 } }); apiMock.projectControls.mockImplementation((_projectId: number, kind: string) => Promise.resolve({ state: "success", data: { outcome: "success", kind, items: [], visible_count: 0 } })); apiMock.projectCompleteness.mockResolvedValue({ state: "success", data: { status: "success", observation: { assessment_status: "complete_within_bounds", authority_class: "derived", advisory: true, authoritative: false, limitation_codes: [], findings: [] } } }); apiMock.engineeringGuidance.mockResolvedValue({ state: "success", data: { kind: "success", observation: { catalog: { catalog_id: "engineering_guidance.v1", catalog_version: 1, catalog_digest: "workflow-safe-catalog", rules: [] }, context_observation_digest: "workflow-safe-context", status: "complete_within_bounds", source_observation_started_at: "2026-08-27T00:00:00Z", source_observation_completed_at: "2026-08-27T00:00:01Z", generated_at: "2026-08-27T00:00:02Z", items: [], candidate_material_requirements: [], limitations: [], authority_class: "derived", advisory: true, authoritative: false } } }); apiMock.effectiveDisciplinePackages.mockResolvedValue({ state: "success", data: { project_id: 7, items: [] } }); apiMock.projectPackageConfiguration.mockResolvedValue({state:"success",data:{state:"NOT_CONFIGURED",project_id:7,organization_id:"org",configuration_version:0,selections:[]}}); apiMock.supportedPackages.mockResolvedValue({state:"success",data:{registry_digest:"core",items:[],next_cursor:null}}); });
beforeEach(()=>{projectContextMock.mockResolvedValue({state:"unavailable"});relatedContextMock.mockResolvedValue({state:"unavailable"});projectStandardsMock.mockResolvedValue({state:"success",data:{items:[],next_cursor:null}});projectStandardCandidatesMock.mockResolvedValue({state:"success",data:{items:[]}});});
beforeEach(() => {
  performanceIndicatorsMock.mockResolvedValue({ state: "success", data: { window_days: 30, observations: [] } });
  performanceHealthMock.mockResolvedValue({ state: "success", data: { factors: [] } });
  performanceActionsMock.mockResolvedValue({ state: "success", data: { actions: [] } });
  performanceTrendsMock.mockResolvedValue({ state: "success", data: { points: [], limitations: ["no_persisted_trend_points"] } });
  performanceDrillDownMock.mockResolvedValue({ state: "success", data: { items: [] } });
  engineeringObjectOptionsMock.mockResolvedValue({state:"success",data:{items:[]}});
  packageContextBindingOptionsMock.mockResolvedValue({state:"success",data:{items:[]}});
  bindControlAutomationContextMock.mockResolvedValue({state:"success",data:{}});
  bindControlAutomationEvidenceMock.mockResolvedValue({state:"success",data:{}});
  createControlAutomationRelationshipMock.mockResolvedValue({state:"success",data:{}});
  createControlAutomationDeliverableMock.mockResolvedValue({state:"success",data:{}});
  controlAutomationReadinessMock.mockResolvedValue({state:"success",data:{}});
  evaluateControlAutomationRuleMock.mockResolvedValue({state:"success",data:{status:"PASS"}});
  compatibilityProfilesMock.mockResolvedValue({state:"success",data:{registry_digest:"r",items:[]}});
});

it("uses an authorized Human-readable compatibility profile selector without raw entry",async()=>{
  compatibilityProfilesMock.mockResolvedValue({state:"success",data:{registry_digest:"r",items:[{handle:"profile-1",label:"Control systems baseline",profile_digest:"d".repeat(64)}]}});
  render(<ProjectPackageConfigurationPanel projectId={7}/>);
  const selector=await screen.findByLabelText("Compatibility profile");
  expect(selector).toHaveValue("profile-1");
  expect(within(selector).getByRole("option",{name:"Control systems baseline"})).toHaveValue("profile-1");
  expect(screen.queryByRole("textbox",{name:"Compatibility profile"})).not.toBeInTheDocument();
});

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

it("derives Workspace choices only from effective server state and preserves unavailable states", async () => {
  apiMock.project.mockResolvedValue({ state: "success", data: project }); apiMock.workspaces.mockResolvedValue({ state: "success", data: { items: [], total: 0 } }); apiMock.captures.mockResolvedValue({ state: "success", data: { items: [], total: 0 } });
  apiMock.effectiveDisciplinePackages.mockResolvedValue({ state: "success", data: { project_id: 7, items: [
    { discipline_id: "control_automation", display_name: "Control & Automation", availability: "OPERATIONAL_AVAILABLE", allowed_actions: ["create_workspace"], binding_state: "OPERATIONAL_PACKAGE_BOUND", package_key: "control_automation", package_version: "1.0.0", descriptor_digest: "a", project_configuration_revision: 3 },
    { discipline_id: "electrical", display_name: "Electrical", availability: "FUTURE_UNAVAILABLE", allowed_actions: [], binding_state: "FUTURE_UNAVAILABLE_UNBOUND", package_key: null, package_version: null, descriptor_digest: null, project_configuration_revision: null },
    { discipline_id: "legacy_unknown", display_name: "Legacy unresolved", availability: "LEGACY_UNRESOLVED", allowed_actions: [], binding_state: "LEGACY_UNRESOLVED", package_key: null, package_version: null, descriptor_digest: null, project_configuration_revision: null },
  ] } });
  apiMock.createWorkspace.mockResolvedValue({ state: "success", data: { id: 9 } });
  const user = userEvent.setup(); render(<MemoryRouter initialEntries={["/projects/7"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage />} /></Routes></MemoryRouter>);
  const selector = await screen.findByLabelText("Discipline");
  expect(screen.getByRole("option", { name: /control & automation.*operational available/i })).not.toBeDisabled();
  expect(screen.getByRole("option", { name: /electrical.*future unavailable/i })).toBeDisabled();
  expect(screen.getByRole("option", { name: /legacy unresolved.*legacy unresolved/i })).toBeDisabled();
  expect(screen.queryByRole("option", { name: /^Mechanical/ })).not.toBeInTheDocument();
  await user.selectOptions(selector, "control_automation"); await user.click(screen.getByRole("button", { name: /create workspace/i }));
  expect(apiMock.createWorkspace).toHaveBeenCalledWith(7, { discipline: "control" });
});

it("builds package-aware navigation only from operational disciplines with authorized Workspaces", async () => {
  apiMock.project.mockResolvedValue({ state: "success", data: project });
  apiMock.workspaces.mockResolvedValue({ state: "success", data: { items: [
    { id: 9, project_id: 7, discipline: "electrical", display_name: "Electrical Engineering", status:"active", version:1 },
    { id: 10, project_id: 7, discipline: "instrumentation", display_name: "Instrumentation Engineering", status:"active", version:1 },
    { id: 11, project_id: 7, discipline: "control", display_name: "Control & Automation Engineering", status:"active", version:1 },
  ], total: 3 } });
  apiMock.captures.mockResolvedValue({ state: "success", data: { items: [], total: 0 } });
  apiMock.effectiveDisciplinePackages.mockResolvedValue({ state: "success", data: { project_id: 7, items: [
    { discipline_id:"electrical",display_name:"Electrical",availability:"OPERATIONAL_AVAILABLE",allowed_actions:[],binding_state:"OPERATIONAL_PACKAGE_BOUND",package_key:"electrical",package_version:"1",descriptor_digest:"e",project_configuration_revision:1 },
    { discipline_id:"instrumentation",display_name:"Instrumentation",availability:"OPERATIONAL_AVAILABLE",allowed_actions:[],binding_state:"OPERATIONAL_PACKAGE_BOUND",package_key:"instrumentation",package_version:"1",descriptor_digest:"i",project_configuration_revision:1 },
    { discipline_id:"control_automation",display_name:"Control & Automation",availability:"OPERATIONAL_AVAILABLE",allowed_actions:[],binding_state:"OPERATIONAL_PACKAGE_BOUND",package_key:"control",package_version:"1",descriptor_digest:"c",project_configuration_revision:1 },
    { discipline_id:"mechanical",display_name:"Mechanical",availability:"FUTURE_UNAVAILABLE",allowed_actions:[],binding_state:"FUTURE_UNAVAILABLE_UNBOUND",package_key:null,package_version:null,descriptor_digest:null,project_configuration_revision:null },
  ] } });
  render(<MemoryRouter initialEntries={["/projects/7"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage/>}/></Routes></MemoryRouter>);
  const nav=await screen.findByRole("navigation",{name:"Project engineering sections"});
  expect(within(nav).getByRole("button",{name:"Electrical"})).toBeVisible();
  expect(within(nav).getByRole("button",{name:"Instrumentation"})).toBeVisible();
  expect(within(nav).getByRole("button",{name:"Control & Automation"})).toBeVisible();
  expect(within(nav).queryByRole("button",{name:"Mechanical"})).not.toBeInTheDocument();
  expect(screen.getByText("Onboarding: ready to enter")).toBeVisible();
});

it.each([
  ["electrical","Electrical"],
  ["instrumentation","Instrumentation"],
  ["control_automation","Control & Automation"],
])("supports a single operational %s package without inventing sibling destinations", async (disciplineId,label) => {
  const legacy=disciplineId==="control_automation"?"control":disciplineId;
  apiMock.project.mockResolvedValue({state:"success",data:project});
  apiMock.workspaces.mockResolvedValue({state:"success",data:{items:[{id:9,project_id:7,discipline:legacy,display_name:label,status:"active",version:1}],total:1}});
  apiMock.captures.mockResolvedValue({state:"success",data:{items:[],total:0}});
  apiMock.effectiveDisciplinePackages.mockResolvedValue({state:"success",data:{project_id:7,items:[{discipline_id:disciplineId,display_name:label,availability:"OPERATIONAL_AVAILABLE",allowed_actions:[],binding_state:"OPERATIONAL_PACKAGE_BOUND",package_key:disciplineId,package_version:"1",descriptor_digest:"x",project_configuration_revision:1}]}});
  render(<MemoryRouter initialEntries={["/projects/7"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage/>}/></Routes></MemoryRouter>);
  const nav=await screen.findByRole("navigation",{name:"Project engineering sections"});
  expect(within(nav).getByRole("button",{name:label})).toBeVisible();
  for(const other of ["Electrical","Instrumentation","Control & Automation"].filter(v=>v!==label)) expect(within(nav).queryByRole("button",{name:other})).not.toBeInTheDocument();
});

it("reports package-aware onboarding without automatically mutating owner state", async () => {
  apiMock.project.mockResolvedValue({state:"success",data:project}); apiMock.workspaces.mockResolvedValue({state:"success",data:{items:[],total:0}}); apiMock.captures.mockResolvedValue({state:"success",data:{items:[],total:0}});
  apiMock.effectiveDisciplinePackages.mockResolvedValueOnce({state:"success",data:{project_id:7,items:[]}});
  const {unmount}=render(<MemoryRouter initialEntries={["/projects/7"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage/>}/></Routes></MemoryRouter>);
  expect(await screen.findByText("Onboarding: needs project configuration")).toBeVisible();
  expect(apiMock.createWorkspace).not.toHaveBeenCalled(); unmount();
  apiMock.effectiveDisciplinePackages.mockResolvedValue({state:"success",data:{project_id:7,items:[{discipline_id:"electrical",display_name:"Electrical",availability:"OPERATIONAL_AVAILABLE",allowed_actions:["create_workspace"],binding_state:"OPERATIONAL_PACKAGE_BOUND",package_key:"electrical",package_version:"1",descriptor_digest:"e",project_configuration_revision:1}]}});
  render(<MemoryRouter initialEntries={["/projects/7"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage/>}/></Routes></MemoryRouter>);
  expect(await screen.findByText("Onboarding: needs workspace")).toBeVisible();
  expect(apiMock.createWorkspace).not.toHaveBeenCalled();
});

it("loads bounded Technical Reports through authorized selectors without typed IDs", async () => {
  apiMock.projects.mockResolvedValue({ state: "success", data: { items: [project], total: 1, page: 1, size: 20 } });
  apiMock.workspaces.mockResolvedValue({ state: "success", data: { items: [{ id: 9, project_id: 7, display_name: "Electrical Engineering" }], total: 1 } });
  apiMock.reports.mockResolvedValue({ state: "success", data: { items: [], total: 0 } }); apiMock.reportSources.mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 20 } });
  const user = userEvent.setup(); render(<MemoryRouter><ReportsPage /></MemoryRouter>); await user.selectOptions(await screen.findByLabelText("Project"), "7"); await user.selectOptions(await screen.findByLabelText("Engineering Workspace"), "9"); expect(await screen.findByText("No reports yet")).toBeVisible(); expect(apiMock.reports).toHaveBeenCalledWith(9, 7); expect(screen.queryByLabelText("Project ID")).not.toBeInTheDocument();
});

it("renders protected Memory through contextual selectors as one neutral state with no count", async () => {
  apiMock.projects.mockResolvedValue({ state: "success", data: { items: [project] } }); apiMock.workspaces.mockResolvedValue({ state: "success", data: { items: [{ id: 9, display_name: "Electrical Engineering" }], total: 1 } }); apiMock.memory.mockResolvedValue({ state: "protected" }); const user = userEvent.setup(); render(<MemoryRouter><MemoryPage /></MemoryRouter>); await user.selectOptions(await screen.findByLabelText("Project"), "7"); await user.selectOptions(await screen.findByLabelText("Engineering Workspace"), "9"); expect(await screen.findByText("Not available")).toBeVisible(); expect(screen.queryByText(/0 records|denied|forbidden/i)).not.toBeInTheDocument(); expect(screen.queryByLabelText(/workspace id|project id/i)).not.toBeInTheDocument();
});

it("restores an authorized Workspace deep link and clears a stale Workspace selection", async () => {
  const workspace = { id: 9, project_id: 7, project_code: "SAT-007", project_name: project.name, discipline: "electrical", display_name: "Electrical Engineering", description: null, status: "active", version: 1, updated_at: "2026-09-22T00:00:00Z", allowed_actions: [] };
  apiMock.project.mockResolvedValue({state:"success",data:project}); apiMock.workspaces.mockResolvedValue({state:"success",data:{items:[workspace],total:1}}); apiMock.captures.mockResolvedValue({state:"success",data:{items:[],total:0}});
  const {unmount}=render(<MemoryRouter initialEntries={["/projects/7?workspace=9"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage/>}/></Routes></MemoryRouter>);
  expect(await screen.findByLabelText("Workspace")).toHaveValue("9"); unmount();
  render(<MemoryRouter initialEntries={["/projects/7?workspace=99"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage/>}/></Routes></MemoryRouter>);
  const recoveredSelector=await screen.findByLabelText("Workspace");
  expect(recoveredSelector).toHaveValue("");
  expect(await screen.findByText(/unavailable Workspace selection was cleared/i)).toBeVisible();
  await waitFor(()=>expect(recoveredSelector).toHaveFocus());
});

it("announces project section changes and moves focus to the selected region",async()=>{
  apiMock.project.mockResolvedValue({state:"success",data:project}); apiMock.workspaces.mockResolvedValue({state:"success",data:{items:[],total:0}}); apiMock.captures.mockResolvedValue({state:"success",data:{items:[],total:0}});
  const user=userEvent.setup();render(<MemoryRouter initialEntries={["/projects/7"]}><Routes><Route path="/projects/:projectId" element={<ProjectWorkspacePage/>}/></Routes></MemoryRouter>);
  const evidence=await screen.findByRole("button",{name:"Evidence"});
  await user.click(evidence);
  expect(evidence).toHaveAttribute("aria-pressed","true");
  expect(screen.getByRole("region",{name:"Evidence"})).toHaveFocus();
  expect(screen.getByText(/Select an Engineering Workspace for Supporting Evidence/i)).toBeVisible();
});

it("closes Control & Automation Object and Context raw-ID entry with exact authorized selectors",async()=>{
  engineeringObjectOptionsMock.mockResolvedValue({state:"success",data:{items:[{handle:"11111111-1111-4111-8111-111111111111",label:"PLC-101 — plc"},{handle:"22222222-2222-4222-8222-222222222222",label:"DCS-201 — dcs controller"}]}});
  packageContextBindingOptionsMock.mockResolvedValue({state:"success",data:{items:[{context_handle:12,subject_handle:34,context_version:5,label:"Control philosophy — PLC-101 · control basis"}]}});
  apiMock.workspacePackageApplicability.mockResolvedValue({state:"success",data:{project_id:7,project_configuration_revision:3}});
  const user=userEvent.setup();render(<ControlAutomationPackagePanel state="OPERATIONAL_AVAILABLE" projectId={7} workspaceId={9}/>);
  expect(await screen.findAllByRole("option",{name:"PLC-101 — plc"})).toHaveLength(2);
  await user.selectOptions(screen.getByLabelText("Engineering Context subject"),"12:34");
  await user.type(screen.getAllByLabelText("Rationale")[2],"Bind selected current Context");
  await user.click(screen.getByRole("button",{name:"Bind Context declaration"}));
  expect(bindControlAutomationContextMock).toHaveBeenCalledWith(7,9,expect.objectContaining({context_id:12,context_subject_reference_id:34,expected_context_version:5,expected_configuration_revision:3}));
  expect(screen.queryByLabelText(/object id|context id|revision id/i)).not.toBeInTheDocument();
});

it("keeps Control & Automation binding actions unavailable without a valid configuration revision",async()=>{
  packageContextBindingOptionsMock.mockResolvedValue({state:"success",data:{items:[{context_handle:12,subject_handle:34,context_version:5,label:"Control philosophy — Workspace"}]}});
  apiMock.workspacePackageApplicability.mockResolvedValue({state:"success",data:{project_id:7,project_configuration_revision:null}});
  render(<ControlAutomationPackagePanel state="OPERATIONAL_AVAILABLE" projectId={7} workspaceId={9}/>);
  expect(await screen.findByText(/Configuration revision: unavailable/)).toBeVisible();
  expect(screen.getByRole("button",{name:"Bind Context declaration"})).toBeDisabled();
  expect(screen.getByRole("button",{name:"Bind Evidence declaration"})).toBeDisabled();
  expect(screen.getByRole("button",{name:"Evaluate exact readiness"})).toBeDisabled();
});
