import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, ReportProvenance, TechnicalReportDetail, TechnicalReportStandardCandidate } from "../api/types";
import { StandardsStatePresentation } from "./StandardsStatePresentation";

export function TechnicalReportStandardsBasisPanel({ provenance, report, onUpdated }: { provenance: ReportProvenance[]; report?: TechnicalReportDetail; onUpdated?: () => void }) {
  const standards = provenance.filter((item) => item.source_type === "standard");
  const draft = report?.lifecycle === "draft" ? report : null;
  const [candidates, setCandidates] = useState<ApiResult<{ items: TechnicalReportStandardCandidate[] }> | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [selectionRationale, setSelectionRationale] = useState("");
  const [acknowledgement, setAcknowledgement] = useState("");
  const [revisionRationale, setRevisionRationale] = useState("");
  const [message, setMessage] = useState("");
  const messageRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    setCandidates(null); setSelected([]); setMessage("");
    if (draft) void api.reportStandardCandidates(draft.id).then(setCandidates);
  }, [draft?.id, draft?.version]);
  useEffect(() => {
    if (message || (candidates && candidates.state !== "success")) messageRef.current?.focus();
  }, [message, candidates]);

  async function attach(event: FormEvent) {
    event.preventDefault();
    if (!draft || candidates?.state !== "success" || !window.confirm("Attach these exact server-authorized standards bases to a new Report revision?")) return;
    const chosen = candidates.data.items.filter((item) => selected.includes(item.authorized_handle));
    const response = await api.reviseReportStandardsBasis(draft.id, {
      expected_version: draft.version,
      expected_draft_revision_id: draft.draft_revision_id,
      selections: chosen.map((item) => ({
        authorized_handle: item.authorized_handle,
        materiality: item.materiality,
        selection_rationale: selectionRationale,
        standing_acknowledgement: item.eligibility === "standing_acknowledgement_required" ? acknowledgement : null,
        assertion_id: null,
      })),
      rationale: revisionRationale,
    });
    if (response.state === "success") { setMessage("Standards basis attached to a new exact Report revision."); setSelected([]); onUpdated?.(); }
    else setMessage(response.state === "conflict" ? "The Report or standards state changed; reload before attaching." : response.state === "protected" ? "The selected standards basis is no longer available." : "Standards basis attachment was not accepted.");
  }

  return <section className="standards-panel" aria-labelledby="report-standards-basis-title">
    <h2 id="report-standards-basis-title">Standards basis and provenance</h2>
    <p>Basis selection is a Human action. Material support and reference-only use are explicit; accepted historical basis is never rewritten.</p>
    {standards.length ? <div className="standards-list" aria-label="Report standards basis history">{standards.map((item) => <article key={item.entry_id}>
      <div className="standards-row-heading"><strong>{item.availability_status === "available" ? item.origin_attribution : "Protected historical standards basis"}</strong><StandardsStatePresentation state={item.availability_status} /></div>
      <span>{item.is_material ? "Material support" : "Reference only"} · {item.verification_status.replaceAll("_", " ")}</span>
      <small>{item.availability_status === "available" ? "Canonical historical basis is attached to this Report revision." : "Historical identity and integrity are retained, but current source content and counts are masked."}</small>
    </article>)}</div> : <p>No standards basis is attached to this Report revision.</p>}
    <p ref={messageRef} role="status" tabIndex={-1}>{message || (candidates?.state === "protected" ? "Standards candidates are not available for this Report." : candidates && candidates.state !== "success" ? "Standards candidates could not be loaded." : "")}</p>
    {draft && candidates?.state === "success" ? <form className="standards-governed-form" onSubmit={attach} aria-labelledby="basis-selector-title">
      <h3 id="basis-selector-title">Select current authorized standards basis</h3>
      {!candidates.data.items.length ? <p>No currently eligible standards basis candidates.</p> : <fieldset><legend>Authorized candidates</legend>{candidates.data.items.map((item) => <label className="standards-candidate" key={item.authorized_handle}><input type="checkbox" checked={selected.includes(item.authorized_handle)} disabled={item.eligibility === "rights_restricted"} onChange={(event) => setSelected(event.target.checked ? [...selected, item.authorized_handle] : selected.filter((value) => value !== item.authorized_handle))} /><span><strong><bdi dir="ltr">{item.issuer} · {item.designation} · {item.edition_designation}</bdi></strong><small>{item.materiality === "material_support" ? "Material support" : "Reference only"} · {item.standing.replaceAll("_", " ")} · {item.eligibility.replaceAll("_", " ")}</small>{item.warnings.map((warning) => <small className="standards-warning" key={warning}>{warning.replaceAll("_", " ")}</small>)}</span></label>)}</fieldset>}
      <small>{selected.length} of 16 standards bases selected. The complete Report provenance limit is 32; the server rejects overflow without truncation.</small>
      <label>Human selection rationale<textarea required maxLength={2000} value={selectionRationale} onChange={(event) => setSelectionRationale(event.target.value)} /></label>
      {candidates.data.items.some((item) => selected.includes(item.authorized_handle) && item.eligibility === "standing_acknowledgement_required") ? <label>Standing acknowledgement<textarea required maxLength={2000} value={acknowledgement} onChange={(event) => setAcknowledgement(event.target.value)} /></label> : null}
      <label>Report revision rationale<textarea required maxLength={2000} value={revisionRationale} onChange={(event) => setRevisionRationale(event.target.value)} /></label>
      <button className="button primary" disabled={!selected.length || !selectionRationale.trim() || !revisionRationale.trim()}>Attach to new exact revision</button>
    </form> : null}
  </section>;
}
