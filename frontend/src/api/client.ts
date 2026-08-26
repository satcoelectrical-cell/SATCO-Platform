import type { AdviceResponse, ApiResult, Capture, ChangeImpactMutation, ContextNode, ContextNodeKind, Customer, DeliverableMutation, DeliverableRegister, EvidenceCandidatePage, EvidenceRecord, ExecutionActivityStanding, ExecutionMutation, ExecutionPlan, IssuedCredential, JournalWorkspace, MemberList, MemoryAdmissionResult, MemoryDetailResult, MemoryPage, OneHopSuccess, Paginated, Project, ProjectContextSectionKind, ProjectContextSuccess, ProjectControl, ProjectControlHistory, ProjectControlKind, ProjectControlList, ProjectControlMutation, ProjectFoundation, ProjectFoundationInput, ProjectFoundationSourcePage, ProjectStage, ReportContent, ReportProvenance, ReportQualification, ReportSourceCandidatePage, SupportingFile, SupportingFilePage, TechnicalReport, TechnicalReportAccepted, TechnicalReportDetail, TechnicalReportDraft, UserProfile, Workspace } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const TOKEN_KEY = "satco.auth.access.v1";

export const authSession = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

async function request<T>(path: string, init: RequestInit = {}): Promise<ApiResult<T>> {
  const token = authSession.get();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof URLSearchParams) && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
    if (response.status === 401) { authSession.clear(); return { state: "protected" }; }
    if (response.status === 403 || response.status === 404) return { state: "protected" };
    if (response.status === 400 || response.status === 422) return { state: "invalid" };
    if (response.status === 409) return { state: "conflict" };
    if (response.status === 503) return { state: "unavailable" };
    if (!response.ok) return { state: "error" };
    return { state: "success", data: await response.json() as T };
  } catch { return { state: "unavailable" }; }
}

async function downloadRequest(path: string): Promise<ApiResult<Blob>> {
  const token = authSession.get();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  try {
    const response = await fetch(`${API_BASE}${path}`, { headers });
    if ([401, 403, 404].includes(response.status)) return { state: "protected" };
    if ([400, 422].includes(response.status)) return { state: "invalid" };
    if (response.status === 503) return { state: "unavailable" };
    if (!response.ok) return { state: "error" };
    return { state: "success", data: await response.blob() };
  } catch { return { state: "unavailable" }; }
}

async function closedResult<T extends { outcome: string }>(path: string, init: RequestInit = {}): Promise<ApiResult<T>> {
  const result = await request<T>(path, init);
  if (result.state !== "success") return result;
  if (result.data.outcome === "protected_not_found") return { state: "protected" };
  if (result.data.outcome === "invalid_request") return { state: "invalid" };
  if (result.data.outcome === "unavailable") return { state: "unavailable" };
  if (["version_conflict", "idempotency_conflict", "duplicate_source", "invalid_standing"].includes(result.data.outcome)) return { state: "conflict" };
  return result;
}

async function closedStatusResult<T extends { status: string }>(path:string):Promise<ApiResult<T>> {
  const result=await request<T>(path);
  if(result.state!=="success") return result;
  if(result.data.status==="protected_not_found") return {state:"protected"};
  if(result.data.status==="invalid_request") return {state:"invalid"};
  if(result.data.status==="unavailable") return {state:"unavailable"};
  return result;
}

export async function login(username: string, password: string): Promise<ApiResult<true>> {
  const body = new URLSearchParams({ username, password });
  const result = await request<{ access_token: string }>("/auth/login", { method: "POST", body });
  if (result.state !== "success") return result;
  authSession.set(result.data.access_token);
  return { state: "success", data: true };
}

