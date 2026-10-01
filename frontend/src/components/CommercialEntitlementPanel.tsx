import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, CommercialEntitlementStatus, CommercialEntitlementValidation, CommercialReasonCode } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";

const reasonLabels: Record<CommercialReasonCode, string> = {
  entitlement_missing: "No commercial entitlement is active for this deployment.",
  invalid_signature: "The signed entitlement was not accepted.",
  untrusted_key: "The signing authority is not trusted.",
  revoked_key: "The signing authority is no longer trusted.",
  organization_mismatch: "The entitlement is not bound to the current Organization.",
  deployment_mismatch: "The entitlement is not bound to this deployment.",
  not_yet_valid: "The entitlement is not currently valid.",
  grace: "The entitlement is in its server-determined grace period.",
  expired: "The entitlement has expired.",
  rollback_detected: "The entitlement revision would roll back accepted state.",
  same_revision_conflict: "This revision conflicts with the accepted entitlement.",
  time_untrusted: "Trusted time validation is unavailable.",
  package_not_entitled: "A requested package is not entitled.",
  seat_required: "A commercial seat is required.",
  seat_reserved: "This seat is reserved while capacity is reconciled.",
  over_capacity: "Assigned seats exceed server-authorized capacity.",
  release_sequence_out_of_range: "Release compatibility could not be established.",
};

function safeReason(reason: CommercialReasonCode | null) {
  return reason ? reasonLabels[reason] : "The server did not accept the commercial operation.";
}

function serverDate(value: string | null) {
  if (!value) return "Not established";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "Not disclosed" : parsed.toLocaleString();
}

function isStatus(value: CommercialEntitlementStatus): boolean {
  return typeof value?.available === "boolean" && typeof value?.effective_state === "string" && Array.isArray(value?.package_keys);
}

