export type ResultState = "success" | "protected" | "invalid" | "conflict" | "unavailable" | "error";
export type ApiResult<T> = { state: "success"; data: T } | { state: Exclude<ResultState, "success"> };
export interface StandardIdentityView { standard_id:string; catalog_scope:"global_trusted"|"organization_private"; issuer:string; designation:string; title:string; language?:string|null; jurisdiction?:Record<string,unknown>; identity_digest:string; retired_from_new_selection:boolean; editions?:StandardEditionView[] }
export interface StandardEditionView { edition_id:string; standard_id:string; edition_designation:string; edition_disambiguator:string; official_publication_identifier?:string|null; edition_digest:string; standing_history?:Array<{standing:"current"|"superseded"|"withdrawn"|"unknown";observed_effective_at:string;version:number}> }
export interface StandardRightsCapabilities { metadata_visibility:boolean; content_storage:boolean; indexing:boolean; excerpt_display:boolean; source_retrieval:boolean; derived_retention:boolean; derived_current_use:boolean }
export interface StandardRightsView { rights_binding_id:string; edition_id:string; source_provider_id:string; rights_basis:string; rights_status:string; capabilities:StandardRightsCapabilities; ai_processing_permission:string; approved_processor_policy_ids:string[]; effective_from:string; effective_until:string|null; version:number; rights_digest:string }
export interface StandardsPage { items:StandardIdentityView[]; next_cursor:string|null }
export interface StandardsRightsPage { items:StandardRightsView[]; next_cursor:string|null }
export interface StandardApplicability { applicability_id:string; edition_id:string|null; candidate_designation_key?:string|null; status:string; applicability_role:string; rationale_code:string; rationale:string; origin_reference?:string|null; source_candidate_reference?:string|null; revision:number; is_current?:boolean; applicability_digest:string }
export interface StandardCandidate { candidate_id:string; candidate_digest:string; designation_key:string; suggested_role:"informative"|"design_basis"|"mandatory"; rationale_code:string; package_key:string; package_version:string; standard_edition_id:string|null }
export interface StandardSourceSnapshot { snapshot_id:string; edition_id:string; source_location:string; availability_status:string; integrity_verified:boolean; snapshot_digest:string; authorized_handle?:string }
export interface StandardAssertion { assertion_id:string; assertion_kind:string; assertion_digest:string; verification_status:string; version:number; verification_handle:string; rejection_handle:string }
export interface StandardsIntelligenceRun { run_id:string; project_id:number; deterministic:Record<string,string>; deterministic_result_digest:string; result_status:string|null; phase_status:string; advisory:{suggestions:{handle:string;rationale_code:string;advisory:string}[];advisory_only:boolean;human_authority_required:boolean}|null; failure_code:string|null; advisory_only:true; human_authority_required:true }
export interface TechnicalReportStandardCandidate { authorized_handle:string; standard_identity_id:string; edition_id:string; issuer:string; designation:string; edition_designation:string; standing:"current"|"superseded"|"withdrawn"|"unknown"; materiality:"material_support"|"reference_only"; eligibility:"eligible"|"standing_acknowledgement_required"|"rights_restricted"; warnings:string[] }
export interface TechnicalReportStandardsBasisRevision { report_id:string; version:number; draft_revision_id:string; basis_ids:string[] }

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

