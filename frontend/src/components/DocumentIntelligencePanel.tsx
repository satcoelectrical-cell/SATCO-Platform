import { useEffect, useState, type FormEvent } from "react";
import { FileSearch, RefreshCw, ShieldCheck } from "lucide-react";
import { api } from "../api/client";
import type { ApiResult, DocumentAnalysisPage, DocumentAnalysisSummary, DocumentFamily, SupportingFilePage } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";
import { Surface } from "./Page";
import { DocumentCandidateInspector } from "./DocumentCandidateInspector";
import { DocumentFindingsPanel } from "./DocumentFindingsPanel";

function familyLabel(value:DocumentFamily|null){return value?value.replaceAll("_"," "):"Awaiting classification";}

export function DocumentIntelligencePanel({projectId,workspaceId}:{projectId:number;workspaceId:number}){
  const [files,setFiles]=useState<ApiResult<SupportingFilePage>|null>(null);
  const [runs,setRuns]=useState<ApiResult<DocumentAnalysisPage>|null>(null);
  const [assetId,setAssetId]=useState("");
  const [familyHint,setFamilyHint]=useState<DocumentFamily|"">("");
  const [rationale,setRationale]=useState("");
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  const [selectedRun,setSelectedRun]=useState<DocumentAnalysisSummary|null>(null);
  const load=()=>{setFiles(null);setRuns(null);void api.supportingFiles(projectId,workspaceId).then(setFiles);void api.documentAnalyses(projectId,workspaceId).then(setRuns);};
  useEffect(load,[projectId,workspaceId]);
  const processing=runs?.state==="success"&&runs.data.items.some(run=>["queued","extracting","interpreting"].includes(run.state));
  useEffect(()=>{if(!processing)return;const timer=window.setInterval(()=>{void api.documentAnalyses(projectId,workspaceId).then(setRuns);},1500);return()=>window.clearInterval(timer);},[processing,projectId,workspaceId]);
  const available=files?.state==="success"?files.data.items.filter(item=>item.lifecycle==="available"&&item.media_type==="application/pdf"):[];
  async function start(event:FormEvent){
    event.preventDefault();const asset=available.find(item=>item.id===assetId);if(!asset||!rationale.trim())return;
    setBusy(true);setMessage("Requesting analysis for the exact available document version…");
    const result=await api.createDocumentAnalysis(projectId,{workspace_id:workspaceId,supporting_file_asset_id:asset.id,expected_asset_version:asset.version,expected_content_digest:asset.content_digest,family_hint:familyHint||null,rationale:rationale.trim()});
    if(result.state==="success"){setMessage("Analysis queued. SATCO will preserve Human review before any canonical promotion.");setAssetId("");setRationale("");load();}
    else setMessage(result.state==="protected"?"This document is not available in the current project scope.":result.state==="invalid"?"The selected document or request changed. Refresh and try again.":"Analysis is temporarily unavailable. No engineering information was promoted.");
    setBusy(false);
  }
  async function retry(runId:string,version:number){setBusy(true);setMessage("Requesting a safe retry against the same source version…");const result=await api.retryDocumentAnalysis(projectId,runId,version);setMessage(result.state==="success"?"Retry queued against the unchanged source. Previous extraction history remains intact.":result.state==="invalid"?"This analysis cannot be retried. Start a new analysis if the source changed.":"Retry is temporarily unavailable. No engineering information was promoted.");if(result.state==="success")load();setBusy(false);}
  return <section className="document-intelligence" aria-labelledby="document-intelligence-title">
    <header className="document-intelligence-heading"><div><span className="eyebrow">Evidence-first document understanding</span><h2 id="document-intelligence-title">Document Intelligence</h2><p>Extracted information remains advisory until an authorized engineer reviews and promotes it.</p></div><ShieldCheck aria-hidden="true"/></header>
    <div className="document-intelligence-grid">
      <Surface title="Request analysis" subtitle="Available PDFs only; optional family hint is never authority"><form className="document-analysis-form" onSubmit={start}><label>Engineering document<select value={assetId} onChange={event=>setAssetId(event.target.value)} required><option value="">Select an available PDF</option>{available.map(item=><option key={item.id} value={item.id}>{item.safe_filename} · version {item.version}</option>)}</select></label><label>Document family hint<select value={familyHint} onChange={event=>setFamilyHint(event.target.value as DocumentFamily|"")}><option value="">Let SATCO classify</option><option value="narrative_engineering">Narrative engineering document</option><option value="tabular_engineering">Tabular engineering document</option></select></label><label>Human rationale<textarea rows={3} minLength={1} maxLength={2000} required value={rationale} onChange={event=>setRationale(event.target.value)}/></label><button className="button primary" disabled={busy||!assetId||!rationale.trim()}><FileSearch size={16}/>{busy?"Requesting…":"Start analysis"}</button>{!available.length&&files?.state==="success"?<p className="form-hint">Upload a PDF and wait for scanner-cleared availability before requesting analysis.</p>:null}</form></Surface>
      <Surface title="Analysis runs" subtitle="Customer-readable progress; provider internals remain protected"><button type="button" className="button secondary compact" onClick={load}><RefreshCw size={15}/>Refresh</button>{!runs?<LoadingState label="Loading document analyses…"/>:runs.state==="protected"?<ProtectedState/>:runs.state!=="success"?<ErrorState unavailable={runs.state==="unavailable"}/>:!runs.data.items.length?<EmptyState title="No analyses yet" detail="Select an available PDF to create the first traceable analysis run."/>:<div className="document-run-list">{runs.data.items.map(run=><article key={run.analysis_run_id}><div><strong>{run.safe_filename}</strong><span>{familyLabel(run.document_family)} · source version {run.source_asset_version}</span><small>{run.progress.customer_message}</small>{run.limitations.map(item=><small key={item}>{item}</small>)}<progress max={run.progress.total_units??1} value={run.progress.completed_units}/></div><div><StatusBadge value={run.state}/><small>{run.unreviewed_count} awaiting review</small>{run.allowed_actions.includes("review_candidates")?<button type="button" className="button primary compact" onClick={()=>setSelectedRun(run)}><FileSearch size={14}/>Inspect evidence</button>:null}{run.allowed_actions.includes("retry")?<button type="button" className="button secondary compact" disabled={busy} onClick={()=>void retry(run.analysis_run_id,run.version)}><RefreshCw size={14}/>Retry</button>:null}</div></article>)}</div>}</Surface>
    </div>{runs?.state==="success"?<DocumentFindingsPanel projectId={projectId} workspaceId={workspaceId} runs={runs.data.items}/>:null}{selectedRun?<DocumentCandidateInspector projectId={projectId} run={selectedRun} onUpdated={load} onClose={()=>setSelectedRun(null)}/>:null}<p className="supporting-live" aria-live="polite" role="status">{message}</p>
  </section>;
}
