import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, StandardsIntelligenceRun } from "../api/types";
import { StandardsStatePresentation } from "./StandardsStatePresentation";

export function StandardsIntelligencePanel({ projectId }: { projectId: number }) {
  const [purpose, setPurpose] = useState("");
  const [snapshots, setSnapshots] = useState<string[]>([]);
  const [assertions, setAssertions] = useState<string[]>([]);
  const [options,setOptions]=useState<ApiResult<{snapshots:{handle:string;label:string;availability_status:string}[];assertions:{handle:string;snapshot_handle:string;label:string;verification_status:string}[]}>|null>(null);
  const [result, setResult] = useState<ApiResult<StandardsIntelligenceRun> | null>(null);
  const [busy, setBusy] = useState(false);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setResult(null); setPurpose(""); setSnapshots([]); setAssertions([]); setOptions(null); if(projectId>0)void api.standardsIntelligenceOptions(projectId).then(setOptions); }, [projectId]);
  useEffect(() => { if (result) resultRef.current?.focus(); }, [result]);

  async function run(event: FormEvent) {
    event.preventDefault();
    const snapshotIds = snapshots;
    const assertionIds = assertions;
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
      <fieldset><legend>Authorized source snapshots</legend>{options?.state==="success"?options.data.snapshots.map(item=><label key={item.handle}><input type="checkbox" checked={snapshots.includes(item.handle)} onChange={()=>{setSnapshots(current=>current.includes(item.handle)?current.filter(value=>value!==item.handle):current.length<8?[...current,item.handle]:current);if(snapshots.includes(item.handle))setAssertions(current=>current.filter(value=>options.data.assertions.find(option=>option.handle===value)?.snapshot_handle!==item.handle));}} />{item.label}</label>):<p>No authorized snapshots are available.</p>}</fieldset>
      <fieldset><legend>Human-verified assertions (optional)</legend>{options?.state==="success"?options.data.assertions.filter(item=>snapshots.includes(item.snapshot_handle)).map(item=><label key={item.handle}><input type="checkbox" checked={assertions.includes(item.handle)} onChange={()=>setAssertions(current=>current.includes(item.handle)?current.filter(value=>value!==item.handle):[...current,item.handle])} />{item.label}</label>):null}</fieldset>
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
