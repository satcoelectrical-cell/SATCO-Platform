import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ApiResult, CandidateMaterialRequirement, EngineeringGuidanceResult, GuidanceItem, GuidanceSafeEvidence } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";
import { Surface } from "./Page";

const label = (value: string) => value.replaceAll("_", " ");

function TextList({ title, values }: { title: string; values: string[] }) {
  return values.length ? <section className="guidance-text-list"><h4>{title}</h4><ul>{values.map((value) => <li key={value}>{value}</li>)}</ul></section> : null;
}

function safeEvidenceOwner(safeKey: string) {
  if (safeKey === "project_control:risk") return "Project Control — Risk";
  if (safeKey === "project_control:issue") return "Project Control — Issue";
  if (safeKey === "project_control:change") return "Project Control — Change";
  if (safeKey.startsWith("execution:")) return "Execution";
  if (safeKey.startsWith("deliverable:")) return "Deliverable";
  if (safeKey.startsWith("engineering_object:")) return "Engineering Object";
  return "Authorized supporting evidence";
}

function safeEvidenceLabel(evidence: GuidanceSafeEvidence) {
  const owner = safeEvidenceOwner(evidence.safe_key);
  return evidence.visible_label?.trim() ? `${owner} — ${evidence.visible_label}` : owner;
}

function SafeEvidenceList({ evidence }: { evidence: GuidanceSafeEvidence[] }) {
  return <section className="guidance-text-list"><h4>Safe evidence</h4>{evidence.length ? <ul>{evidence.map((reference, index) => <li key={index}>{safeEvidenceLabel(reference)}</li>)}</ul> : <p>No safe evidence reference supplied.</p>}</section>;
}

function GuidanceItemCard({ item }: { item: GuidanceItem }) {
  const ai = item.ai_enhancement;
  return <article className="guidance-item"><header><StatusBadge value={item.guidance_type} /><StatusBadge value={item.evidence_sufficiency} /></header><h3>{item.guidance_type === "potential_risk_consideration" ? "Potential consideration to verify" : item.title}</h3><p>{item.summary}</p><p>{item.explanation}</p><p className="guidance-rationale">{item.engineering_rationale}</p><SafeEvidenceList evidence={item.evidence} /><TextList title="Assumptions" values={item.assumptions} /><TextList title="Limitations" values={item.limitations} /><TextList title="Human verification required" values={item.verification_requirements} /><section className="guidance-ai" aria-label="Model-assisted explanation"><StatusBadge value={ai.state} />{ai.state === "available" ? <><strong>Model-assisted explanation</strong>{ai.enhanced_explanation ? <p>{ai.enhanced_explanation}</p> : null}{ai.enhanced_clarification ? <p>{ai.enhanced_clarification}</p> : null}</> : <p>Optional AI enhancement: {label(ai.state)}. Deterministic guidance remains available for this view.</p>}</section></article>;
}

function CandidateCard({ candidate }: { candidate: CandidateMaterialRequirement }) {
  return <article className="guidance-candidate"><header><StatusBadge value={candidate.category} /><StatusBadge value={candidate.evidence_sufficiency} /></header><h3>{label(candidate.category)}</h3><p>{candidate.engineering_rationale}</p><p><strong>Quantity: NOT ESTIMATED</strong></p><SafeEvidenceList evidence={candidate.evidence} /><TextList title="Attributes requiring engineering determination" values={candidate.attributes_to_determine.map((attribute) => attribute.label)} /><TextList title="Assumptions" values={candidate.assumptions} /><TextList title="Limitations" values={candidate.limitations} /><TextList title="Human verification required" values={candidate.verification_requirements} /></article>;
}

export function EngineeringGuidancePanel({ projectId, workspaceId }: { projectId: number; workspaceId?: number | null }) {
  const [result, setResult] = useState<ApiResult<EngineeringGuidanceResult> | null>(null);
  const load = (ai_enhancement: "not_requested" | "requested" = "not_requested") => { setResult(null); void api.engineeringGuidance(projectId, { workspace_id: workspaceId ?? null, ai_enhancement }).then(setResult); };
  useEffect(() => { load("not_requested"); }, [projectId, workspaceId]);
  if (!result) return <section className="engineering-guidance" aria-live="polite"><LoadingState label="Loading deterministic Engineering Guidance…" /></section>;
  if (result.state !== "success") return <section className="engineering-guidance"><ProtectedState /></section>;
  const data = result.data;
  if (data.kind === "protected_not_found" || data.kind === "invalid_request") return <section className="engineering-guidance"><ProtectedState /></section>;
  if (data.kind === "unavailable") return <section className="engineering-guidance"><ErrorState unavailable retry={() => load("not_requested")} /></section>;
  if (data.kind === "insufficient_context") return <section className="engineering-guidance"><Surface title="Engineering Guidance" subtitle="Derived, advisory and non-authoritative"><EmptyState title="More authorized context is needed" detail="The authorized context is categorically insufficient for this bounded assessment." /></Surface></section>;
  if (data.kind === "success" || data.kind === "partial_success") {
    const observation = data.observation;
    return <section className="engineering-guidance" aria-labelledby="engineering-guidance-title"><Surface title="Derived, advisory and non-authoritative" subtitle="Human engineer verification remains required."><header className="guidance-heading"><div><h2 id="engineering-guidance-title">Engineering Guidance</h2><p role="status">{data.kind === "partial_success" ? "Partial bounded observation" : "Bounded observation"}</p></div><div className="guidance-actions"><button type="button" className="button secondary" onClick={() => load("not_requested")}>Refresh guidance</button>{!observation.no_guidance_warranted ? <button type="button" className="button ghost" onClick={() => load("requested")}>Request optional AI enhancement</button> : null}</div></header>{observation.limitations.length ? <TextList title="Assessment limitations" values={observation.limitations} /> : null}<section aria-labelledby="consider-next-title"><h3 id="consider-next-title">Consider Next</h3>{observation.no_guidance_warranted ? <EmptyState title="No guidance warranted" detail="No applicable guidance is visible in this bounded observation." /> : <div className="guidance-list">{observation.items.map((item) => <GuidanceItemCard item={item} key={item.guidance_item_id} />)}</div>}</section><section aria-labelledby="candidate-material-title"><h3 id="candidate-material-title">Candidate Material Requirements</h3><p className="guidance-supporting">Advisory only — not a BOM, MTO, BOQ, requisition, selection, or purchase item.</p>{observation.candidate_material_requirements.length ? <div className="guidance-list">{observation.candidate_material_requirements.map((candidate) => <CandidateCard candidate={candidate} key={candidate.candidate_id} />)}</div> : <EmptyState title="No candidate material requirements" detail="No advisory material requirement is visible in this bounded observation." />}</section></Surface></section>;
  }
  return <section className="engineering-guidance"><ProtectedState /></section>;
}