export interface PackageSelection { package_key:string; package_version:string; descriptor_digest?:string }
export interface SupportedPackage { package_key:string; package_version:string; primary_discipline_id:string; standing:string; descriptor_digest:string }
export interface SupportedPackages { registry_digest:string; items:SupportedPackage[]; next_cursor:string|null }
export interface OrganizationPackageConfiguration { organization_id:string; configuration_version:number; enabled_selections:PackageSelection[]; disabled_selections:PackageSelection[]; registry_digest:string; updated_at:string|null }
export interface ProjectPackageConfiguration { state:"NOT_CONFIGURED"|"CONFIGURED"; project_id:number; organization_id:string; configuration_version:number; configuration_revision?:number; profile_id?:string; profile_digest?:string; registry_digest?:string; selections:PackageSelection[] }
export interface EffectiveDisciplinePackage { discipline_id:string; display_name:string; availability:"OPERATIONAL_AVAILABLE"|"FUTURE_UNAVAILABLE"|"HISTORICAL_ONLY"|"LEGACY_UNRESOLVED"; allowed_actions:string[]; binding_state:string; package_key:string|null; package_version:string|null; descriptor_digest:string|null; project_configuration_revision:number|null }
export interface EffectiveDisciplinePackages { project_id:number; items:EffectiveDisciplinePackage[] }
export interface WorkspacePackageApplicability { workspace_id:number; project_id:number; legacy_discipline:string; canonical_discipline_id:string|null; binding_state:string; package_key:string|null; package_version:string|null; descriptor_digest:string|null; project_configuration_revision:number|null; effective_standing:string|null; operational_state:"OPERATIONAL_AVAILABLE"|"HISTORICAL_READ_ONLY"|"UNAVAILABLE"; component_key:string|null; allowed_actions:string[] }
export interface EngineeringIdentifier { identifier_id:string; engineering_object_id:string; identifier_kind:string; display_value:string; normalized_value:string; lifecycle:string; authority_standing:string; primary_role:string; version:number; origin_package_key:string|null; origin_project_configuration_revision:number|null; origin_declaration_id:string|null }
export interface PackageEngineeringObject { id:string; project_id:number; workspace_id:number; object_type:string; lifecycle:string; authority_standing:string; version:number; origin_package_key:string|null; origin_project_configuration_revision:number|null; origin_declaration_id:string|null }
export interface PackageObjectCreateResult { object:PackageEngineeringObject; primary_identifier:EngineeringIdentifier }
export interface PackageRuleResult { status:"PASS"|"FINDINGS"|"INDETERMINATE"|"UNAVAILABLE"; finding_codes:string[]; limitations:string[]; result_digest:string }

export type ProjectContextSectionKind = "project_basis" | "execution" | "deliverables" | "project_controls" | "engineering_context" | "engineering_objects" | "evidence" | "supporting_files" | "technical_reports" | "organizational_memory";
export type ContextNodeKind = "project" | "workspace" | "execution_plan" | "activity" | "milestone" | "deliverable" | "deliverable_revision" | "risk" | "issue" | "human_decision" | "change" | "change_impact" | "engineering_object" | "engineering_context" | "evidence" | "supporting_file" | "technical_report" | "organizational_memory";
export type AuthorityClassification = "human_authoritative" | "external_tool_authored" | "canonical_evidence" | "derived" | "contextual_advisory";
export type TemporalClassification = "current" | "historical";
export interface ContextProvenance { owner_kind:string; selector:string; version:number|null; standing:string|null; source_observed_at:string|null; observed_at:string; authority_class:AuthorityClassification; temporal_class:TemporalClassification }
export interface ContextTruncation { truncated:boolean; continuation:{continuation:string;last_evaluated_key:string}|null }
export interface ProjectContextItem {
  item_kind:string; selector:string; version:number|null; standing:string|null; provenance:ContextProvenance;
  project_id?:number; workspace_id?:number|null; title?:string; project_name?:string|null; project_code?:string|null;
  code?:string; filename?:string; object_type?:string; evidence_kind?:string; report_type?:string;
  title_or_purpose?:string|null; purpose?:string|null; memory_id?:string; report_id?:string; object_id?:string;
  evidence_id?:string; asset_id?:string; deliverable_id?:string; control_id?:string; plan_id?:string; context_id?:number;
}
export type ProjectContextSectionState =
  | {state:"available";visible_count:number;truncated:ContextTruncation;observed_at:string}
  | {state:"empty"}
  | {state:"not_established"}
  | {state:"not_disclosed"}
  | {state:"unavailable"};
