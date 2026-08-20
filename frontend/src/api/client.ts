import type { AdviceResponse, ApiResult, Capture, Customer, JournalWorkspace, MemoryAdmissionResult, MemoryDetailResult, MemoryPage, Paginated, Project, ReportContent, ReportProvenance, ReportQualification, ReportSourceCandidatePage, TechnicalReport, TechnicalReportAccepted, TechnicalReportDetail, TechnicalReportDraft, Workspace } from "./types";

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
  if (init.body && !(init.body instanceof URLSearchParams)) headers.set("Content-Type", "application/json");
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

async function closedResult<T extends { outcome: string }>(path: string, init: RequestInit = {}): Promise<ApiResult<T>> {
  const result = await request<T>(path, init);
  if (result.state !== "success") return result;
  if (result.data.outcome === "protected_not_found") return { state: "protected" };
  if (result.data.outcome === "invalid_request") return { state: "invalid" };
  if (result.data.outcome === "unavailable") return { state: "unavailable" };
  if (["version_conflict", "idempotency_conflict", "duplicate_source", "invalid_standing"].includes(result.data.outcome)) return { state: "conflict" };
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
  me: () => request<{ user_id: string }>("/auth/me"),
  customers: () => request<Paginated<Customer>>("/customers/?page=1&size=100"),
  createCustomer: (payload: { name: string; company?: string | null; phone?: string | null; email?: string | null }) => request<Customer>("/customers/", { method: "POST", body: JSON.stringify(payload) }),
  updateCustomer: (id: number, payload: Partial<Pick<Customer, "name" | "company" | "phone" | "email">>) => request<Customer>(`/customers/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  projects: () => request<Paginated<Project>>("/projects/?page=1&size=20&sort_by=updated_at&order=desc"),
  createProject: (payload: { name: string; customer_id: number; description?: string | null; priority?: string; start_date?: string | null; target_completion_date?: string | null }) => request<Project>("/projects/", { method: "POST", body: JSON.stringify(payload) }),
  updateProject: (id: number, payload: { name?: string; description?: string | null; customer_id?: number; priority?: string; start_date?: string | null; target_completion_date?: string | null }) => request<Project>(`/projects/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  project: (id: number) => request<Project>(`/projects/${id}`),
  workspaces: (id: number) => request<{ items: Workspace[]; total: number }>(`/projects/${id}/workspaces?page=1&size=20`),
  createWorkspace: (projectId: number, payload: { discipline: string; description?: string | null }) => request<Workspace>(`/projects/${projectId}/workspaces`, { method: "POST", body: JSON.stringify(payload) }),
  captures: (id: number) => request<{ items: Capture[]; total: number }>(`/projects/${id}/engineering-experience-captures?page=1&size=20`),
  createCapture: (payload: { project_id: number; workspace_id: number; source_kind: string; original_content: string; source_reference?: string | null }) => request<Capture>("/engineering-experience-captures", { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ ...payload, engineering_object_id: null }) }),
  journal: (projectId?: number) => request<JournalWorkspace>(`/api/v1/engineering-journal${projectId ? `?project_id=${projectId}` : ""}`),
  reports: (workspaceId: number, projectId?: number) => request<{ items: TechnicalReport[]; total: number }>(`/technical-reports?workspace_id=${workspaceId}${projectId ? `&project_id=${projectId}` : ""}&page=1&size=20`),
  report: (id: string) => request<TechnicalReportDetail>(`/technical-reports/${encodeURIComponent(id)}`),
  reportSources: (projectId: number, workspaceId: number) => request<ReportSourceCandidatePage>(`/technical-reports/capture-source-candidates?project_id=${projectId}&workspace_id=${workspaceId}&page=1&size=20`),
  createReport: (payload: { workspace_id: number; project_id: number; purpose: string; content: ReportContent; qualification: ReportQualification; provenance: ReportProvenance[] }) => request<TechnicalReportDraft>("/technical-reports", { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) }),
  reviseReport: (id: string, payload: { expected_version: number; expected_draft_revision_id: string; content: ReportContent; qualification: ReportQualification; provenance: ReportProvenance[]; rationale: string }) => request<TechnicalReportDraft>(`/technical-reports/${encodeURIComponent(id)}/draft-revisions`, { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) }),
  acceptReport: (id: string, payload: { expected_version: number; exact_draft_revision_id: string; confirmed: true; rationale: string }) => request<TechnicalReportAccepted>(`/technical-reports/${encodeURIComponent(id)}/acceptance`, { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) }),
  memory: (workspaceId: number, projectId?: number) => closedResult<MemoryPage>(`/organizational-memory?workspace_id=${workspaceId}${projectId ? `&project_id=${projectId}` : ""}&page_size=20`),
  memoryDetail: (id: string) => closedResult<MemoryDetailResult>(`/organizational-memory/${encodeURIComponent(id)}?include_provenance=true&reuse_intent=true`),
  admitMemory: (payload: { report_id: string; accepted_aggregate_version: number; accepted_snapshot_digest: string; workspace_id: number; project_id: number | null; admission_rationale: string; authority_rationale: string; reuse_restrictions: string[] }) => closedResult<MemoryAdmissionResult>("/organizational-memory/admissions", { method: "POST", headers: { "X-Correlation-ID": crypto.randomUUID(), "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ ...payload, audience_actor_ids: [] }) }),
  advice: (payload: { capture_id: string; project_id: number; workspace_id: number | null; human_instruction: string }) => request<AdviceResponse>("/engineering-copilot/capture-advice", { method: "POST", body: JSON.stringify(payload) }),
};
