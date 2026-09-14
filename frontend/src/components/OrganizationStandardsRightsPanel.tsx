import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, StandardRightsCapabilities, StandardRightsView, StandardsRightsPage } from "../api/types";
import { StandardsStatePresentation } from "./StandardsStatePresentation";

const capabilityLabels: Array<[keyof StandardRightsCapabilities, string]> = [
  ["metadata_visibility", "Metadata visibility"],
  ["content_storage", "Content storage"],
  ["indexing", "Indexing"],
  ["excerpt_display", "Excerpt display"],
  ["source_retrieval", "Source retrieval"],
  ["derived_retention", "Derived retention"],
  ["derived_current_use", "Derived current use"],
];

function localDateTime(value: string) {
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

export function OrganizationStandardsRightsPanel() {
  const [result, setResult] = useState<ApiResult<StandardsRightsPage> | null>(null);
  const [editing, setEditing] = useState<StandardRightsView | null>(null);
  const [message, setMessage] = useState("");
  const [basis, setBasis] = useState("organization_license");
  const [status, setStatus] = useState("active");
  const [permission, setPermission] = useState("prohibited");
  const [policies, setPolicies] = useState("");
  const [effectiveFrom, setEffectiveFrom] = useState("");
  const [effectiveUntil, setEffectiveUntil] = useState("");
  const [authorityReference, setAuthorityReference] = useState("");
  const [authorityDigest, setAuthorityDigest] = useState("");
  const [reason, setReason] = useState("");
  const [capabilities, setCapabilities] = useState<StandardRightsCapabilities | null>(null);
  const messageRef = useRef<HTMLParagraphElement>(null);

  async function load() { setResult(await api.standardRights()); }
  useEffect(() => { void load(); }, []);
  useEffect(() => {
    if (message || (result && result.state !== "success")) messageRef.current?.focus();
  }, [message, result]);

  function beginReplace(item: StandardRightsView) {
    setEditing(item); setBasis(item.rights_basis); setStatus(item.rights_status);
    setPermission(item.ai_processing_permission); setPolicies(item.approved_processor_policy_ids.join("\n"));
    setEffectiveFrom(localDateTime(item.effective_from)); setEffectiveUntil(item.effective_until ? localDateTime(item.effective_until) : "");
    setCapabilities({ ...item.capabilities }); setAuthorityReference(""); setAuthorityDigest(""); setReason(""); setMessage("");
  }

  async function replace(event: FormEvent) {
    event.preventDefault();
    if (!editing || !capabilities || !window.confirm("Replace this exact current rights version?")) return;
    const policyIds = policies.split(/\s+/).map((value) => value.trim()).filter(Boolean).sort();
    const response = await api.replaceStandardRights(editing.edition_id, editing.source_provider_id, {
      rights_basis: basis, rights_status: status,
      ...Object.fromEntries(capabilityLabels.map(([key]) => [`allow_${key}`, capabilities[key]])),
      ai_processing_permission: permission,
      approved_processor_policy_ids: permission === "approved_processor" ? [...new Set(policyIds)] : [],
      effective_from: new Date(effectiveFrom).toISOString(), effective_until: effectiveUntil ? new Date(effectiveUntil).toISOString() : null,
      rights_authority_reference: authorityReference, rights_authority_digest: authorityDigest,
      expected_version: editing.version, reason_code: "administrator_replacement", reason: reason || null,
    });
    if (response.state === "success") { setEditing(null); setMessage("Rights replacement recorded as a new governed version."); await load(); }
    else setMessage(response.state === "conflict" ? "Rights changed; reload and review the current version." : "Rights replacement was not accepted.");
  }

  async function revoke(item: StandardRightsView) {
    const explanation = window.prompt("Reason for revoking this exact rights version:");
    if (!explanation?.trim() || !window.confirm("Revoke this rights version and deny protected use?")) return;
    const response = await api.revokeStandardRights(item.rights_binding_id, { expected_version: item.version, reason: explanation.trim() });
    setMessage(response.state === "success" ? "Rights revoked. Current protected capabilities are denied." : response.state === "conflict" ? "Rights changed; reload before revoking." : "Rights revocation was not accepted.");
    if (response.state === "success") await load();
  }

  return <section className="standards-panel" aria-labelledby="standards-rights-title">
    <h2 id="standards-rights-title">Standards rights administration</h2>
    <p>Only Organization administrators can replace or revoke rights. Every action uses the exact current version and fresh server authorization.</p>
    <p ref={messageRef} role="status" tabIndex={-1}>{message || (result?.state === "protected" ? "Rights are not available." : result?.state !== "success" && result ? "Rights could not be loaded." : "")}</p>
    {result?.state === "success" ? <div className="standards-list">{result.data.items.map((item) => <article key={item.rights_binding_id}>
      <div className="standards-row-heading"><strong><code dir="ltr">{item.edition_id}</code></strong><StandardsStatePresentation state={item.rights_status} /></div>
      <span>Provider: <bdi>{item.source_provider_id}</bdi> · AI: {item.ai_processing_permission}</span>
      {item.rights_status !== "active" || (item.effective_until && new Date(item.effective_until) <= new Date()) ? <strong className="standards-warning">Protected use is denied because these rights are expired, revoked, or otherwise inactive.</strong> : null}
      <dl className="rights-capability-matrix" aria-label={`Capability matrix for ${item.edition_id}`}>{capabilityLabels.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{item.capabilities[key] ? "Permitted" : "Denied"}</dd></div>)}</dl>
      <small>Effective {new Date(item.effective_from).toLocaleString()} {item.effective_until ? `until ${new Date(item.effective_until).toLocaleString()}` : "without a recorded end time"}. Version {item.version}.</small>
      <div className="standards-actions"><button type="button" className="button secondary compact" onClick={() => beginReplace(item)}>Replace rights</button><button type="button" className="button ghost compact" onClick={() => void revoke(item)}>Revoke rights</button></div>
    </article>)}</div> : null}
    {editing && capabilities ? <form className="standards-governed-form" onSubmit={replace} aria-labelledby="replace-rights-title">
      <h3 id="replace-rights-title">Replace exact rights version {editing.version}</h3>
      <div className="form-row"><label>Rights basis<select value={basis} onChange={(event) => setBasis(event.target.value)}><option value="organization_license">Organization license</option><option value="customer_supplied_declared">Customer supplied</option><option value="open_distribution">Open distribution</option><option value="internally_authored">Internally authored</option><option value="metadata_only">Metadata only</option><option value="unknown">Unknown</option></select></label><label>Rights status<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="active">Active</option><option value="expired">Expired</option><option value="revoked">Revoked</option><option value="unknown">Unknown</option></select></label></div>
      <fieldset><legend>Independent capabilities</legend>{capabilityLabels.map(([key, label]) => <label className="check-row" key={key}><input type="checkbox" checked={capabilities[key]} onChange={(event) => setCapabilities({ ...capabilities, [key]: event.target.checked })} />{label}</label>)}</fieldset>
      <div className="form-row"><label>AI permission<select value={permission} onChange={(event) => setPermission(event.target.value)}><option value="prohibited">Prohibited</option><option value="local_only">Local only</option><option value="approved_processor">Approved processor</option></select></label><label>Approved processor policy IDs<textarea disabled={permission !== "approved_processor"} value={policies} onChange={(event) => setPolicies(event.target.value)} placeholder="One policy ID per line" /></label></div>
      <div className="form-row"><label>Effective from<input required type="datetime-local" value={effectiveFrom} onChange={(event) => setEffectiveFrom(event.target.value)} /></label><label>Effective until <span>(optional)</span><input type="datetime-local" value={effectiveUntil} onChange={(event) => setEffectiveUntil(event.target.value)} /></label></div>
      <label>Rights authority reference<input required maxLength={500} value={authorityReference} onChange={(event) => setAuthorityReference(event.target.value)} /></label>
      <label>Rights authority SHA-256 digest<input required dir="ltr" pattern="[0-9a-f]{64}" value={authorityDigest} onChange={(event) => setAuthorityDigest(event.target.value)} /></label>
      <label>Human replacement rationale <span>(optional)</span><textarea maxLength={500} value={reason} onChange={(event) => setReason(event.target.value)} /></label>
      <div className="standards-actions"><button className="button primary">Confirm replacement</button><button type="button" className="button ghost" onClick={() => setEditing(null)}>Cancel</button></div>
    </form> : null}
  </section>;
}