export function CommercialEntitlementPanel({ onStepUpRequired }: { onStepUpRequired?: () => void }) {
  const [status, setStatus] = useState<ApiResult<CommercialEntitlementStatus> | null>(null);
  const [signedEnvelope, setSignedEnvelope] = useState("");
  const [fileName, setFileName] = useState("");
  const [preview, setPreview] = useState<CommercialEntitlementValidation | null>(null);
  const [validatedEnvelope, setValidatedEnvelope] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => void api.commercialEntitlement().then(setStatus);
  useEffect(load, []);

  function handleStepUp() {
    setMessage("Recent administrator authentication is required. Confirm it in Sensitive security administration, then retry this action.");
    onStepUpRequired?.();
  }

  function resetPreview(value: string) {
    setSignedEnvelope(value);
    setPreview(null);
    setValidatedEnvelope(null);
    setMessage("");
  }

  async function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    try {
      resetPreview(await file.text());
    } catch {
      resetPreview("");
      setMessage("The selected entitlement file could not be read.");
    }
  }

  async function validate(event: FormEvent) {
    event.preventDefault();
    if (!signedEnvelope.trim()) {
      setMessage("Select or paste a signed entitlement envelope first.");
      return;
    }
    setBusy(true);
    const result = await api.validateCommercialEntitlement(signedEnvelope);
    setBusy(false);
    if (result.state === "step_up_required") return handleStepUp();
    if (result.state !== "success") {
      setPreview(null);
      setValidatedEnvelope(null);
      setMessage(result.state === "invalid" ? "The entitlement envelope format was not accepted." : result.state === "unavailable" ? "Commercial entitlement verification is temporarily unavailable." : "The entitlement could not be validated in the current authorized context.");
      return;
    }
    setPreview(result.data);
    setValidatedEnvelope(result.data.valid ? signedEnvelope : null);
    setMessage(result.data.valid ? "Server validation succeeded. Review the preview before explicit activation." : "");
  }

  async function activate() {
    if (!preview?.valid || validatedEnvelope !== signedEnvelope) return;
    if (!window.confirm("Activate this server-validated commercial entitlement for the current Organization and configured deployment?")) return;
    setBusy(true);
    const result = await api.activateCommercialEntitlement(signedEnvelope);
    setBusy(false);
    if (result.state === "step_up_required") return handleStepUp();
    if (result.state !== "success") {
      setMessage(result.state === "conflict" ? "Activation conflicted with current commercial state. Reload and validate again." : result.state === "unavailable" ? "Commercial entitlement activation is temporarily unavailable." : "The entitlement was not activated in the current authorized context.");
      return;
    }
    if (!result.data.valid) {
      setMessage(safeReason(result.data.reason_code));
      return;
    }
    setSignedEnvelope("");
    setFileName("");
    setPreview(null);
    setValidatedEnvelope(null);
    setMessage("The entitlement was activated by the server.");
    load();
  }

  const current = status?.state === "success" && isStatus(status.data) ? status.data : null;

  return <section className="surface commercial-panel" aria-labelledby="commercial-entitlement-title">
    <div className="surface-header"><h2 id="commercial-entitlement-title">Commercial entitlement</h2><p>Signed status and binding are evaluated by the server. This browser does not verify signatures, expiry, trusted time, or package authority.</p></div>
    {!status ? <LoadingState label="Loading server-derived commercial status…" /> : status.state === "protected" ? <ProtectedState /> : status.state !== "success" || !current ? <ErrorState retry={load} unavailable={status.state === "unavailable"} /> : current.reason_code === "entitlement_missing" ? <EmptyState title="No commercial entitlement" detail={safeReason(current.reason_code)} /> : <div className="commercial-status">
      <div className="commercial-status-heading"><StatusBadge value={current.effective_state.toUpperCase()} />{current.reason_code ? <span>{safeReason(current.reason_code)}</span> : <span>Effective state is server-derived.</span>}</div>
      <dl className="commercial-facts">
        <div><dt>Binding</dt><dd>Current Organization · configured deployment (server verified)</dd></div>
        <div><dt>Entitlement</dt><dd>{current.entitlement_id ?? "Not disclosed"}</dd></div>
        <div><dt>Revision</dt><dd>{current.revision ?? "Not established"}</dd></div>
        <div><dt>Digest prefix</dt><dd>{current.digest_prefix ?? "Not disclosed"}</dd></div>
        <div><dt>Packages</dt><dd>{current.package_keys.length ? current.package_keys.map((item) => item.replaceAll("_", " ")).join(", ") : "None disclosed"}</dd></div>
        <div><dt>Seat capacity</dt><dd>{current.seat_capacity ?? "Not established"}</dd></div>
        <div><dt>Valid until</dt><dd>{serverDate(current.valid_until)}</dd></div>
        <div><dt>Grace until</dt><dd>{serverDate(current.grace_until)}</dd></div>
        <div><dt>Support until</dt><dd>{serverDate(current.support_until)}</dd></div>
      </dl>
    </div>}
    <form className="bootstrap-form commercial-upload" onSubmit={validate}>
      <label>Signed entitlement file<input type="file" accept="application/json,.json" onChange={(event) => void chooseFile(event)} /></label>
      {fileName ? <p className="form-hint">Selected file: {fileName}</p> : null}
      <label>Signed entitlement envelope<textarea aria-label="Signed entitlement envelope" value={signedEnvelope} onChange={(event) => resetPreview(event.target.value)} rows={7} spellCheck={false} autoComplete="off" placeholder="Paste the complete signed JSON envelope" /></label>
      <div className="commercial-actions"><button className="button secondary" disabled={busy || !signedEnvelope.trim()}>{busy ? "Validating…" : "Validate on server"}</button>{preview?.valid && validatedEnvelope === signedEnvelope ? <button type="button" className="button primary" disabled={busy} onClick={() => void activate()}>Activate validated entitlement</button> : null}</div>
    </form>
    {preview ? <div className="commercial-preview" role="status"><strong>Server validation preview</strong><dl className="commercial-facts"><div><dt>Decision</dt><dd>{preview.valid ? "VALID" : "REJECTED"}</dd></div><div><dt>Effect</dt><dd>{preview.effect.toUpperCase()}</dd></div><div><dt>Entitlement</dt><dd>{preview.entitlement_id ?? "Not disclosed"}</dd></div><div><dt>Revision</dt><dd>{preview.revision ?? "Not established"}</dd></div><div><dt>Digest prefix</dt><dd>{preview.digest_prefix ?? "Not disclosed"}</dd></div></dl>{preview.reason_code ? <p>{safeReason(preview.reason_code)}</p> : null}</div> : null}
    {message ? <p className="form-message" role="status">{message}</p> : null}
  </section>;
}
