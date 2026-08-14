export type ResultState = "success" | "protected" | "invalid" | "unavailable" | "error";
export type ApiResult<T> = { state: "success"; data: T } | { state: Exclude<ResultState, "success"> };

export interface Paginated<T> { items: T[]; total: number; page: number; size: number }
export interface Person { id: number; username: string; full_name: string | null }
export interface Project {
  id: number; project_code: string; name: string; description: string | null;
  customer: { id: number; name: string }; status: string; priority: string;
  owner: Person | null; primary_assignee: Person | null; progress: number;
  target_completion_date: string | null; updated_at: string;
}
export interface Workspace {
  id: number; project_id: number; project_code: string; project_name: string;
  discipline: string; display_name: string; description: string | null;
  status: string; version: number; updated_at: string; allowed_actions: string[];
}
export interface Capture {
  id: string; project_id: number; workspace_id: number | null; discipline: string | null;
  source_kind: string; lifecycle: string; version: number; original_content?: string;
  created_at: string; updated_at: string;
}
export interface TechnicalReport {
  id: string; workspace_id: number; project_id: number | null; purpose: string;
  lifecycle: string; version: number; is_preliminary: boolean; updated_at: string;
}
export interface MemorySummary {
  memory_id: string; version: number; standing: "active"; source_report_id: string;
  purpose: string; workspace_id: number; project_id: number | null; admitted_at: string; updated_at: string;
}
export interface MemoryPage { outcome: string; page?: { items: MemorySummary[]; visible_total: number; next_continuation: string | null } }
export interface JournalWorkspace { view: string; availability: string; result_state: string; view_content: unknown }
export interface AdviceProposal {
  advisory: true; suggested_text: string; observations: string[]; assumptions: string[];
  missing_information: string[]; confidence: string; confidence_rationale: string;
  limitations: string[]; recommended_next_step: string;
  capture_attribution: { capture_id: string; version: number; project_id: number; workspace_id: number | null; source_kind: string; updated_at: string };
  provider_attribution: { provider_id: string; model_id: string; model_version: string };
  generated_at: string;
}
export type AdviceResponse = { outcome: "success"; proposal: AdviceProposal } | { outcome: "refused"; refusal_code: string; recommended_next_step: string } | { outcome: "protected_not_found" | "invalid_request" | "disabled" | "unavailable" };
