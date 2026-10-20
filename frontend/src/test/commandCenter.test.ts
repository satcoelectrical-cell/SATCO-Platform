import { retentionApi } from "../services/retentionApi";
import { api } from "../api/client";
import { commandMetrics, loadCommandCenter, orderedProjectWork } from "../dashboard/commandCenter";
import type { Project } from "../api/types";

vi.mock("../services/retentionApi",()=>({retentionApi:{workbench:vi.fn()}}));

vi.mock("../api/client", () => ({ api: {
  projects: vi.fn(), workspaces: vi.fn(), captures: vi.fn(), journal: vi.fn(), reports: vi.fn(), memory: vi.fn(), effectiveDisciplinePackages:vi.fn(), crossDisciplineAssessments:vi.fn(), projectStandards:vi.fn(), engineeringPerformanceHealth:vi.fn(), engineeringPerformanceActions:vi.fn(), evidence:vi.fn(),
} }));

const project = (id: number, priority = "medium", updated_at = "2026-08-14T00:00:00Z"): Project => ({
  id, project_code: `P-${id}`, name: `Project ${id}`, description: null, customer: { id, name: `Customer ${id}` }, status: "active", priority,
  owner: null, primary_assignee: null, progress: 40, target_completion_date: null, updated_at,
});

describe("bounded Command Center composition", () => {
  beforeEach(() => { vi.resetAllMocks(); vi.mocked(api.effectiveDisciplinePackages).mockResolvedValue({state:"success",data:{project_id:1,items:[]}}); vi.mocked(api.crossDisciplineAssessments).mockResolvedValue({state:"success",data:{items:[],next_cursor:null}}); vi.mocked(api.projectStandards).mockResolvedValue({state:"success",data:{items:[],next_cursor:null}}); vi.mocked(api.engineeringPerformanceHealth).mockResolvedValue({state:"success",data:{}}); vi.mocked(api.engineeringPerformanceActions).mockResolvedValue({state:"success",data:{actions:[]}}); vi.mocked(retentionApi.workbench).mockResolvedValue({state:"success",data:{project_id:1,workspace_id:5,evidence:[],supporting_files:[],visible_count:0}}); vi.mocked(api.evidence).mockResolvedValue({state:"success",data:{items:[],total:0,page:1,size:100}}); });
  it("fails closed after a protected project read without downstream calls", async () => {
    vi.mocked(api.projects).mockResolvedValue({ state: "protected" });
    expect(await loadCommandCenter()).toEqual({ state: "protected" });
    expect(api.workspaces).not.toHaveBeenCalled(); expect(api.captures).not.toHaveBeenCalled();
  });
  it("uses a constant bounded fan-out and retains bounded visible records", async () => {
    vi.mocked(api.projects).mockResolvedValue({ state: "success", data: { items: Array.from({ length: 12 }, (_, i) => project(i + 1)), total: 99, page: 1, size: 20 } });
    vi.mocked(api.workspaces).mockResolvedValue({ state: "success", data: { items: [{ id: 2, project_id: 1, project_code: "P-1", project_name: "Project 1", discipline: "control", display_name: "Control", description: null, status: "active", version: 1, updated_at: "2026-08-14T00:00:00Z", allowed_actions: [] }], total: 50 } });
    vi.mocked(api.captures).mockResolvedValue({ state: "success", data: { items: [], total: 50 } });
    vi.mocked(api.journal).mockResolvedValue({ state: "success", data: { view: "inbox", availability: "available", result_state: "success", view_content: {} } });
    vi.mocked(api.reports).mockResolvedValue({ state: "success", data: { items: [], total: 50 } });
    vi.mocked(api.memory).mockResolvedValue({ state: "success", data: { outcome: "success", page: { items: [], visible_total: 0, next_continuation: null } } });
    const result = await loadCommandCenter({projectId:1,workspaceId:2});
    expect(result.state).toBe("success"); if (result.state === "success") expect(result.data.projects).toHaveLength(12);
    expect(api.projects).toHaveBeenCalledTimes(1); expect(api.effectiveDisciplinePackages).toHaveBeenCalledTimes(1); expect(api.crossDisciplineAssessments).toHaveBeenCalledTimes(1); expect(api.projectStandards).toHaveBeenCalledTimes(1); expect(api.engineeringPerformanceHealth).toHaveBeenCalledTimes(1);
    const boundedCalls=[api.projects,api.workspaces,api.captures,api.journal,api.effectiveDisciplinePackages,api.crossDisciplineAssessments,api.projectStandards,api.engineeringPerformanceHealth,api.engineeringPerformanceActions,api.reports,api.memory,api.evidence,retentionApi.workbench].reduce((n,fn)=>n+vi.mocked(fn).mock.calls.length,0);
    expect(boundedCalls).toBe(13);
  });
  it("isolates a protected intelligence owner without hiding successful sibling slices", async () => {
    vi.mocked(api.projects).mockResolvedValue({state:"success",data:{items:[project(1)],total:1,page:1,size:20}});
    vi.mocked(api.workspaces).mockResolvedValue({state:"success",data:{items:[],total:0}}); vi.mocked(api.captures).mockResolvedValue({state:"success",data:{items:[],total:0}}); vi.mocked(api.journal).mockResolvedValue({state:"success",data:{view:"inbox",availability:"available",result_state:"success",view_content:{}}});
    vi.mocked(api.projectStandards).mockResolvedValue({state:"protected"});
    const result=await loadCommandCenter({projectId:1});
    expect(result.state).toBe("success");
    if(result.state==="success"){expect(result.data.intelligence.standards.state).toBe("protected");expect(result.data.intelligence.packages.state).toBe("empty");expect(result.data.intelligence.performance.state).toBe("ready");}
  });
  it("preserves bounded-source completeness states", async () => {
    vi.mocked(api.projects).mockResolvedValue({state:"success",data:{items:[project(1)],total:1,page:1,size:20}});
    vi.mocked(api.workspaces).mockResolvedValue({state:"success",data:{items:[{id:5,project_id:1,project_code:"P-1",project_name:"Project 1",discipline:"control",display_name:"Control",description:null,status:"active",version:1,updated_at:"2026-08-14T00:00:00Z",allowed_actions:[]}],total:1}});
    vi.mocked(api.captures).mockResolvedValue({state:"success",data:{items:[],total:0}});
    vi.mocked(api.journal).mockResolvedValue({state:"success",data:{view:"inbox",availability:"available",result_state:"success",view_content:{}}});
    vi.mocked(api.crossDisciplineAssessments).mockResolvedValue({state:"success",data:{items:[],next_cursor:"next"}});
    vi.mocked(api.projectStandards).mockResolvedValue({state:"success",data:{items:[],next_cursor:"next"}});
    vi.mocked(api.evidence).mockResolvedValue({state:"success",data:{items:[],total:12,page:1,size:100}});
    vi.mocked(api.reports).mockResolvedValue({state:"success",data:{items:[],total:0}});
    vi.mocked(api.memory).mockResolvedValue({state:"success",data:{outcome:"success",page:{items:[],visible_total:0,next_continuation:null}}});
    const result=await loadCommandCenter({projectId:1,workspaceId:5});
    if(result.state==="success"){expect(result.data.intelligence.xdi.state).toBe("partial");expect(result.data.intelligence.standards.state).toBe("partial");expect(result.data.intelligence.evidence.state).toBe("partial");expect(result.data.intelligence.retention.state).toBe("indeterminate");}
  });
  it("does not fan out for an unselected or non-visible Project", async () => {
    vi.mocked(api.projects).mockResolvedValue({state:"success",data:{items:[project(1)],total:1,page:1,size:20}});
    const result=await loadCommandCenter({projectId:999});
    expect(result.state).toBe("success");
    expect(api.workspaces).not.toHaveBeenCalled(); expect(api.effectiveDisciplinePackages).not.toHaveBeenCalled(); expect(api.engineeringPerformanceActions).not.toHaveBeenCalled(); expect(retentionApi.workbench).not.toHaveBeenCalled();
  });
  it("does not request scoped sources without a visible workspace", async () => {
    vi.mocked(api.projects).mockResolvedValue({ state: "success", data: { items: [project(1)], total: 1, page: 1, size: 20 } });
    vi.mocked(api.workspaces).mockResolvedValue({ state: "protected" }); vi.mocked(api.captures).mockResolvedValue({ state: "protected" }); vi.mocked(api.journal).mockResolvedValue({ state: "protected" });
    const result = await loadCommandCenter({projectId:1}); expect(result.state).toBe("success");
    expect(api.reports).not.toHaveBeenCalled(); expect(api.memory).not.toHaveBeenCalled();
  });
});

describe("truthful visible-item derivation", () => {
  it("ignores hidden totals and derives exact visible counts", () => {
    const data = { projects: [project(1, "high"), project(2, "low", "2026-07-01T00:00:00Z")], workspaces: [], captures: [], reports: [], memory: [], journalState: "success" as const, sourceStates: { projects: "success", workspaces: "success", captures: "success", reports: "not_requested", memory: "not_requested" } as const, sliceStates:{projects:"ready",workspaces:"empty",captures:"empty",reports:"not_requested",memory:"not_requested"} as const, intelligence:{packages:{state:"not_requested"},xdi:{state:"not_requested"},standards:{state:"not_requested"},evidence:{state:"not_requested"},retention:{state:"not_requested"},performance:{state:"not_requested"},actions:{state:"not_requested"}} as const, selectedProjectId:null, selectedWorkspaceId:null };
    expect(commandMetrics(data, new Date("2026-08-15T00:00:00Z")).map((m) => m.value)).toEqual([2, 1, 1, 0]);
  });
  it("orders priority then update deterministically", () => expect(orderedProjectWork([project(2, "low"), project(3, "high", "2026-08-13T00:00:00Z"), project(1, "high")]).map((p) => p.id)).toEqual([1, 3, 2]));
});
