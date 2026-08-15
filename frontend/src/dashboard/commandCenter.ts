import { api } from "../api/client";
import type { ApiResult, Capture, MemorySummary, Project, TechnicalReport, Workspace } from "../api/types";

export type SourceState = "success" | "protected" | "invalid" | "unavailable" | "error" | "not_requested";

export interface CommandCenterData {
  projects: Project[];
  workspaces: Workspace[];
  captures: Capture[];
  reports: TechnicalReport[];
  memory: MemorySummary[];
  journalState: SourceState;
  sourceStates: Record<"projects" | "workspaces" | "captures" | "reports" | "memory", SourceState>;
}

export interface CommandMetric { label: string; value: number; detail: string; tone: "gold" | "green" | "blue" | "neutral" }

const stateOf = (result: ApiResult<unknown>): SourceState => result.state;

export async function loadCommandCenter(): Promise<ApiResult<CommandCenterData>> {
  const projectsResult = await api.projects();
  if (projectsResult.state !== "success") return projectsResult;
  const projects = projectsResult.data.items.slice(0, 8);
  const empty: CommandCenterData = {
    projects, workspaces: [], captures: [], reports: [], memory: [], journalState: "not_requested",
    sourceStates: { projects: "success", workspaces: "not_requested", captures: "not_requested", reports: "not_requested", memory: "not_requested" },
  };
  const primary = projects[0];
  if (!primary) return { state: "success", data: empty };

  const [workspaceResult, captureResult, journalResult] = await Promise.all([
    api.workspaces(primary.id), api.captures(primary.id), api.journal(primary.id),
  ]);
  const workspaces = workspaceResult.state === "success" ? workspaceResult.data.items.slice(0, 8) : [];
  const captures = captureResult.state === "success" ? captureResult.data.items.slice(0, 20) : [];
  const workspace = workspaces[0];
  let reportsResult: Awaited<ReturnType<typeof api.reports>> | null = null;
  let memoryResult: Awaited<ReturnType<typeof api.memory>> | null = null;
  if (workspace) {
    [reportsResult, memoryResult] = await Promise.all([api.reports(workspace.id, primary.id), api.memory(workspace.id, primary.id)]);
  }
  return { state: "success", data: {
    projects, workspaces, captures,
    reports: reportsResult?.state === "success" ? reportsResult.data.items.slice(0, 3) : [],
    memory: memoryResult?.state === "success" ? (memoryResult.data.page?.items ?? []).slice(0, 3) : [],
    journalState: stateOf(journalResult),
    sourceStates: {
      projects: "success", workspaces: stateOf(workspaceResult), captures: stateOf(captureResult),
      reports: reportsResult ? stateOf(reportsResult) : "not_requested",
      memory: memoryResult ? stateOf(memoryResult) : "not_requested",
    },
  } };
}

export function commandMetrics(data: CommandCenterData, now = new Date()): CommandMetric[] {
  const cutoff = now.getTime() - 7 * 24 * 60 * 60 * 1000;
  const recent = data.projects.filter((project) => {
    const value = Date.parse(project.updated_at);
    return Number.isFinite(value) && value >= cutoff && value <= now.getTime();
  }).length;
  return [
    { label: "Visible projects", value: data.projects.length, detail: "Authorized bounded view", tone: "gold" },
    { label: "High priority", value: data.projects.filter((p) => ["high", "critical"].includes(p.priority.toLowerCase())).length, detail: "Canonical priority", tone: "blue" },
    { label: "Recently updated", value: recent, detail: "Project updates · 7 days", tone: "green" },
    { label: "Capture contexts", value: data.captures.length, detail: "Available for Human-led work", tone: "neutral" },
  ];
}

export function orderedProjectWork(projects: Project[]): Project[] {
  const rank = (priority: string) => ({ critical: 0, high: 1, medium: 2, low: 3 }[priority.toLowerCase()] ?? 4);
  return [...projects].sort((a, b) => rank(a.priority) - rank(b.priority) || Date.parse(b.updated_at) - Date.parse(a.updated_at) || a.id - b.id).slice(0, 5);
}
