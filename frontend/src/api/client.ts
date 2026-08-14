import type { AdviceResponse, ApiResult, Capture, JournalWorkspace, MemoryPage, Paginated, Project, TechnicalReport, Workspace } from "./types";

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
    if (response.status === 503) return { state: "unavailable" };
    if (!response.ok) return { state: "error" };
    return { state: "success", data: await response.json() as T };
  } catch { return { state: "unavailable" }; }
}

async function closedResult<T extends { outcome: string }>(path: string): Promise<ApiResult<T>> {
  const result = await request<T>(path);
  if (result.state !== "success") return result;
  if (result.data.outcome === "protected_not_found") return { state: "protected" };
  if (result.data.outcome === "invalid_request") return { state: "invalid" };
  if (result.data.outcome === "unavailable") return { state: "unavailable" };
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
  projects: () => request<Paginated<Project>>("/projects/?page=1&size=20&sort_by=updated_at&order=desc"),
  project: (id: number) => request<Project>(`/projects/${id}`),
  workspaces: (id: number) => request<{ items: Workspace[]; total: number }>(`/projects/${id}/workspaces?page=1&size=20`),
  captures: (id: number) => request<{ items: Capture[]; total: number }>(`/projects/${id}/engineering-experience-captures?page=1&size=20`),
  journal: (projectId?: number) => request<JournalWorkspace>(`/api/v1/engineering-journal${projectId ? `?project_id=${projectId}` : ""}`),
  reports: (workspaceId: number, projectId?: number) => request<{ items: TechnicalReport[]; total: number }>(`/technical-reports?workspace_id=${workspaceId}${projectId ? `&project_id=${projectId}` : ""}&page=1&size=20`),
  memory: (workspaceId: number, projectId?: number) => closedResult<MemoryPage>(`/organizational-memory?workspace_id=${workspaceId}${projectId ? `&project_id=${projectId}` : ""}&page_size=20`),
  advice: (payload: { capture_id: string; project_id: number; workspace_id: number | null; human_instruction: string }) => request<AdviceResponse>("/engineering-copilot/capture-advice", { method: "POST", body: JSON.stringify(payload) }),
};
