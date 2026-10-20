import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { XDIAssessment, XDIFinding, XDIPage, XDIReadiness, XDIState } from "../api/types";
import { CrossDisciplineAssessmentHistory } from "./crossDiscipline/CrossDisciplineAssessmentHistory";
import { CrossDisciplineDispositionPanel } from "./crossDiscipline/CrossDisciplineDispositionPanel";
import { CrossDisciplineFindingDetail } from "./crossDiscipline/CrossDisciplineFindingDetail";
import { CrossDisciplineFindingQueue } from "./crossDiscipline/CrossDisciplineFindingQueue";
import { CrossDisciplineOverviewMatrix } from "./crossDiscipline/CrossDisciplineOverviewMatrix";
import { CrossDisciplineProvenancePanel } from "./crossDiscipline/CrossDisciplineProvenancePanel";
import { CrossDisciplineSourceComparison } from "./crossDiscipline/CrossDisciplineSourceComparison";
import { CrossDisciplineCommitmentContext } from "./crossDiscipline/CrossDisciplineCommitmentContext";
import { CrossDisciplineDependencyView } from "./crossDiscipline/CrossDisciplineDependencyView";
import { CrossDisciplinePotentialImpactView } from "./crossDiscipline/CrossDisciplinePotentialImpactView";
import { CrossDisciplineAIExplanation } from "./crossDiscipline/CrossDisciplineAIExplanation";
import { resolveOwnerRoute } from "../productExperience/routes";

export function CrossDisciplineIntelligencePanel({ projectId, workspaceIds = [] }: { projectId: number;workspaceIds?:number[] }) {
  const navigate=useNavigate();
  const [searchParams]=useSearchParams();
  const requestedAssessmentId=searchParams.get("assessment");
  const requestedFindingId=searchParams.get("finding");
  const [state,setState]=useState<XDIState>("loading");
  const [readiness,setReadiness]=useState<XDIReadiness|null>(null);
  const [assessments,setAssessments]=useState<XDIPage<XDIAssessment>|null>(null);
  const [selectedAssessmentId,setSelectedAssessmentId]=useState<string|null>(null);
  const [findings,setFindings]=useState<XDIFinding[]|null>(null);
  const [selectedFinding,setSelectedFinding]=useState<XDIFinding|null>(null);
  const [routeMessage,setRouteMessage]=useState("");
  useEffect(()=>{
    let active=true;
    setState("loading");setReadiness(null);setAssessments(null);setSelectedAssessmentId(null);setFindings(null);setSelectedFinding(null);setRouteMessage("");
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
        const first=(requestedAssessmentId?history.data.items.find(item=>item.assessment_id===requestedAssessmentId):null)??history.data.items[0];setSelectedAssessmentId(first?.assessment_id??null);
        if(first?.status==="indeterminate"){setState("indeterminate");return;}
        if(first?.status==="unavailable"){setState("unavailable");return;}
        setState(first?"ready":"empty");
      });
    return()=>{active=false;};
  },[projectId,requestedAssessmentId]);
  useEffect(()=>{
    let active=true;
    setFindings(null);setSelectedFinding(null);
    if(!selectedAssessmentId || typeof api.crossDisciplineFindings!=="function") return ()=>{active=false;};
    api.crossDisciplineFindings(projectId,selectedAssessmentId).then((result)=>{
      if(!active)return;
      if(result.state==="protected"){setFindings(null);setState("protected_not_found");return;}
      if(result.state!=="success"){setFindings(null);return;}
      setFindings(result.data.items);
      setSelectedFinding(requestedFindingId&&selectedAssessmentId===requestedAssessmentId?result.data.items.find(item=>item.finding_id===requestedFindingId)??null:null);
    }).catch(()=>{if(active)setFindings(null);});
    return()=>{active=false;};
  },[projectId,requestedAssessmentId,requestedFindingId,selectedAssessmentId]);
  async function openFinding(finding:XDIFinding){
    setRouteMessage("");
    const path=await resolveOwnerRoute({routeKind:"cross_discipline_finding",label:`Finding ${finding.ordinal}`,projectId,parentHandle:finding.assessment_id,targetHandle:finding.finding_id});
    if(path)navigate(path);else setRouteMessage("That Finding is no longer available in the authorized Project context.");
  }
  if(state==="protected_not_found")return null;
  if(state==="loading")return <section className="surface cross-discipline-intelligence" aria-busy="true" aria-label="Cross-discipline intelligence">Loading cross-discipline intelligence…</section>;
  return <section className={"surface cross-discipline-intelligence cross-discipline-state-"+state} aria-label="Cross-discipline intelligence">
    <header className="cross-discipline-heading"><div><span className="eyebrow">Deterministic · retained history</span><h2>Cross-discipline intelligence</h2><p className="cross-discipline-advisory">Advisory engineering output — Human disposition remains authoritative.</p></div><span role="status">{state.replaceAll("_"," ")}</span></header>
    {state==="unavailable"?<p role="alert">Cross-discipline intelligence is unavailable. No assessment result is implied.</p>:null}
    {state==="conflict"?<p role="alert">The assessment changed. Reloaded current server state is required.</p>:null}
    {state==="indeterminate"?<p role="status">Assessment is indeterminate. It is not a PASS or an empty result.</p>:null}
    <div className="cross-discipline-grid">
      <CrossDisciplineOverviewMatrix readiness={readiness} assessments={assessments?.items??[]} workspaceIds={workspaceIds}/>
      <CrossDisciplineFindingQueue assessmentId={selectedAssessmentId} findings={findings} onOpen={(finding)=>void openFinding(finding)}/>
      <CrossDisciplineFindingDetail finding={selectedFinding}/>
      <CrossDisciplineProvenancePanel assessmentId={selectedAssessmentId}/>
      <CrossDisciplineSourceComparison findings={findings}/>
      <CrossDisciplineCommitmentContext findings={findings}/>
      <CrossDisciplineDependencyView findings={findings}/>
      <CrossDisciplineDispositionPanel assessmentId={selectedAssessmentId}/>
      <CrossDisciplinePotentialImpactView impact={null}/>
      <CrossDisciplineAIExplanation explanation={null}/>
      <CrossDisciplineAssessmentHistory assessments={assessments?.items??[]}/>
    </div>
    {routeMessage?<p role="status">{routeMessage}</p>:null}
  </section>;
}