export interface ProjectContextSection { kind:ProjectContextSectionKind; state:ProjectContextSectionState; items:ProjectContextItem[] }
export interface ProjectContextSuccess { status:"success";observation_started_at:string;observation_completed_at:string;observation_status:"complete_within_bounds"|"partial";sections:ProjectContextSection[] }
export type CompletenessClassification="present"|"missing"|"indeterminate"|"not_disclosed"|"not_applicable";
export interface CompletenessFinding {rule_id:string;title:string;description:string;classification:CompletenessClassification;evidence:{display_label?:string|null;section_kind?:string;item_kind?:string}[];question:{text:string}|null;checklist_item:{text:string}|null;limitation_codes:string[];source_truncated:boolean}
export interface CompletenessObservation {assessment_status:"complete_within_bounds"|"partial";authority_class:"derived";advisory:true;authoritative:false;limitation_codes:string[];findings:CompletenessFinding[]}
export type ProjectCompletenessResult={status:"success"|"partial_success";observation:CompletenessObservation}|{status:"protected_not_found"|"invalid_request"|"unavailable"};
export interface ContextNodeSelector {kind:ContextNodeKind;value:string|number}
export interface ContextNode {node_kind:ContextNodeKind;selector:string|number;navigation:{project_id:number;workspace_id:number|null};provenance:ContextProvenance;authority_class:AuthorityClassification;temporal_class:TemporalClassification;[key:string]:unknown}
export interface ContextEdge {relationship_selector:string;relationship_kind:string|{family:string;relationship_type:string};source:ContextNodeSelector;target:ContextNodeSelector;provenance:ContextProvenance}
export interface OneHopSuccess {status:"success";start:ContextNode;edges:ContextEdge[];nodes:ContextNode[];truncated:ContextTruncation}
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
export type ExecutionActivityStanding = "planned"|"ready"|"in_progress"|"blocked"|"completed"|"cancelled";
export type ExecutionMilestoneStanding = "not_ready"|"blocked"|"achieved";
export interface ExecutionActivity { id:string; title:string; description:string|null; ordinal:number; workspace_id:number|null; responsible_user_id:number|null; target_date:string|null; completion_basis:string; standing:ExecutionActivityStanding; version:number; blocker_rationale:string|null; updated_at:string }
export interface ExecutionMilestone { id:string; title:string; completion_basis:string; target_date:string|null; ordinal:number; activity_ids:string[]; standing:ExecutionMilestoneStanding }
export interface ExecutionDependency { predecessor_activity_id:string; dependent_activity_id:string }
export interface ExecutionPlanEstablished { outcome:"success"; availability:"established"; project_id:number; plan_id:string; version:number; activities:ExecutionActivity[]; milestones:ExecutionMilestone[]; dependencies:ExecutionDependency[]; progress:{completed_count:number;eligible_count:number;percent:number} }
export interface ExecutionPlanNotEstablished { outcome:"success"; availability:"plan_not_established"; project_id:number; allowed_actions:string[] }
export type ExecutionPlan = ExecutionPlanEstablished | ExecutionPlanNotEstablished;
export type DeliverableStanding = "planned"|"in_preparation"|"ready_for_review"|"reviewed"|"issued"|"withdrawn"|"cancelled";
export type DeliverableRevisionStanding = "draft"|"ready_for_review"|"reviewed"|"issued"|"superseded"|"withdrawn";
export interface DeliverableRevision { id:string;sequence:number;external_label:string;source_reference:string|null;representation_available:boolean;standing:DeliverableRevisionStanding;version:number;created_at:string;transitioned_at:string }
export interface Deliverable { id:string;project_id:number;workspace_id:number|null;code:string;title:string;discipline:string;deliverable_type:string;purpose:string|null;external_authority:"cad"|"eplan"|"etap"|"spreadsheet"|"document"|"vendor_tool"|"other";responsible_user_id:number|null;target_date:string|null;standing:DeliverableStanding;version:number;activity_id:string|null;milestone_id:string|null;current_revision:DeliverableRevision }
export interface DeliverableRegister { outcome:"success";items:Deliverable[];visible_count:number;continuation:string|null }
export interface DeliverableMutation { outcome:"success";deliverable_id:string;deliverable_version:number;revision_id:string|null;revision_version:number|null;standing:DeliverableStanding|null;revision_standing:DeliverableRevisionStanding|null }
export interface ExecutionMutation { outcome:"success"; project_id:number; plan_id:string; plan_version:number; activity_id:string|null; milestone_id:string|null; activity_version:number|null; standing:ExecutionActivityStanding|null }
export interface IssuedCredential { outcome: string; organization?: OrganizationProfile & { is_active: boolean }; member?: OrganizationMember; one_time_token?: string; replayed?: boolean }
export interface MemberList { outcome: string; items: OrganizationMember[] }
export type ProjectControlKind = "risk" | "issue" | "decision" | "change";
export type ChangeImpactTargetKind = "activity" | "milestone" | "deliverable" | "deliverable_revision" | "evidence" | "supporting_file";
export interface ChangeImpact { id:string; change_id:string; target_kind:ChangeImpactTargetKind; target_id:string; statement:string; standing:"potential"|"confirmed"; confirmed_by_id:number|null; confirmed_at:string|null }
export interface ProjectControl { outcome:"success"; id:string; version:number; organization_id:string; project_id:number; workspace_id:number|null; standing:string; statement:string; rationale:string|null; predecessor_id:string|null; owner_id:number|null; disposition:string|null; observed_context:string|null; alternatives:string[]; accepted_by_id:number|null; accepted_at:string|null; confirmed_by_id:number|null; confirmed_at:string|null; impacts:ChangeImpact[] }
export interface ProjectControlList { outcome:"success"; kind:ProjectControlKind; items:ProjectControl[]; visible_count:number }
export interface ProjectControlHistoryEntry { id:string; aggregate_version:number; event_type:string; actor_id:number; occurred_at:string }
export interface ProjectControlHistory { outcome:"success"; kind:ProjectControlKind; control_id:string; items:ProjectControlHistoryEntry[]; visible_count:number }
export interface ProjectControlMutation { outcome:"success"; id:string; version:number }
export interface ChangeImpactMutation { outcome:"success"; id:string; change_id:string; standing:"potential"|"confirmed" }

