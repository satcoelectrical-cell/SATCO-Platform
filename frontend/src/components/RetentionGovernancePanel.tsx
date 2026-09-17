import { useEffect, useState } from "react";
import type { EvidenceRecord } from "../api/types";
import { retentionApi, type RetentionState, type RetentionSubject } from "../services/retentionApi";
import { ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";
import { Surface } from "./Page";

export function RetentionGovernancePanel({evidence,projectId,workspaceId}:{evidence:EvidenceRecord[];projectId:number;workspaceId:number}){
 const [selected,setSelected]=useState(""); const [state,setState]=useState<RetentionState|null>(null); const [loadState,setLoadState]=useState("idle");
 const [message,setMessage]=useState(""); const [busy,setBusy]=useState(false); const [rationale,setRationale]=useState("");
 const item=evidence.find(x=>x.id===selected); const subject:RetentionSubject|undefined=item?{subject_kind:"evidence",subject_id:item.id,organization_id:item.organization_id,project_id:projectId,workspace_id:workspaceId}:undefined;
 const refresh=async()=>{if(!subject){setState(null);return;}setLoadState("loading");const r=await retentionApi.state(subject);setLoadState(r.state);setState(r.state==="success"?r.data:null);};
 useEffect(()=>{setSelected("");setState(null);setMessage("");setRationale("");},[projectId,workspaceId]); useEffect(()=>{void refresh();},[selected]);
 async function run(action:()=>Promise<{state:string}>){setBusy(true);const r=await action();setMessage(r.state==="success"?"Governance action recorded. Authoritative state reread completed.":r.state==="conflict"?"Retention state changed. Reread required before resubmission.":r.state==="unavailable"?"Governance state is unavailable; no optimistic success was applied.":"Governance action was not completed.");setBusy(false);await refresh();}
 const expected=state?.version??0;
 return <Surface title="Retention governance" subtitle="Human authority · server state is authoritative"><label>Evidence<select value={selected} onChange={e=>setSelected(e.target.value)}><option value="">Select visible Evidence</option>{evidence.map(x=><option key={x.id} value={x.id}>{x.supported_fact}</option>)}</select></label>
 {loadState==="loading"?<LoadingState/>:loadState==="protected"?<ProtectedState/>:loadState==="unavailable"?<ErrorState unavailable/>:state?<div className="record-list"><article><div><strong>Retention state</strong><span><StatusBadge value={state.retention_mode??"not_established"}/> · Eligibility <StatusBadge value={state.disposition_eligibility}/></span><p>Hold: {state.hold_status??"none"} · Human disposition: {state.disposition_decision}</p></div></article></div>:selected?<p className="form-hint">Retention state is not established.</p>:null}
 {subject?<><label>Human governance rationale<textarea rows={2} maxLength={2000} value={rationale} onChange={e=>setRationale(e.target.value)}/></label><div className="record-actions">
 <button type="button" className="button secondary" disabled={busy||!!state||!rationale.trim()} onClick={()=>void run(()=>retentionApi.policy(subject,{retention_mode:"retain_indefinitely",retention_until:null,policy_source:"human_subject_override",basis_code:"human.workbench",rationale:rationale.trim(),expected_version:0}))}>Establish retention policy</button>
 <button type="button" className="button secondary" disabled={busy||!state||state.hold_status==="active"||!rationale.trim()} onClick={()=>void run(()=>retentionApi.hold(subject,{reason_code:"human.workbench",rationale:rationale.trim(),authority_reference:"Evidence Workbench Human action",expected_version:expected}))}>Place Human hold</button>
 <button type="button" className="button secondary" disabled={busy||state?.hold_status!=="active"||!state.active_hold_id||!state.active_hold_version||!rationale.trim()} onClick={()=>void run(()=>retentionApi.release(subject,state!.active_hold_id!,{release_rationale:rationale.trim(),expected_version:state!.active_hold_version!}))}>Release Human hold</button>
 <button type="button" className="button secondary" disabled={busy||!state?.retention_record_id||!item||!rationale.trim()} onClick={()=>void run(()=>retentionApi.disposition(subject,{decision:"retain",reason:rationale.trim(),retention_record_id:state!.retention_record_id,subject_version_snapshot:item!.version,expected_version:expected}))}>Record Human retain decision</button>
 </div></>:null}<p aria-live="polite" role="status">{message}</p></Surface>;
}
