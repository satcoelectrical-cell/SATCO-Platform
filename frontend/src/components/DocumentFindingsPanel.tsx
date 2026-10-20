import { useEffect, useState, type FormEvent } from "react";
import { ExternalLink, GitCompareArrows, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import type { ApiResult, DocumentAnalysisSummary, DocumentCorrelationPage, DocumentEvidenceSource, DocumentFindingPage, SourceLocator } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";
import { Surface } from "./Page";

function sourceLabel(locator:SourceLocator){return `Page ${(locator.page_index??0)+1}${locator.table_key?` · ${locator.table_key}`:""}${locator.row_index!=null?` · row ${locator.row_index+1}`:""}${locator.column_label?` · ${locator.column_label}`:""}`;}

export function DocumentFindingsPanel({projectId,workspaceId,runs}:{projectId:number;workspaceId:number;runs:DocumentAnalysisSummary[]}){
  const [correlations,setCorrelations]=useState<ApiResult<DocumentCorrelationPage>|null>(null);
  const [findings,setFindings]=useState<ApiResult<DocumentFindingPage>|null>(null);
  const [selected,setSelected]=useState<string[]>([]);
  const [rationale,setRationale]=useState("");
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  const [reportFindingIds,setReportFindingIds]=useState<string[]>([]);
  const [reportPurpose,setReportPurpose]=useState<"field_experience"|"troubleshooting"|"engineering_analysis"|"technical_recommendation">("engineering_analysis");
  const [reportRationale,setReportRationale]=useState("");
  const [reportId,setReportId]=useState<string|null>(null);
  const eligible=runs.filter(run=>["requires_review","completed","completed_with_limitations"].includes(run.state));
  const runById=new Map(runs.map(run=>[run.analysis_run_id,run]));
  const load=()=>{setCorrelations(null);setFindings(null);void api.documentCorrelations(projectId,workspaceId).then(setCorrelations);void api.documentFindings(projectId,workspaceId).then(setFindings);};
  useEffect(load,[projectId,workspaceId]);
  useEffect(()=>{setSelected(current=>current.filter(id=>eligible.some(run=>run.analysis_run_id===id)));},[runs]);
  async function evaluate(event:FormEvent){event.preventDefault();if(selected.length<2||!rationale.trim())return;setBusy(true);setMessage("Running the approved deterministic document rules…");const result=await api.correlateDocuments(projectId,{analysis_run_ids:[...selected],rule_pack_id:"satco.document-correlation.v2",rationale:rationale.trim()});if(result.state==="success"){setMessage(`Evaluation complete: ${result.data.correlations.length} correlations and ${result.data.findings.length} advisory findings.`);setRationale("");load();}else setMessage(result.state==="invalid"?"Choose at least two completed analyses in the same workspace.":result.state==="conflict"?"This evaluation request changed. Refresh before retrying.":"Correlation is temporarily unavailable. No finding state changed.");setBusy(false);}
  function openSource(source:DocumentEvidenceSource){
    const target=window.open("","_blank");
    if(!target){setMessage("The source tab was blocked. Allow popups for this SATCO site and try again.");return;}
    let relay:MessageChannel|undefined;
    try{
      relay=new MessageChannel();
      target.document.title="SATCO authorized source";
      target.document.body.textContent="Loading authorized exact source…";
      const relayTarget=target as Window&{__satcoSourcePort?:MessagePort};
      relayTarget.__satcoSourcePort=relay.port2;
      const relayScript=target.document.createElement("script");
      relayScript.textContent=`(()=>{const port=window.__satcoSourcePort;delete window.__satcoSourcePort;window.opener=null;if(!port)return;port.addEventListener("message",event=>{const data=event.data;if(data?.type!=="open"||data.blob?.type!=="application/pdf"||!Number.isInteger(data.page)||data.page<1)return;const url=URL.createObjectURL(data.blob);document.title="SATCO source received";port.postMessage({type:"ready",url});setTimeout(()=>{port.close();window.location.replace(url+"#page="+data.page);},0);},{once:true});port.start();})();`;
      target.document.head.append(relayScript);
      target.opener=null;
    }catch{relay?.port1.close();relay?.port2.close();target.close();setMessage("SATCO could not isolate the source tab safely. No source was opened.");return;}
    if(!relay){target.close();setMessage("SATCO could not isolate the source tab safely. No source was opened.");return;}
    setMessage("Loading the authorized exact source…");
    void (async()=>{
      const result=await api.documentAnalysisSource(projectId,source.analysis_run_id);
      if(result.state!=="success"){
        relay.port1.close();relay.port2.close();
        if(!target.closed)target.close();
        setMessage(result.state==="protected"?"The exact source is not available in your current authorized context.":"The exact source could not be loaded. The reserved tab was closed safely.");
        return;
      }
      if(target.closed){relay.port1.close();relay.port2.close();setMessage("The reserved source tab was closed before the PDF finished loading.");return;}
      let objectUrl:string|null=null;
      let closePoll:number|undefined;
      let expiry:number|undefined;
      const cleanup=()=>{relay.port1.close();if(objectUrl){URL.revokeObjectURL(objectUrl);objectUrl=null;}if(closePoll!==undefined)window.clearInterval(closePoll);if(expiry!==undefined)window.clearTimeout(expiry);};
      try{
        closePoll=window.setInterval(()=>{if(target.closed)cleanup();},1000);
        relay.port1.addEventListener("message",event=>{const data=event.data as {type?:unknown;url?:unknown}|null;if(data?.type!=="ready"||typeof data.url!=="string"||!data.url.startsWith("blob:"))return;objectUrl=data.url;expiry=window.setTimeout(cleanup,300_000);setMessage("Authorized exact source opened in an isolated tab.");},{once:true});
        relay.port1.start();
        relay.port1.postMessage({type:"open",blob:result.data,page:(source.locator.page_index??0)+1});
      }catch{
        cleanup();if(!target.closed)target.close();
        setMessage("The exact source could not be opened safely. The reserved tab was closed.");
      }
    })();
  }
  async function generateReport(event:FormEvent){event.preventDefault();if(!reportFindingIds.length||!reportRationale.trim())return;setBusy(true);setReportId(null);setMessage("Generating a preliminary Technical Report draft…");const result=await api.createDocumentReportDraft(projectId,{workspace_id:workspaceId,finding_ids:[...reportFindingIds],purpose:reportPurpose,rationale:reportRationale.trim()});if(result.state==="success"){setReportId(result.data.report_id);setMessage("Preliminary draft generated. A Human must review the exact draft before acceptance.");}else setMessage(result.state==="protected"?"One or more findings are not available in this authorized workspace.":result.state==="invalid"?"Select at least one current finding and provide a rationale.":"Draft generation is temporarily unavailable. No report was accepted.");setBusy(false);}
  return <div className="document-findings-grid">
    <Surface title="Cross-document correlation" subtitle="Versioned deterministic rules over Human-reviewed candidates"><form className="document-correlation-form" onSubmit={evaluate}><fieldset disabled={busy}><legend>Analysis scope</legend>{eligible.length<2?<p>Complete and review at least two document analyses to enable correlation.</p>:eligible.map(run=><label key={run.analysis_run_id}><input type="checkbox" checked={selected.includes(run.analysis_run_id)} onChange={event=>setSelected(current=>event.target.checked?[...current,run.analysis_run_id]:current.filter(id=>id!==run.analysis_run_id))}/><span><strong>{run.safe_filename}</strong><small>{run.document_family?.replaceAll("_"," ")}</small></span></label>)}</fieldset><label>Evaluation rationale<textarea required minLength={1} maxLength={2000} value={rationale} onChange={event=>setRationale(event.target.value)}/></label><button className="button primary" disabled={busy||selected.length<2||!rationale.trim()}><GitCompareArrows size={15}/>{busy?"Evaluating…":"Run approved correlation rules"}</button></form><p className="supporting-live" role="status" aria-live="polite">{message}</p></Surface>
    <Surface title="Correlations" subtitle="Agreement is shown separately from advisory findings"><button type="button" className="button secondary compact" onClick={load}><RefreshCw size={14}/>Refresh</button>{!correlations?<LoadingState label="Loading correlations…"/>:correlations.state==="protected"?<ProtectedState/>:correlations.state!=="success"?<ErrorState unavailable={correlations.state==="unavailable"}/>:!correlations.data.items.length?<EmptyState title="No correlations yet" detail="Select reviewed analyses and run the approved rule pack."/>:<div className="document-correlation-list">{correlations.data.items.map(item=><article key={item.correlation_id}><div><StatusBadge value={item.status}/><strong>{item.summary}</strong></div><small>{item.rule_id} · version {item.rule_version}</small><p>{item.applicability}</p></article>)}</div>}</Surface>
    <Surface title="Missing information and discrepancies" subtitle="Advisory only; rules explain why each result exists">{!findings?<LoadingState label="Loading findings…"/>:findings.state==="protected"?<ProtectedState/>:findings.state!=="success"?<ErrorState unavailable={findings.state==="unavailable"}/>:!findings.data.items.length?<EmptyState title="No advisory findings" detail="No approved rule has produced a missing-information or discrepancy result."/>:<><div className="document-finding-list">{findings.data.items.map(finding=><article key={finding.finding_id}><header><div><label className="finding-report-choice"><input aria-label={`Include ${finding.title} in report`} type="checkbox" checked={reportFindingIds.includes(finding.finding_id)} onChange={event=>setReportFindingIds(current=>event.target.checked?[...current,finding.finding_id]:current.filter(id=>id!==finding.finding_id))}/><span>Include in draft</span></label><StatusBadge value={finding.kind}/><h4>{finding.title}</h4></div><StatusBadge value={finding.state}/></header><p>{finding.explanation}</p><details><summary>Why SATCO raised this</summary><dl><div><dt>Rule</dt><dd>{finding.rule_id} · version {finding.rule_version}</dd></div><div><dt>Applicability</dt><dd>{finding.applicability}</dd></div>{finding.uncertainty?<div><dt>Uncertainty</dt><dd>{finding.uncertainty}</dd></div>:null}</dl></details><div className="finding-evidence"><strong>Exact source evidence</strong>{finding.evidence_sources?.length?finding.evidence_sources.map(source=>{const locator=source.locator;return <div key={`${source.candidate_id}:${locator.locator_id}`}><span>{runById.get(source.analysis_run_id)?.safe_filename??"Bound source"} · {sourceLabel(locator)}</span>{locator.text_excerpt?<small>{locator.text_excerpt}</small>:null}<button type="button" className="button secondary compact" onClick={()=>openSource(source)}><ExternalLink size={13}/>Open exact source</button></div>;}):<p>Exact source bindings are unavailable. Refresh after the traceability service is restored.</p>}</div><p className="finding-advisory">SATCO has not selected engineering truth or closed this finding. Human engineering disposition remains required.</p></article>)}</div><form className="document-report-form" onSubmit={generateReport}><h4>Generate preliminary Technical Report</h4><p>Selected findings become integrity-bound material provenance. Generation never accepts the report.</p><label>Report purpose<select value={reportPurpose} onChange={event=>setReportPurpose(event.target.value as typeof reportPurpose)}><option value="engineering_analysis">Engineering analysis</option><option value="technical_recommendation">Technical recommendation</option><option value="troubleshooting">Troubleshooting</option><option value="field_experience">Field experience</option></select></label><label>Draft generation rationale<textarea required minLength={1} maxLength={2000} value={reportRationale} onChange={event=>setReportRationale(event.target.value)}/></label><button className="button primary" disabled={busy||!reportFindingIds.length||!reportRationale.trim()}>{busy?"Generating…":"Generate Technical Report draft"}</button>{reportId?<a className="button secondary" href={`/reports/${reportId}?project_id=${projectId}&workspace_id=${workspaceId}`}>Review generated draft</a>:null}</form></>}</Surface>
  </div>;
}
