export type ResultState = "success" | "protected" | "invalid" | "conflict" | "unavailable" | "error";
export type ApiResult<T> = { state: "success"; data: T } | { state: Exclude<ResultState, "success"> };

export interface Paginated<T> { items: T[]; total: number; page: number; size: number }
export interface Person { id: number; username: string; full_name: string | null }
export interface Customer {
  id: number; name: string; company: string | null; phone: string | null;
  email: string | null; created_at: string;
}
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
  id: string; organization_id: string; workspace_id: number; project_id: number | null;
  owner_id: number; purpose: string; lifecycle: "draft" | "accepted"; version: number;
  draft_revision_id: string; is_preliminary: boolean; predecessor_report_id: string | null;
  created_at: string; updated_at: string; allowed_actions: string[];
}
export interface ReportContent { engineering_scope: string; technical_content: string; assumptions: string[]; uncertainty: string; limitations: string[]; conclusions: string; recommendations: string[] }
export interface ReportQualification { is_preliminary: boolean; evidence_deficiencies: string[]; unresolved_issues: string[]; follow_up_requirements: string[] }
export interface ReportProvenance { entry_id: string; ordinal: number; source_class: string; source_type: string; is_material: boolean; owning_capability: string | null; reliance_role: string; verification_status: string; availability_status: string; origin_attribution: string; limitations: string[]; locator: Record<string, unknown>; integrity_algorithm: string | null; integrity_digest: string | null }
export interface TechnicalReportDraft extends TechnicalReport { lifecycle: "draft"; content: ReportContent; qualification: ReportQualification; provenance: ReportProvenance[] }
export interface AcceptedReportSnapshot { report_id: string; purpose: string; organization_id: string; workspace_id: number; project_id: number | null; content: ReportContent; qualification: ReportQualification; provenance: ReportProvenance[]; accepted_draft_revision_id: string; accepted_aggregate_version: number; accepted_by_id: number; accepted_at: string; predecessor_report_id: string | null; integrity_digest: string }
export interface TechnicalReportAccepted extends TechnicalReport { lifecycle: "accepted"; accepted_snapshot: AcceptedReportSnapshot; accepted_by_id: number; accepted_at: string; accepted_draft_revision_id: string; accepted_aggregate_version: number }
export type TechnicalReportDetail = TechnicalReportDraft | TechnicalReportAccepted;
export interface ReportSourceCandidate { capture_id: string; project_id: number; workspace_id: number; source_kind: string; version: number; created_at: string; preview: string; provenance: ReportProvenance }
export interface ReportSourceCandidatePage { items: ReportSourceCandidate[]; total: number; page: number; size: number }
export interface SupportingFile {
  id: string; organization_id: string; project_id: number; workspace_id: number | null;
  safe_filename: string; media_type: string; byte_size: number; digest_algorithm: "sha256";
  content_digest: string; lifecycle: "quarantined" | "available" | "rejected" | "withdrawn";
  version: number; uploader_id: number; uploaded_at: string; scanned_at: string | null;
  predecessor_asset_id: string | null; allowed_actions: string[];
}
export interface SupportingFilePage { items: SupportingFile[]; visible_count: number; continuation: string | null }
export interface EvidenceRecord {
  id: string; organization_id: string; project_id: number | null; workspace_id: number | null;
  lifecycle: "proposed" | "current" | "withdrawn" | "superseded"; source_kind: string;
  source_reference: string; source_revision: string; source_standing: string;
  effective_at: string | null; supported_fact: string; creator_id: number; version: number;
  created_at: string; updated_at: string; allowed_actions: string[];
}
export interface EvidenceCandidate {
  evidence_id: string; project_id: number; workspace_id: number | null; source_kind: string;
  version: number; updated_at: string; preview: string; supporting_file_count: number;
  provenance: ReportProvenance;
}
export interface EvidenceCandidatePage { items: EvidenceCandidate[]; total: number; page: number; size: number }
export interface MemorySummary {
  memory_id: string; version: number; standing: "active"; source_report_id: string;
  source_accepted_version: number; purpose: string; organization_id: string; workspace_id: number; project_id: number | null;
  admitted_by_id: number; admitted_at: string; updated_at: string;
}
export interface MemoryPage { outcome: string; page?: { items: MemorySummary[]; visible_total: number; next_continuation: string | null } }
export interface MemorySafeProvenance { entry_id: string; ordinal: number; source_class: "canonical_material"; source_type: string; owning_capability: string; is_material: true; reliance_role: string; locator_digest: string; source_integrity_algorithm: "sha256"; source_integrity_digest: string }
export interface MemoryProjection { projection_contract: "organizational_memory.accepted_report.v1"; report_id: string; purpose: string; organization_id: string; workspace_id: number; project_id: number | null; content: ReportContent; qualification: ReportQualification; accepted_draft_revision_id: string; accepted_draft_revision_number: number; accepted_aggregate_version: number; accepted_by_id: number; accepted_at: string; predecessor_report_id: string | null }
export interface MemoryDetail { summary: MemorySummary; projection: MemoryProjection; admission_rationale: string; reuse_restrictions: string[]; safe_provenance: MemorySafeProvenance[] }
export interface MemoryDetailResult { outcome: string; item?: MemoryDetail }
export interface MemoryAdmissionResult { outcome: string; memory_id?: string; version?: number; standing?: "active" }
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
export interface OrganizationProfile { id: string; name: string; slug: string }
export interface UserProfile { user_id: string; username: string; full_name: string | null; role: "admin" | "engineer"; organization: OrganizationProfile }
export interface OrganizationMember { user_id: number; username: string; email: string; full_name: string | null; role: "admin" | "engineer"; account_active: boolean; activation_pending: boolean; membership_enabled: boolean; membership_selected: boolean; version: number }
export type ProjectStage = "definition" | "preparation" | "execution" | "verification" | "completion_readiness";
export type ProjectInputStanding = "missing" | "received" | "clarification_required" | "not_applicable";
export interface ProjectFoundationSource { kind: "supporting_file" | "evidence"; source_id: string; version: number; workspace_id: number | null }
export interface ProjectFoundationOrderedText { id:string; ordinal:number; statement:string }
export interface ProjectFoundationInput { id:string; title:string; description:string|null; ordinal:number; required_by_stage:ProjectStage; standing:ProjectInputStanding; source_condition:"not_required"|"authorized_current"|"source_reauthorization_required"; source:ProjectFoundationSource|null; version:number; standing_changed_at:string; updated_at:string }
export interface ProjectFoundationBlocker { code:string; input_id:string|null; input_title:string|null }
export interface ProjectFoundationEstablished { outcome:"success"; availability:"established"; project_id:number; version:number; purpose:string; engineering_basis:string; stage:ProjectStage; in_scope:ProjectFoundationOrderedText[]; out_of_scope:ProjectFoundationOrderedText[]; completion_criteria:ProjectFoundationOrderedText[]; inputs:ProjectFoundationInput[]; next_stage_readiness:{state:"ready"|"blocked"|"not_applicable";target_stage:ProjectStage|null;blockers:ProjectFoundationBlocker[]}; allowed_actions:string[]; established_at:string; updated_at:string }
export interface ProjectFoundationNotEstablished { outcome:"success"; availability:"basis_not_established"; project_id:number; allowed_actions:string[] }
export type ProjectFoundation = ProjectFoundationEstablished | ProjectFoundationNotEstablished;
export interface ProjectFoundationSourceCandidate { kind:"supporting_file"|"evidence"; source_id:string; version:number; workspace_id:number|null; display_label:string }
export interface ProjectFoundationSourcePage { outcome:"success"; items:ProjectFoundationSourceCandidate[]; visible_count:number }
export interface IssuedCredential { outcome: string; organization?: OrganizationProfile & { is_active: boolean }; member?: OrganizationMember; one_time_token?: string; replayed?: boolean }
export interface MemberList { outcome: string; items: OrganizationMember[] }
