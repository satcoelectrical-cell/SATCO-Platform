import type { EvidenceRecord } from "../api/types";
import type { EvidenceWorkbenchState } from "../services/retentionApi";
import { StatusBadge } from "./States";
import { Surface } from "./Page";
export function EvidenceLineageReliancePanel({evidence,workbench}:{evidence:EvidenceRecord[];workbench:EvidenceWorkbenchState|null}){
 const byId=new Map((workbench?.evidence??[]).map(x=>[x.evidence_id,x]));
 return <Surface title="Evidence lineage & reliance" subtitle="Canonical server lineage · accepted Report reliance remains historical truth">
  <div className="record-list">{evidence.map(item=>{const server=byId.get(item.id);return <article key={item.id}><div><strong>{item.supported_fact}</strong><span><StatusBadge value={item.lifecycle}/> · Evidence version {item.version}</span>{item.lifecycle==="current"?<p>Current engineering Evidence. Historical report reliance is not rewritten by retention actions.</p>:null}<p>{server?.replacement_evidence_id?"Canonical replacement is recorded for this superseded Evidence.":item.lifecycle==="superseded"?"Legacy supersession has no recorded canonical replacement; SATCO does not guess one.":"No replacement relationship is currently recorded."}</p><p>{server?.predecessor_evidence_ids.length?`${server.predecessor_evidence_ids.length} authorized predecessor Evidence relationship(s).`:"No authorized predecessor relationship is visible."} {server?.reliance.length?`${server.reliance.length} Human-accepted Technical Report reliance record(s) preserve historical Evidence versions.`:"No accepted Technical Report reliance is visible."}</p></div></article>})}</div>
 </Surface>;
}
