import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, StandardsIntelligenceRun } from "../api/types";
import { StandardsStatePresentation } from "./StandardsStatePresentation";

export function StandardsIntelligencePanel({ projectId }: { projectId: number }) {
  const [purpose, setPurpose] = useState("");
  const [snapshots, setSnapshots] = useState("");
  const [assertions, setAssertions] = useState("");
  const [result, setResult] = useState<ApiResult<StandardsIntelligenceRun> | null>(null);
  const [busy, setBusy] = useState(false);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setResult(null); setPurpose(""); setSnapshots(""); setAssertions(""); }, [projectId]);
  useEffect(() => { if (result) resultRef.current?.focus(); }, [result]);

  async function run(event: FormEvent) {
    event.preventDefault();
    const snapshotIds = snapshots.split(/\s*,\s*/).filter(Boolean);
    const assertionIds = assertions.split(/\s*,\s*/).filter(Boolean);
    if (!purpose.trim() || !snapshotIds.length) return;
    setBusy(true); setResult(null);
    setResult(await api.standardsIntelligence(projectId, { purpose: purpose.trim(), snapshot_ids: snapshotIds, assertion_ids: assertionIds }));
    setBusy(false);
  }

  return <section className="standards-panel" aria-labelledby="standards-intelligence-title">
    <h2 id="standards-intelligence-title">Standards advisory intelligence</h2>
    <p>Human-requested and advisory only. AI cannot declare compliance, applicability, approval, acceptance, or change the deterministic result.</p>
    <form className="standards-governed-form" onSubmit={run}>
      <label>Human advisory purpose<textarea required maxLength={500} value={purpose} onChange={(event) => setPurpose(event.target.value)} /></label>
      <label>Authorized snapshot IDs <span>(comma separated, maximum 8)</span><input required value={snapshots} onChange={(event) => setSnapshots(event.target.value)} dir="ltr" /></label>
      <label>Human-verified assertion IDs <span>(optional, comma separated)</span><input value={assertions} onChange={(event) => setAssertions(event.target.value)} dir="ltr" /></label>
      <button className="button secondary" disabled={busy}>{busy ? "Running bounded advisory…" : "Run advisory check"}</button>
    </form>
    <div ref={resultRef} role="status" tabIndex={-1}>{result?.state === "success" ? <>
      <div className="standards-row-heading"><strong>Advisory interaction</strong><StandardsStatePresentation state={result.data.result_status ?? result.data.phase_status} /></div>
      <p>Deterministic result retained independently of AI.</p>
      <dl className="intelligence-deterministic">{Object.entries(result.data.deterministic).sort(([left], [right]) => left.localeCompare(right)).map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{value}</dd></div>)}</dl>
      {result.data.advisory?.suggestions.length ? <div className="standards-list" aria-label="Advisory suggestions">{result.data.advisory.suggestions.map((item) => <article key={`${item.handle}-${item.rationale_code}`}><strong>{item.rationale_code.replaceAll("_", " ")}</strong><p>{item.advisory}</p><code dir="ltr">{item.handle}</code><small>Advisory only; Human review is required.</small></article>)}</div> : null}
      {result.data.result_status === "not_permitted" ? <p>AI processing is not permitted by current rights or processor policy. No advisory output is available.</p> : null}
      {result.data.result_status === "invalid_output" ? <p>The provider response failed the closed output contract. No partial suggestion was accepted.</p> : null}
      {result.data.failure_code ? <p>Advisory unavailable: {result.data.failure_code}. The deterministic result remains available.</p> : null}
      <code dir="ltr">Run {result.data.run_id}</code>
    </> : result ? <p>{result.state === "protected" ? "This advisory context is not available. Previous protected detail has been cleared." : result.state === "conflict" ? "The advisory state changed; no second provider call was attempted." : "The advisory run could not be completed. No unsafe output is shown."}</p> : null}</div>
  </section>;
}