export type GuidanceType = "engineering_observation" | "missing_engineering_consideration" | "potential_risk_consideration" | "explicit_conflict_to_verify" | "verification_point" | "clarification_requirement" | "suggested_next_check" | "alternative_consideration";
export type GuidanceEvidenceSufficiency = "sufficient" | "partial" | "insufficient" | "indeterminate";
export type GuidanceMaterialCategory = "instrumentation_measurement" | "electrical_power_or_interconnection" | "automation_and_control";
export type GuidanceAiState = "not_requested" | "available" | "disabled" | "unavailable" | "timed_out" | "rejected";
export interface GuidanceSafeEvidence { reference_kind:"visible_fact"|"visible_section_state"|"completeness_finding"; safe_key:string; predicate_code:string; observed_at:string; visible_label:string|null }
export type GuidanceAiEnhancement = { state:"available"; enhanced_explanation:string; enhanced_clarification:string|null } | { state:"available"; enhanced_explanation:null; enhanced_clarification:string } | { state:Exclude<GuidanceAiState,"available">; enhanced_explanation:null; enhanced_clarification:null };
export interface GuidanceItem { guidance_item_id:string; catalog_id:"engineering_guidance.v1"; catalog_version:1; catalog_digest:string; rule_id:string; rule_version:1; ordinal:number; guidance_type:GuidanceType; title:string; summary:string; explanation:string; engineering_rationale:string; evidence_sufficiency:GuidanceEvidenceSufficiency; evidence:GuidanceSafeEvidence[]; assumptions:string[]; limitations:string[]; verification_requirements:string[]; source_observation_started_at:string; source_observation_completed_at:string; generated_at:string; authority_class:"derived"; advisory:true; authoritative:false; ai_enhancement:GuidanceAiEnhancement }
export interface GuidanceMaterialAttribute { key:string; label:string; status:"requires_engineering_determination" }
export interface CandidateMaterialRequirement { candidate_id:string; category:GuidanceMaterialCategory; triggering_guidance_item_id:string; triggering_rule_id:string; engineering_rationale:string; evidence:GuidanceSafeEvidence[]; attributes_to_determine:GuidanceMaterialAttribute[]; assumptions:string[]; limitations:string[]; verification_requirements:string[]; evidence_sufficiency:GuidanceEvidenceSufficiency; quantity_status:"not_estimated"; generated_at:string; authority_class:"derived"; advisory:true; authoritative:false }
export interface GuidanceObservation { catalog:{catalog_id:"engineering_guidance.v1";catalog_version:1;catalog_digest:string;rules:unknown[]}; context_observation_digest:string; status:"complete_within_bounds"|"partial"; source_observation_started_at:string; source_observation_completed_at:string; generated_at:string; items:GuidanceItem[]; no_guidance_warranted:boolean; candidate_material_requirements:CandidateMaterialRequirement[]; limitations:string[]; authority_class:"derived"; advisory:true; authoritative:false }
export type EngineeringGuidanceResult = { kind:"success"; observation:GuidanceObservation } | { kind:"partial_success"; observation:GuidanceObservation } | { kind:"insufficient_context"|"protected_not_found"|"invalid_request"|"unavailable" };
export type EngineeringGuidanceRequest = { workspace_id?:number|null; ai_enhancement:"not_requested"|"requested" };