export const api = {
  me: () => request<UserProfile>("/auth/me"),
  bootstrapOrganization: (payload: { organization_name: string; organization_slug: string; admin_username: string; admin_email: string; admin_full_name?: string }, bootstrapKey: string) => closedResult<IssuedCredential>("/platform/bootstrap/organizations", { method: "POST", headers: { "X-SATCO-Bootstrap-Key": bootstrapKey, "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) }),
  activateAccount: (token: string, newPassword: string) => closedResult<{ outcome: string }>("/auth/activate", { method: "POST", body: JSON.stringify({ token, new_password: newPassword }) }),
  resetAccount: (token: string, newPassword: string) => closedResult<{ outcome: string }>("/auth/reset", { method: "POST", body: JSON.stringify({ token, new_password: newPassword }) }),
  changePassword: (currentPassword: string, newPassword: string) => closedResult<{ outcome: string }>("/auth/change-password", { method: "POST", body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) }),
  members: () => closedResult<MemberList>("/organization-admin/members"),
  provisionMember: (payload: { username: string; email: string; full_name?: string; role: "admin" | "engineer" }) => closedResult<IssuedCredential>("/organization-admin/members", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) }),
  mutateMember: (userId: number, payload: { expected_version: number; role?: "admin" | "engineer"; membership_enabled?: boolean; account_active?: boolean }) => closedResult<IssuedCredential>(`/organization-admin/members/${userId}`, { method: "PATCH", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) }),
  issueMemberReset: (userId: number) => closedResult<IssuedCredential>(`/organization-admin/members/${userId}/reset`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  customers: () => request<Paginated<Customer>>("/customers/?page=1&size=100"),
  createCustomer: (payload: { name: string; company?: string | null; phone?: string | null; email?: string | null }) => request<Customer>("/customers/", { method: "POST", body: JSON.stringify(payload) }),
  updateCustomer: (id: number, payload: Partial<Pick<Customer, "name" | "company" | "phone" | "email">>) => request<Customer>(`/customers/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  projects: () => request<Paginated<Project>>("/projects/?page=1&size=20&sort_by=updated_at&order=desc"),
  createProject: (payload: { name: string; customer_id: number; description?: string | null; priority?: string; start_date?: string | null; target_completion_date?: string | null }) => request<Project>("/projects/", { method: "POST", body: JSON.stringify(payload) }),
  updateProject: (id: number, payload: { name?: string; description?: string | null; customer_id?: number; priority?: string; start_date?: string | null; target_completion_date?: string | null }) => request<Project>(`/projects/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  project: (id: number) => request<Project>(`/projects/${id}`),
  projectContext: (id:number, workspaceId?:number|null, section?:ProjectContextSectionKind, continuation?:string) => closedStatusResult<ProjectContextSuccess>(`/projects/${id}/context?${new URLSearchParams([...(workspaceId ? [["workspace_id",String(workspaceId)]] : []),...(section ? [["section",section],["page_size","100"]] : []),...(continuation ? [["continuation",continuation]] : [])]).toString()}`),
  projectCompleteness: (id:number, workspaceId?:number|null) => closedStatusResult<import("./types").ProjectCompletenessResult>(`/projects/${id}/completeness${workspaceId ? `?workspace_id=${workspaceId}` : ""}`),
  contextNode: (projectId:number, kind:ContextNodeKind, selector:string|number, workspaceId?:number|null) => closedStatusResult<{status:"success";node:ContextNode}>(`/projects/${projectId}/engineering-context/nodes/${kind}/${encodeURIComponent(String(selector))}${workspaceId ? `?workspace_id=${workspaceId}`:""}`),
  relatedContext: (projectId:number, kind:ContextNodeKind, selector:string|number, workspaceId?:number|null, continuation?:string) => closedStatusResult<OneHopSuccess>(`/projects/${projectId}/engineering-context/nodes/${kind}/${encodeURIComponent(String(selector))}/related?${new URLSearchParams([...(workspaceId ? [["workspace_id",String(workspaceId)]] : []),...(continuation ? [["continuation",continuation]] : [])]).toString()}`),
  projectFoundation: (id:number) => closedResult<ProjectFoundation>(`/projects/${id}/foundation`),
  putProjectFoundation: (id:number,payload:{expected_version:number;purpose:string;engineering_basis:string;in_scope:string[];out_of_scope:string[];completion_criteria:string[];rationale:string}) => closedResult<ProjectFoundation>(`/projects/${id}/foundation`,{method:"PUT",body:JSON.stringify(payload)}),
  createProjectInput: (id:number,payload:{expected_foundation_version:number;title:string;description:string|null;ordinal:number;required_by_stage:ProjectStage;rationale:string}) => closedResult<{outcome:"success";project_id:number;foundation_version:number;item:ProjectFoundationInput}>(`/projects/${id}/foundation/inputs`,{method:"POST",body:JSON.stringify(payload)}),
  updateProjectInput: (id:number,inputId:string,payload:{expected_foundation_version:number;expected_input_version:number;title:string;description:string|null;ordinal:number;required_by_stage:ProjectStage;rationale:string}) => closedResult<{outcome:"success";project_id:number;foundation_version:number;item:ProjectFoundationInput}>(`/projects/${id}/foundation/inputs/${encodeURIComponent(inputId)}`,{method:"PUT",body:JSON.stringify(payload)}),
  reorderProjectInputs: (id:number,payload:{expected_foundation_version:number;ordered_input_ids:string[];rationale:string}) => closedResult<{outcome:"success";project_id:number;foundation_version:number;ordered_input_ids:string[]}>(`/projects/${id}/foundation/inputs/reorder`,{method:"POST",body:JSON.stringify(payload)}),
  transitionProjectInput: (id:number,inputId:string,payload:{expected_foundation_version:number;expected_input_version:number;target_standing:string;source_kind?:string;source_id?:string;source_workspace_id?:number|null;rationale:string}) => closedResult<{outcome:"success";project_id:number;foundation_version:number;item:ProjectFoundationInput}>(`/projects/${id}/foundation/inputs/${encodeURIComponent(inputId)}/transitions`,{method:"POST",body:JSON.stringify(payload)}),
  transitionProjectStage: (id:number,payload:{expected_foundation_version:number;target_stage:ProjectStage;rationale:string}) => closedResult<{outcome:"success";project_id:number;foundation_version:number;stage:ProjectStage}>(`/projects/${id}/foundation/stage-transitions`,{method:"POST",body:JSON.stringify(payload)}),
  projectInputSources: (id:number,kind:"supporting_file"|"evidence",workspaceId:number|null) => closedResult<ProjectFoundationSourcePage>(`/projects/${id}/foundation/source-candidates?kind=${kind}${workspaceId ? `&workspace_id=${workspaceId}`:""}&limit=50`),
  executionPlan: (id:number) => closedResult<ExecutionPlan>(`/projects/${id}/execution-plan`),
  deliverables: (id:number) => closedResult<DeliverableRegister>(`/projects/${id}/deliverables`),
  createDeliverable: (id:number,payload:{code:string;title:string;discipline:string;deliverable_type:string;purpose:string|null;external_authority:string;workspace_id:number|null;activity_id:string|null;milestone_id:string|null;responsible_user_id:number|null;target_date:string|null;initial_external_label:string;rationale:string}) => closedResult<DeliverableMutation>(`/projects/${id}/deliverables`,{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  establishExecutionPlan: (id:number,payload:{expected_plan_version:0;rationale:string}) => closedResult<ExecutionMutation>(`/projects/${id}/execution-plan`,{method:"PUT",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  createExecutionActivity: (id:number,payload:{expected_plan_version:number;title:string;description:string|null;ordinal:number;workspace_id:number|null;responsible_user_id:number|null;target_date:string|null;completion_basis:string;rationale:string}) => closedResult<ExecutionMutation>(`/projects/${id}/execution-plan/activities`,{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  updateExecutionActivity: (id:number,activityId:string,payload:{expected_plan_version:number;expected_activity_version:number;title:string;description:string|null;ordinal:number;workspace_id:number|null;responsible_user_id:number|null;target_date:string|null;completion_basis:string;rationale:string}) => closedResult<ExecutionMutation>(`/projects/${id}/execution-plan/activities/${encodeURIComponent(activityId)}`,{method:"PUT",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  transitionExecutionActivity: (id:number,activityId:string,payload:{expected_activity_version:number;target_standing:ExecutionActivityStanding;rationale:string}) => closedResult<ExecutionMutation>(`/projects/${id}/execution-plan/activities/${encodeURIComponent(activityId)}/transitions`,{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  replaceExecutionDependencies: (id:number,payload:{expected_plan_version:number;dependencies:{predecessor_activity_id:string;dependent_activity_id:string}[];rationale:string}) => closedResult<ExecutionMutation>(`/projects/${id}/execution-plan/dependencies`,{method:"PUT",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  createExecutionMilestone: (id:number,payload:{expected_plan_version:number;title:string;completion_basis:string;target_date:string|null;ordinal:number;activity_ids:string[];rationale:string}) => closedResult<ExecutionMutation>(`/projects/${id}/execution-plan/milestones`,{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  updateExecutionMilestone: (id:number,milestoneId:string,payload:{expected_plan_version:number;title:string;completion_basis:string;target_date:string|null;ordinal:number;activity_ids:string[];rationale:string}) => closedResult<ExecutionMutation>(`/projects/${id}/execution-plan/milestones/${encodeURIComponent(milestoneId)}`,{method:"PUT",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  projectControls: (projectId:number, kind:ProjectControlKind) => closedResult<ProjectControlList>(`/projects/${projectId}/controls/${kind}`),
  projectControl: (projectId:number, kind:ProjectControlKind, controlId:string) => closedResult<ProjectControl>(`/projects/${projectId}/controls/${kind}/${encodeURIComponent(controlId)}`),
  projectControlHistory: (projectId:number, kind:ProjectControlKind, controlId:string) => closedResult<ProjectControlHistory>(`/projects/${projectId}/controls/${kind}/${encodeURIComponent(controlId)}/history`),
  createProjectControl: (projectId:number, kind:ProjectControlKind, payload:Record<string, unknown>) => closedResult<ProjectControlMutation>(`/projects/${projectId}/controls/${kind}s`,{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  transitionProjectControl: (projectId:number, kind:ProjectControlKind, controlId:string, payload:{target_standing:string;expected_version:number;rationale:string}) => closedResult<ProjectControlMutation>(`/projects/${projectId}/controls/${kind}/${encodeURIComponent(controlId)}/transitions`,{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  createChangeImpact: (projectId:number, changeId:string, payload:Record<string, unknown>) => closedResult<ChangeImpactMutation>(`/projects/${projectId}/controls/changes/${encodeURIComponent(changeId)}/impacts`,{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  confirmChangeImpact: (projectId:number, impactId:string, payload:{expected_change_version:number;deliverable_id?:string;rationale:string}) => closedResult<ChangeImpactMutation>(`/projects/${projectId}/controls/impacts/${encodeURIComponent(impactId)}/confirmations`,{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  workspaces: (id: number) => request<{ items: Workspace[]; total: number }>(`/projects/${id}/workspaces?page=1&size=20`),
  createWorkspace: (projectId: number, payload: { discipline: string; description?: string | null }) => request<Workspace>(`/projects/${projectId}/workspaces`, { method: "POST", body: JSON.stringify(payload) }),
  captures: (id: number) => request<{ items: Capture[]; total: number }>(`/projects/${id}/engineering-experience-captures?page=1&size=20`),
  createCapture: (payload: { project_id: number; workspace_id: number; source_kind: string; original_content: string; source_reference?: string | null }) => request<Capture>("/engineering-experience-captures", { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ ...payload, engineering_object_id: null }) }),
  journal: (projectId?: number) => request<JournalWorkspace>(`/api/v1/engineering-journal${projectId ? `?project_id=${projectId}` : ""}`),
  reports: (workspaceId: number, projectId?: number) => request<{ items: TechnicalReport[]; total: number }>(`/technical-reports?workspace_id=${workspaceId}${projectId ? `&project_id=${projectId}` : ""}&page=1&size=20`),
  report: (id: string) => request<TechnicalReportDetail>(`/technical-reports/${encodeURIComponent(id)}`),
  reportSources: (projectId: number, workspaceId: number) => request<ReportSourceCandidatePage>(`/technical-reports/capture-source-candidates?project_id=${projectId}&workspace_id=${workspaceId}&page=1&size=20`),
  reportEvidenceSources: (projectId: number, workspaceId: number) => request<EvidenceCandidatePage>(`/technical-reports/evidence-source-candidates?project_id=${projectId}&workspace_id=${workspaceId}&page=1&size=20`),
  supportingFiles: (projectId: number, workspaceId: number, continuation?: string) => request<SupportingFilePage>(`/projects/${projectId}/supporting-files?workspace_id=${workspaceId}&limit=20${continuation ? `&continuation=${encodeURIComponent(continuation)}` : ""}`),
  uploadSupportingFile: (projectId: number, workspaceId: number, file: File, rationale: string) => { const body = new FormData(); body.set("project_id", String(projectId)); body.set("workspace_id", String(workspaceId)); body.set("rationale", rationale); body.set("file", file); return request<SupportingFile>("/supporting-files/uploads", { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body }); },
  evidence: (projectId: number, workspaceId: number) => request<{ items: EvidenceRecord[]; total: number; page: number; size: number }>(`/projects/${projectId}/evidence?workspace_id=${workspaceId}&page=1&size=100`),
  linkSupportingFiles: (evidenceId: string, expectedVersion: number, assetIds: string[], rationale: string) => request<EvidenceRecord>(`/evidence/${encodeURIComponent(evidenceId)}/supporting-files`, { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ expected_version: expectedVersion, asset_ids: [...assetIds].sort(), rationale }) }),
  downloadSupportingFile: (assetId: string, projectId: number, workspaceId: number) => downloadRequest(`/supporting-files/${encodeURIComponent(assetId)}/download?project_id=${projectId}&workspace_id=${workspaceId}`),
  downloadHistoricalSupportingFile: (reportId: string, evidenceId: string, assetId: string) => downloadRequest(`/technical-reports/${encodeURIComponent(reportId)}/evidence/${encodeURIComponent(evidenceId)}/supporting-files/${encodeURIComponent(assetId)}/download`),
  createReport: (payload: { workspace_id: number; project_id: number; purpose: string; content: ReportContent; qualification: ReportQualification; provenance: ReportProvenance[] }) => request<TechnicalReportDraft>("/technical-reports", { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) }),
  reviseReport: (id: string, payload: { expected_version: number; expected_draft_revision_id: string; content: ReportContent; qualification: ReportQualification; provenance: ReportProvenance[]; rationale: string }) => request<TechnicalReportDraft>(`/technical-reports/${encodeURIComponent(id)}/draft-revisions`, { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) }),
  acceptReport: (id: string, payload: { expected_version: number; exact_draft_revision_id: string; confirmed: true; rationale: string }) => request<TechnicalReportAccepted>(`/technical-reports/${encodeURIComponent(id)}/acceptance`, { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) }),
  memory: (workspaceId: number, projectId?: number) => closedResult<MemoryPage>(`/organizational-memory?workspace_id=${workspaceId}${projectId ? `&project_id=${projectId}` : ""}&page_size=20`),
  memoryDetail: (id: string) => closedResult<MemoryDetailResult>(`/organizational-memory/${encodeURIComponent(id)}?include_provenance=true&reuse_intent=true`),
  admitMemory: (payload: { report_id: string; accepted_aggregate_version: number; accepted_snapshot_digest: string; workspace_id: number; project_id: number | null; admission_rationale: string; authority_rationale: string; reuse_restrictions: string[] }) => closedResult<MemoryAdmissionResult>("/organizational-memory/admissions", { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ ...payload, audience_actor_ids: [] }) }),
  advice: (payload: { capture_id: string; project_id: number; workspace_id: number | null; human_instruction: string }) => request<AdviceResponse>("/engineering-copilot/capture-advice", { method: "POST", body: JSON.stringify(payload) }),
};
