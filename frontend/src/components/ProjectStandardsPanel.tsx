import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, StandardApplicability, StandardAssertion, StandardCandidate, StandardSourceSnapshot } from "../api/types";
import { StandardsStatePresentation } from "./StandardsStatePresentation";

type ApplicabilityPage = { items: StandardApplicability[]; next_cursor: string | null };

export function ProjectStandardsPanel({ projectId }: { projectId: number }) {
  const [result, setResult] = useState<ApiResult<ApplicabilityPage> | null>(null);
  const [candidates, setCandidates] = useState<ApiResult<{ items: StandardCandidate[] }> | null>(null);
  const [message, setMessage] = useState("");
  const [editionId, setEditionId] = useState("");
  const [status, setStatus] = useState("declared_applicable");
  const [role, setRole] = useState("design_basis");
  const [rationale, setRationale] = useState("");
  const [mandatoryKind, setMandatoryKind] = useState("contract");
  const [mandatoryReference, setMandatoryReference] = useState("");
  const [mandatoryDigest, setMandatoryDigest] = useState("");
  const [expectedRevision, setExpectedRevision] = useState(0);
  const [providerId, setProviderId] = useState("registry_metadata");
  const [sourcePurpose, setSourcePurpose] = useState("reference_only");
  const [locations, setLocations] = useState("");
  const [snapshots, setSnapshots] = useState<StandardSourceSnapshot[]>([]);
  const [display, setDisplay] = useState<ApiResult<Record<string, unknown>> | null>(null);
  const [assertion, setAssertion] = useState<StandardAssertion | null>(null);
  const [assertionStatement, setAssertionStatement] = useState("");
  const [decisionReason, setDecisionReason] = useState("");
  const messageRef = useRef<HTMLParagraphElement>(null);

  async function load() {
    const [applicability, advisory] = await Promise.all([api.projectStandards(projectId), api.projectStandardCandidates(projectId)]);
    setResult(applicability); setCandidates(advisory);
  }
  useEffect(() => {
    setResult(null); setCandidates(null); setSnapshots([]); setDisplay(null); setAssertion(null); setMessage("");
    if (projectId > 0) void load();
  }, [projectId]);
  useEffect(() => {
    if (message || (result && result.state !== "success")) messageRef.current?.focus();
  }, [message, result]);

  async function declare(event: FormEvent) {
    event.preventDefault();
    const response = await api.declareProjectStandard(projectId, {
      edition_id: editionId, status, applicability_role: role,
      rationale_code: "human_review", rationale, expected_revision: expectedRevision,
      ...(role === "mandatory" ? {
        mandatory_source_kind: mandatoryKind,
        mandatory_source_reference: mandatoryReference,
        mandatory_source_digest: mandatoryDigest,
      } : {}),
    });
    if (response.state === "success") { setMessage("Human applicability declaration recorded."); setRationale(""); setExpectedRevision(response.data.revision); await load(); }
    else setMessage(response.state === "conflict" ? "Applicability changed; reload the current revision." : "Applicability declaration was not accepted.");
  }

  async function retire(item: StandardApplicability) {
    const reason = window.prompt("Human rationale for retiring this applicability head:");
    if (!reason?.trim() || !window.confirm("Retire this exact current applicability revision?")) return;
    const response = await api.retireProjectStandard(projectId, item.applicability_id, { expected_revision: item.revision, reason: reason.trim() });
    setMessage(response.state === "success" ? "Applicability retired; historical provenance remains." : response.state === "conflict" ? "Applicability changed; reload before retiring." : "Applicability retirement was not accepted.");
    if (response.state === "success") await load();
  }

  async function retrieve(event: FormEvent) {
    event.preventDefault(); setDisplay(null); setAssertion(null);
    const fragments = locations.split("\n").map((location) => location.trim()).filter(Boolean).map((location) => ({ location }));
    const response = await api.retrieveStandardSources(projectId, { edition_id: editionId, provider_id: providerId, purpose: sourcePurpose, fragments });
    if (response.state === "success") { setSnapshots(response.data.items); setMessage(`${response.data.items.length} governed source snapshot record(s) created.`); }
    else { setSnapshots([]); setMessage(response.state === "protected" ? "Source context is not available." : "Source retrieval was not accepted."); }
  }

  async function displaySnapshot(snapshot: StandardSourceSnapshot) {
    if (!snapshot.authorized_handle) return;
    const response = await api.displayStandardSource(projectId, snapshot.snapshot_id, snapshot.authorized_handle);
    setDisplay(response);
    setMessage(response.state === "protected" ? "The protected source is no longer available." : response.state === "success" ? "Source display was freshly authorized." : "Source display could not be authorized.");
  }

  async function createAssertion(event: FormEvent) {
    event.preventDefault();
    const snapshot = snapshots.find((item) => item.availability_status === "available" && item.integrity_verified);
    if (!snapshot) return;
    const response = await api.createStandardAssertion(projectId, {
      snapshot_id: snapshot.snapshot_id, source_location: snapshot.source_location,
      assertion_kind: "requirement_statement", canonical_representation: { statement: assertionStatement }, origin: "human",
    });
    if (response.state === "success") { setAssertion(response.data); setMessage("Unverified Human assertion recorded; it has no authority until a separate decision."); }
    else setMessage("Assertion creation was not accepted.");
  }

  async function decide(approved: boolean) {
    if (!assertion || !decisionReason.trim() || !window.confirm(`${approved ? "Verify" : "Reject"} this exact assertion version?`)) return;
    const response = await api.decideStandardAssertion(projectId, assertion.assertion_id, approved, { expected_version: assertion.version, reason: decisionReason.trim() }, approved ? assertion.verification_handle : assertion.rejection_handle);
    if (response.state === "success") { setAssertion(response.data); setDecisionReason(""); setMessage(approved ? "Assertion Human-verified." : "Assertion rejected."); }
    else setMessage(response.state === "conflict" ? "Assertion changed; this decision lost the version race." : "Assertion decision was not accepted.");
  }

  return <section className="standards-panel" aria-labelledby="project-standards-title">
    <h2 id="project-standards-title">Project standards</h2>
    <p>Package candidates are advisory. Applicability, source use, and assertion verification are separate Human-governed actions.</p>
    <p ref={messageRef} role="status" tabIndex={-1}>{message || (result?.state === "protected" ? "Project standards are not available." : result?.state !== "success" && result ? "Standards context is unavailable." : "")}</p>

    {candidates?.state === "success" && candidates.data.items.length ? <div><h3>Package advisory candidates</h3><ul className="standards-list">{candidates.data.items.map((item) => <li key={item.candidate_id}><bdi dir="ltr">{item.designation_key}</bdi> · suggested {item.suggested_role}<small>{item.package_key}@{item.package_version} · advisory only; resolve to registry metadata before Human declaration.</small></li>)}</ul></div> : null}
    {result?.state === "success" ? <div><h3>Current Human declarations</h3><div className="standards-list">{result.data.items.map((item) => <article key={item.applicability_id}>
      <div className="standards-row-heading"><strong><code dir="ltr">{item.edition_id ?? item.candidate_designation_key ?? "candidate"}</code></strong><StandardsStatePresentation state={item.status} /></div>
      <span>{item.applicability_role.replaceAll("_", " ")} · {item.rationale_code.replaceAll("_", " ")}</span><small>{item.rationale}</small>
      {item.status !== "retired" && item.status !== "candidate_advisory" ? <button type="button" className="button ghost compact" onClick={() => void retire(item)}>Retire declaration</button> : null}
    </article>)}</div></div> : null}

    <form className="standards-governed-form" onSubmit={declare} aria-labelledby="declare-standard-title"><h3 id="declare-standard-title">Human applicability declaration</h3>
      <label>Registry edition ID<input required dir="ltr" value={editionId} onChange={(event) => setEditionId(event.target.value)} /></label>
      <div className="form-row"><label>Declaration<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="declared_applicable">Applicable</option><option value="declared_not_applicable">Not applicable</option></select></label><label>Role<select value={role} onChange={(event) => setRole(event.target.value)}><option value="informative">Informative</option><option value="design_basis">Design basis</option><option value="mandatory">Mandatory (Human-attributed)</option></select></label></div>
      {role === "mandatory" ? <fieldset><legend>Attributable mandatory basis</legend><label>Authority kind<select value={mandatoryKind} onChange={(event) => setMandatoryKind(event.target.value)}><option value="contract">Contract</option><option value="regulation">Regulation</option><option value="customer_requirement">Customer requirement</option><option value="company_policy">Company policy</option></select></label><label>Authority reference<input required maxLength={500} value={mandatoryReference} onChange={(event) => setMandatoryReference(event.target.value)} /></label><label>Authority SHA-256 digest<input required dir="ltr" pattern="[0-9a-f]{64}" value={mandatoryDigest} onChange={(event) => setMandatoryDigest(event.target.value)} /></label></fieldset> : null}
      <label>Human rationale<textarea required maxLength={1000} value={rationale} onChange={(event) => setRationale(event.target.value)} /></label>
      <label>Expected current revision<input required min={0} type="number" value={expectedRevision} onChange={(event) => setExpectedRevision(Number(event.target.value))} /></label>
      <button className="button secondary">Record declaration</button>
    </form>

    <form className="standards-governed-form" onSubmit={retrieve} aria-labelledby="retrieve-source-title"><h3 id="retrieve-source-title">Create governed source snapshots</h3>
      <p>Locations are registered provider-local identifiers, never arbitrary URLs. Material support requires current retrieval rights.</p>
      <div className="form-row"><label>Provider ID<input required pattern="[a-z][a-z0-9_]*" value={providerId} onChange={(event) => setProviderId(event.target.value)} /></label><label>Purpose<select value={sourcePurpose} onChange={(event) => setSourcePurpose(event.target.value)}><option value="reference_only">Reference only</option><option value="material_support">Material support</option></select></label></div>
      <label>Provider-local locations <span>(one per line, maximum 8)</span><textarea required value={locations} onChange={(event) => setLocations(event.target.value)} /></label>
      <button className="button secondary">Create bounded snapshots</button>
    </form>
    {snapshots.length ? <div className="standards-list" aria-label="Created source snapshots">{snapshots.map((snapshot) => <article key={snapshot.snapshot_id}><div className="standards-row-heading"><code dir="ltr">{snapshot.snapshot_id}</code><StandardsStatePresentation state={snapshot.availability_status} /></div><span>{snapshot.source_location} · integrity {snapshot.integrity_verified ? "verified" : "not verified"}</span>{snapshot.authorized_handle ? <button type="button" className="button ghost compact" onClick={() => void displaySnapshot(snapshot)}>Freshly authorize display</button> : null}</article>)}</div> : null}
    {display?.state === "success" ? <div className="standards-protected-display" role="region" aria-label="Authorized standards excerpt"><pre>{JSON.stringify(display.data, null, 2)}</pre><small>Protected display is not cached and grants no applicability or acceptance authority.</small></div> : null}

    {snapshots.some((item) => item.availability_status === "available" && item.integrity_verified) ? <form className="standards-governed-form" onSubmit={createAssertion} aria-labelledby="assertion-title"><h3 id="assertion-title">Human assertion from current material support</h3><label>Requirement statement<textarea required maxLength={4000} value={assertionStatement} onChange={(event) => setAssertionStatement(event.target.value)} /></label><button className="button secondary">Record unverified assertion</button></form> : null}
    {assertion ? <article className="standards-decision"><div className="standards-row-heading"><strong>Assertion decision</strong><StandardsStatePresentation state={assertion.verification_status} /></div><code dir="ltr">{assertion.assertion_id}</code>{assertion.verification_status === "unverified" ? <><label>Human decision rationale<textarea required value={decisionReason} onChange={(event) => setDecisionReason(event.target.value)} /></label><div className="standards-actions"><button type="button" className="button primary" onClick={() => void decide(true)}>Verify assertion</button><button type="button" className="button ghost" onClick={() => void decide(false)}>Reject assertion</button></div></> : null}</article> : null}
  </section>;
}
