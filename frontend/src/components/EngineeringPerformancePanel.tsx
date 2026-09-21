import {useEffect,useState} from "react";
import {api} from "../api/client";
import {Surface} from "./Page";

type Observation={indicator_id:string;state:string;value:Record<string,unknown>;limitations:string[];source_cutoff?:string;calculation_method_version?:string};
type Factor={factor:string;state:string;indicator_ids:string[];limitations:string[];rationale_codes?:string[];rule_version?:string;source_handles?:string[]};
type Action={action_key:string;title_code:string;rationale_codes:string[];source_handles:string[];limitations:string[];status:string};
type DrillDown={indicator_id:string;state:string;items:{source_handle:string}[];limitations:string[];next_offset:number|null};

export function EngineeringPerformancePanel({projectId,workspaceId}:{projectId:number;workspaceId?:number|null}){
 const [indicators,setIndicators]=useState<any>(null),[health,setHealth]=useState<any>(null),[actions,setActions]=useState<any>(null),[trends,setTrends]=useState<any>(null);
 const [drill,setDrill]=useState<DrillDown|null>(null),[drillError,setDrillError]=useState<string|null>(null),[drillLoading,setDrillLoading]=useState(false);
 async function openDrillDown(indicatorId:string,offset=0){
  setDrillLoading(true);
  const result=await api.engineeringPerformanceDrillDown(projectId,indicatorId,workspaceId,20,offset);
  if(result.state==="success"){setDrill(result.data as DrillDown);setDrillError(null)}
  else {setDrill(null);setDrillError(result.state==="protected"?"Source details are protected.":"Source details are unavailable.")}
  setDrillLoading(false);
 }
 useEffect(()=>{void Promise.all([
  api.engineeringPerformanceIndicators(projectId,workspaceId),
  api.engineeringPerformanceHealth(projectId,workspaceId),
  api.engineeringPerformanceActions(projectId,workspaceId),
  api.engineeringPerformanceTrends(projectId,workspaceId),
 ]).then(([i,h,a,t])=>{setIndicators(i);setHealth(h);setActions(a);setTrends(t)})},[projectId,workspaceId]);
 const ok=(x:any)=>x?.state==="success"?x.data:null;const i=ok(indicators),h=ok(health),a=ok(actions),t=ok(trends);
 return <section className="engineering-performance" aria-labelledby="engineering-performance-title" dir="auto"><Surface title="Engineering Performance" subtitle="Derived, advisory and non-authoritative">
  <h2 id="engineering-performance-title">Engineering Performance</h2>
  <p>Human engineering authority remains final. Indicators explain engineering flow; they do not rank people.</p>
  {!i?<p role="status">Loading engineering performance…</p>:<section aria-label="Engineering indicators"><h3>Indicators</h3><div className="completeness-list">{i.observations.map((o:Observation)=><article key={o.indicator_id}><strong>{o.indicator_id.replaceAll("_"," ")}</strong><span>{o.state.replaceAll("_"," ")}</span><dl>{Object.entries(o.value??{}).map(([key,value])=><div key={key}><dt>{key.replaceAll("_"," ")}</dt><dd>{String(value)}</dd></div>)}</dl><small>Method: {o.calculation_method_version??"unknown"}</small>{o.source_cutoff&&<small>Source cutoff: {new Date(o.source_cutoff).toLocaleString()}</small>}{o.limitations?.map(x=><small key={x}>Limitation: {x.replaceAll("_"," ")}</small>)}<button type="button" className="button secondary" onClick={()=>void openDrillDown(o.indicator_id)}>Open authorized drill-down for {o.indicator_id.replaceAll("_"," ")}</button></article>)}</div><small>Window: {i.window_days} days</small></section>}
  {!h?null:<section aria-label="Engineering Health"><h3>Engineering Health</h3><div className="completeness-list">{h.factors.map((f:Factor)=><article key={f.factor}><strong>{f.factor.replaceAll("_"," ")}</strong><span>{f.state.replaceAll("_"," ")}</span><small>{f.indicator_ids.join(" · ")}</small>{f.rule_version&&<small>Rule: {f.rule_version}</small>}{f.rationale_codes?.map(x=><small key={x}>Rationale: {x.replaceAll("_"," ")}</small>)}{f.limitations?.map(x=><small key={x}>Limitation: {x.replaceAll("_"," ")}</small>)}</article>)}</div></section>}
  {!a?null:<section aria-label="Advisory next actions"><h3>Advisory next actions</h3>{a.actions.length?a.actions.map((x:Action)=><article key={x.action_key}><strong>{x.title_code.replaceAll("_"," ")}</strong><span>{x.status.replaceAll("_"," ")}</span><p>{x.rationale_codes.join(" · ").replaceAll("_"," ")}</p><small>{x.source_handles.join(" · ")}</small>{x.limitations.map(code=><small key={code}>Limitation: {code.replaceAll("_"," ")}</small>)}</article>):<p>No advisory next actions are currently projected.</p>}</section>}
  {!t?null:<section aria-label="Engineering trends"><h3>Trends</h3><p>{t.points.length?"Trend observations available.":"No persisted trend points are available yet."}</p>{t.points.map((point:any,index:number)=><p key={point.id??index}>{point.indicator_id} · {point.observation_state??point.state}{point.method_changed?" · method changed":""}</p>)}{t.limitations?.map((x:string)=><small key={x}>{x.replaceAll("_"," ")}</small>)}</section>}
  <section aria-label="Authorized drill-down" aria-live="polite"><h3>Authorized drill-down</h3>{drillLoading&&<p role="status">Loading authorized sources…</p>}{drillError&&<p>{drillError}</p>}{drill&&<><p>{drill.indicator_id.replaceAll("_"," ")} · {drill.state.replaceAll("_"," ")}</p>{drill.items.length?<ul>{drill.items.map(item=><li key={item.source_handle}>{item.source_handle}</li>)}</ul>:<p>No authorized source handles are available.</p>}{drill.limitations.map(code=><small key={code}>{code.replaceAll("_"," ")}</small>)}{drill.next_offset!==null&&<button type="button" className="button secondary" onClick={()=>void openDrillDown(drill.indicator_id,drill.next_offset!)}>Next sources</button>}</>}</section>
 </Surface></section>
}
