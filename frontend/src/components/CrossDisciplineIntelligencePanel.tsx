import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { XDIAssessment, XDIPage, XDIReadiness, XDIState } from "../api/types";
import { CrossDisciplineAssessmentHistory } from "./crossDiscipline/CrossDisciplineAssessmentHistory";
import { CrossDisciplineDispositionPanel } from "./crossDiscipline/CrossDisciplineDispositionPanel";
import { CrossDisciplineFindingDetail } from "./crossDiscipline/CrossDisciplineFindingDetail";
import { CrossDisciplineFindingQueue } from "./crossDiscipline/CrossDisciplineFindingQueue";
import { CrossDisciplineOverviewMatrix } from "./crossDiscipline/CrossDisciplineOverviewMatrix";
import { CrossDisciplineProvenancePanel } from "./crossDiscipline/CrossDisciplineProvenancePanel";

export function CrossDisciplineIntelligencePanel({ projectId, workspaceIds = [] }: { projectId: number;workspaceIds?:number[] }) {
  const [state,setState]=useState<XDIState>("loading");
  const [readiness,setReadiness]=useState<XDIReadiness|null>(null);
  const [assessments,setAssessments]=useState<XDIPage<XDIAssessment>|null>(null);
  const [selectedAssessmentId,setSelectedAssessmentId]=useState<string|null>(null);
  useEffect(()=>{
    let active=true;
    setState("loading");setReadiness(null);setAssessments(null);setSelectedAssessmentId(null);
    const readinessRequest=typeof api.crossDisciplineReadiness==="function"
      ? api.crossDisciplineReadiness(projectId)
      : Promise.resolve({state:"unavailable"} as const);
    const historyRequest=typeof api.crossDisciplineAssessments==="function"
      ? api.crossDisciplineAssessments(projectId)
      : Promise.resolve({state:"unavailable"} as const);
    Promise.all([readinessRequest,historyRequest])
      .then(([ready,history])=>{
        if(!active)return;
        if(ready.state==="protected"||history.state==="protected"){setState("protected_not_found");return;}
        if(ready.state!=="success"||history.state!=="success"){setState(ready.state==="conflict"||history.state==="conflict"?"conflict":"unavailable");return;}
        setReadiness(ready.data);setAssessments(history.data);
        if(ready.data.state==="unavailable"||ready.data.state==="not_ready"){setState("unavailable");return;}
        const first=history.data.items[0];setSelectedAssessmentId(first?.assessment_id??null);
        if(first?.status==="indeterminate"){setState("indeterminate");return;}
        if(first?.status==="unavailable"){setState("unavailable");return;}
        setState(first?"ready":"empty");
      });
    return()=>{active=false;};
  },[projectId]);
  if(state==="protected_not_found")return null;
  if(state==="loading")return <section className="surface cross-discipline-intelligence" aria-busy="true" aria-label="Cross-discipline intelligence">Loading cross-discipline intelligence…</section>;
  return <section className={"surface cross-discipline-intelligence cross-discipline-state-"+state} aria-label="Cross-discipline intelligence">
    <header className="cross-discipline-heading"><div><span className="eyebrow">Deterministic · retained history</span><h2>Cross-discipline intelligence</h2><p className="cross-discipline-advisory">Advisory engineering output — Human disposition remains authoritative.</p></div><span role="status">{state.replaceAll("_"," ")}</span></header>
    {state==="unavailable"?<p role="alert">Cross-discipline intelligence is unavailable. No assessment result is implied.</p>:null}
    {state==="conflict"?<p role="alert">The assessment changed. Reloaded current server state is required.</p>:null}
    {state==="indeterminate"?<p role="status">Assessment is indeterminate. It is not a PASS or an empty result.</p>:null}
    <div className="cross-discipline-grid">
      <CrossDisciplineOverviewMatrix readiness={readiness} assessments={assessments?.items??[]} workspaceIds={workspaceIds}/>
      <CrossDisciplineFindingQueue assessmentId={selectedAssessmentId}/>
      <CrossDisciplineFindingDetail finding={null}/>
      <CrossDisciplineProvenancePanel assessmentId={selectedAssessmentId}/>
      <CrossDisciplineDispositionPanel assessmentId={selectedAssessmentId}/>
      <CrossDisciplineAssessmentHistory assessments={assessments?.items??[]}/>
    </div>
  </section>;
}
