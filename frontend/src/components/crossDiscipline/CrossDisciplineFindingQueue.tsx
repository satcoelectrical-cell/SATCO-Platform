import type { XDIFinding } from "../../api/types";

export function CrossDisciplineFindingQueue({assessmentId,findings,onOpen}:{assessmentId:string|null;findings:XDIFinding[]|null;onOpen:(finding:XDIFinding)=>void}) {
  return <section className="cross-discipline-card" aria-label="Cross-discipline finding queue"><h3>Finding queue</h3>{!assessmentId?<p>No authorized Findings.</p>:findings?.length?<ul>{findings.map(finding=><li key={finding.finding_id}><button type="button" className="button ghost compact" aria-label={`Open owner for ${finding.subcode}`} onClick={()=>onOpen(finding)}>Finding {finding.ordinal} · {finding.category.replaceAll("_"," ")} · {finding.severity}</button></li>)}</ul>:<p>{findings?"No authorized Findings.":"Loading authorized Findings…"}</p>}</section>;
}