export type XDIState = "loading"|"ready"|"empty"|"indeterminate"|"unavailable"|"protected_not_found"|"conflict";
export interface XDIReadiness { state:"ready"|"not_ready"|"unavailable"|"protected_not_found";reason_codes:string[];definition_digest?:string }
export interface XDIScope { workspace_ids:number[];combination_id:string;interface_definition_ids:string[];endpoint_selectors:string[];purpose:"interface_assessment"|"current_handoff_gate"|"explicit_change_impact";project_change_id?:number;project_change_version?:number }
export interface XDIEligibility { state:"eligible"|"ineligible"|"indeterminate"|"unavailable"|"protected_not_found";reason_codes:string[];definition_digest?:string }
export interface XDIAssessment { assessment_id:string;aggregate_version:number;status:"completed_no_findings"|"completed_with_findings"|"indeterminate"|"unavailable";reason_code:string|null;result_digest:string;completed_at:string }
export interface XDIFinding { finding_id:string;assessment_id:string;ordinal:number;category:string;subcode:string;severity:string;fingerprint:string;recurrence_key:string;current_state:string;allowed_actions:string[];provenance:Record<string,unknown>;advisory:true }
export interface XDIICComparisonPresentation { rule_id:"xdi.ic.signal_type.v1"|"xdi.ic.signal_range.v1"; advisory:true; protected_operands:true }
export interface XDIICDependencyPresentation { rule_id:"xdi.ic.valve_command_feedback.v1"; advisory:true; persisted_path_only:true }
export interface XDIICCommitmentPresentation { rule_id:"xdi.ic.commitment_fulfilment.v1"; advisory:true; retained_provenance_only:true }
export interface XDIPage<T> { items:T[];next_cursor:string|null }
export interface XDIDisposition { disposition_id:string;sequence:number;action:string;resulting_view_state:string;actor_id:number;rationale:string;occurred_at:string;view_version:number }
export interface XDILineage { lineage_id:string;kind:"reassessment_of"|"supersedes";predecessor_id:string;successor_id:string;occurred_at:string }
export type XDIClosedResult = {outcome:"success"|"protected_not_found"|"invalid_request"|"version_conflict"|"idempotency_conflict"|"indeterminate"|"unavailable";reason_code?:string};
export interface XDIPotentialImpact { outcome:string; state:"pending"|"reconciled"|"handoff_link_pending"|null; impact_id?:string|null; handoff_key?:string|null; advisory:true }
export interface XDIReportProjection { assessment_id:string;snapshot_digest:string;advisory:true }
export interface XDIAIExplanation { outcome:string;summary?:string|null;draft_next_actions?:string[];advisory:true }
