import { useEffect, useState } from "react";
import { ChevronRight, Network, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import type { ApiResult, ContextNodeKind, OneHopSuccess, ProjectContextItem, ProjectContextSection, ProjectContextSectionKind, ProjectContextSuccess } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";
import { Surface } from "./Page";

const sectionLabels:Record<ProjectContextSectionKind,string>={project_basis:"Project basis",execution:"Execution",deliverables:"Deliverables",project_controls:"Project controls",engineering_context:"Engineering context",engineering_objects:"Engineering objects",evidence:"Evidence",supporting_files:"Supporting files",technical_reports:"Technical reports",organizational_memory:"Organizational memory"};

function nodeSelector(item:ProjectContextItem):{kind:ContextNodeKind;value:string|number}|null {
  const kindMap:Record<string,ContextNodeKind>={project_basis:"project",execution:"execution_plan",deliverable:"deliverable","project_control:risk":"risk","project_control:issue":"issue","project_control:human_decision":"human_decision","project_control:change":"change",engineering_context:"engineering_context",engineering_object:"engineering_object",evidence:"evidence",supporting_file:"supporting_file",technical_report:"technical_report",organizational_memory:"organizational_memory"};
  const kind=kindMap[item.item_kind]; if(!kind)return null;
  const rawByKind:Record<ContextNodeKind,string|number|undefined|null>={project:item.project_id,workspace:item.workspace_id,execution_plan:item.plan_id,activity:undefined,milestone:undefined,deliverable:item.deliverable_id,deliverable_revision:undefined,risk:item.control_id,issue:item.control_id,human_decision:item.control_id,change:item.control_id,change_impact:undefined,engineering_object:item.object_id,engineering_context:item.context_id??item.selector,evidence:item.evidence_id,supporting_file:item.asset_id,technical_report:item.report_id,organizational_memory:item.memory_id};
  const raw=rawByKind[kind];
  if(raw===undefined||raw===null)return null;
  return {kind,value:["project","workspace","engineering_context"].includes(kind)?Number(raw):String(raw)};
}

function itemLabel(item:ProjectContextItem){return item.title??item.project_name??item.code??item.filename??item.title_or_purpose??item.purpose??item.object_type??item.evidence_kind??item.report_type??item.item_kind.replaceAll("_"," ");}

function SectionCard({section,onContinue,onRelated}:{section:ProjectContextSection;onContinue:(section:ProjectContextSectionKind,token:string)=>void;onRelated:(item:ProjectContextItem)=>void}){
  const state=section.state;
  let body:React.ReactNode;
  if(state.state==="not_disclosed") body=<ProtectedState/>;
  else if(state.state==="unavailable") body=<ErrorState unavailable/>;
  else if(state.state==="not_established") body=<EmptyState title="Not established" detail="This canonical source has not been established."/>;
  else if(state.state==="empty") body=<EmptyState title="No visible records" detail="No authorized records are currently visible."/>;
  else body=<><p className="context-visible" aria-live="polite">{state.visible_count} visible {state.visible_count===1?"record":"records"}{state.truncated.truncated?" · bounded view":""}</p>
    <div className="context-records">{section.items.map((item)=><article key={`${item.item_kind}:${item.selector}`}><div><strong>{itemLabel(item)}</strong><span>{item.item_kind.replaceAll("_"," ")} · {item.standing??"standing unavailable"}</span></div><div className="context-classification"><StatusBadge value={item.provenance.authority_class}/><StatusBadge value={item.provenance.temporal_class}/></div>{nodeSelector(item)?<button type="button" className="button secondary compact" onClick={()=>onRelated(item)}>Related context<ChevronRight size={14}/></button>:null}</article>)}</div>
    {state.truncated.continuation?<button type="button" className="button secondary context-more" onClick={()=>onContinue(section.kind,state.truncated.continuation!.continuation)}>Load next bounded page</button>:null}</>;
  return <Surface title={sectionLabels[section.kind]} subtitle={state.state.replaceAll("_"," ")}><section className="context-section" aria-labelledby={`context-${section.kind}`}>
    <h3 id={`context-${section.kind}`} className="sr-only">{sectionLabels[section.kind]}</h3>
    {body}
  </section></Surface>;
}

export function ProjectEngineeringContextPanel({projectId,workspaceId}:{projectId:number;workspaceId?:number|null}){
  const [context,setContext]=useState<ApiResult<ProjectContextSuccess>|null>(null); const [related,setRelated]=useState<ApiResult<OneHopSuccess>|null>(null); const [relatedStart,setRelatedStart]=useState<{kind:ContextNodeKind;value:string|number}|null>(null);
  const load=()=>{setContext(null);void api.projectContext(projectId,workspaceId).then(setContext);};
  useEffect(load,[projectId,workspaceId]);
  async function continueSection(kind:ProjectContextSectionKind,token:string){const next=await api.projectContext(projectId,workspaceId,kind,token);if(next.state!=="success"){setContext(next);return;}setContext((current)=>current?.state==="success"?{state:"success",data:{...current.data,sections:current.data.sections.map((section)=>{const page=next.data.sections[0];if(section.kind!==kind||section.state.state!=="available"||page.state.state!=="available")return section;return {...page,items:[...section.items,...page.items],state:{...page.state,visible_count:section.items.length+page.items.length}};})}}:next);}
  async function showRelated(item:ProjectContextItem){const selector=nodeSelector(item);if(!selector)return;setRelatedStart(selector);setRelated(null);setRelated(await api.relatedContext(projectId,selector.kind,selector.value,workspaceId));}
  async function continueRelated(){if(related?.state!=="success"||!relatedStart||!related.data.truncated.continuation)return;const next=await api.relatedContext(projectId,relatedStart.kind,relatedStart.value,workspaceId,related.data.truncated.continuation.continuation);if(next.state!=="success"){setRelated(next);return;}setRelated({state:"success",data:{...next.data,edges:[...related.data.edges,...next.data.edges],nodes:[...related.data.nodes,...next.data.nodes]}});}
  return <section className="project-context" aria-labelledby="project-context-title"><header className="project-context-heading"><div><span className="eyebrow">Read-only engineering intelligence</span><h2 id="project-context-title">Project Engineering Context</h2><p>Canonical owner-authorized context. Partial and unavailable sources remain explicitly identified.</p></div><button type="button" className="button secondary" onClick={load}><RefreshCw size={15}/>Refresh context</button></header>
    {!context?<LoadingState/>:context.state==="protected"||context.state==="invalid"?<ProtectedState/>:context.state!=="success"?<ErrorState unavailable={context.state==="unavailable"}/>:<><p className="context-observation" role="status">Observation {context.data.observation_status.replaceAll("_"," ")} · {context.data.sections.length} canonical sections</p><div className="project-context-grid">{context.data.sections.map((section)=><SectionCard key={section.kind} section={section} onContinue={continueSection} onRelated={showRelated}/>)}</div></>}
    {relatedStart?<aside className="related-context" aria-labelledby="related-context-title"><div className="related-context-heading"><Network/><div><h3 id="related-context-title">Related Context</h3><p>Authorized one-hop relationships only. Returned targets are not expanded.</p></div></div>{!related?<LoadingState/>:related.state==="protected"||related.state==="invalid"?<ProtectedState/>:related.state!=="success"?<ErrorState unavailable={related.state==="unavailable"}/>:related.data.edges.length===0?<EmptyState title="No related context visible" detail="No authorized explicit relationship is visible within this bounded view."/>:<><div className="related-records">{related.data.edges.map((edge,index)=><article key={`${edge.relationship_selector}:${index}`}><strong>{typeof edge.relationship_kind==="string"?edge.relationship_kind.replaceAll("_"," "):`${edge.relationship_kind.family} · ${edge.relationship_kind.relationship_type}`}</strong><span>{edge.source.kind.replaceAll("_"," ")} → {edge.target.kind.replaceAll("_"," ")}</span><StatusBadge value={edge.provenance.authority_class}/></article>)}</div>{related.data.truncated.continuation?<button type="button" className="button secondary" onClick={continueRelated}>Load more related context</button>:null}</>}</aside>:null}
  </section>;
}
