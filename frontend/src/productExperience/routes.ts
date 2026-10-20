import { api } from "../api/client";
import { retentionApi } from "../services/retentionApi";

export const OWNER_ROUTE_KINDS = [
  "project_context","discipline_workspace","cross_discipline_finding","standards",
  "evidence_workbench","retention","engineering_performance_source","technical_report","organizational_memory",
] as const;
export type OwnerRouteKind = typeof OWNER_ROUTE_KINDS[number];
export interface OwnerRouteDescriptor { routeKind:OwnerRouteKind; label:string; projectId:number; workspaceId?:number|null; targetHandle?:string; parentHandle?:string; sourceVersion?:number|null }

const PERFORMANCE_INDICATORS=new Set([
  "required_input_readiness","blocked_work_aging","milestone_predictability",
  "deliverable_review_cycle_time","rework_revision_trend","risk_issue_change_aging",
  "interface_commitment_fulfilment","completeness_trend",
  "technical_report_acceptance_flow","evidence_availability",
]);

export async function resolveOwnerRoute(route:OwnerRouteDescriptor):Promise<string|null>{
  if(!OWNER_ROUTE_KINDS.includes(route.routeKind)) return null;
  switch(route.routeKind){
    case "project_context": { const r=await api.projectContext(route.projectId,route.workspaceId??null); return r.state==="success"?`/projects/${route.projectId}?section=intelligence`:null; }
    case "discipline_workspace": { if(!route.workspaceId)return null; const r=await api.workspacePackageApplicability(route.workspaceId); return r.state==="success"&&r.data.project_id===route.projectId?`/projects/${route.projectId}?workspace=${route.workspaceId}&section=discipline`:null; }
    case "standards": { const r=await api.projectStandards(route.projectId); return r.state==="success"?`/projects/${route.projectId}?section=intelligence`:null; }
    case "evidence_workbench": { if(!route.workspaceId)return null; const r=await api.evidence(route.projectId,route.workspaceId); return r.state==="success"?`/projects/${route.projectId}?workspace=${route.workspaceId}&section=evidence`:null; }
    case "retention": { if(!route.workspaceId)return null; const r=await retentionApi.workbench(route.projectId,route.workspaceId); return r.state==="success"&&r.data.project_id===route.projectId&&r.data.workspace_id===route.workspaceId?`/projects/${route.projectId}?workspace=${route.workspaceId}&section=evidence`:null; }
    case "engineering_performance_source": {
      const indicator=route.targetHandle?.startsWith("indicator:")?route.targetHandle.slice("indicator:".length):null;
      if(route.targetHandle&&(!indicator||!PERFORMANCE_INDICATORS.has(indicator)))return null;
      const r=await api.engineeringPerformanceIndicators(route.projectId,route.workspaceId);
      if(r.state!=="success")return null;
      if(indicator&&!r.data.observations?.some((item:{indicator_id?:string})=>item.indicator_id===indicator))return null;
      return `/projects/${route.projectId}${route.workspaceId?`?workspace=${route.workspaceId}&section=intelligence`:"?section=intelligence"}`;
    }
    case "cross_discipline_finding": { if(!route.targetHandle||!route.parentHandle)return null; const r=await api.crossDisciplineFinding(route.projectId,route.parentHandle,route.targetHandle); return r.state==="success"?`/projects/${route.projectId}?section=intelligence&assessment=${encodeURIComponent(route.parentHandle)}&finding=${encodeURIComponent(route.targetHandle)}`:null; }
    case "technical_report": {
      if(!route.targetHandle)return null;
      const r=await api.report(route.targetHandle);
      if(r.state!=="success")return null;
      if(r.data.project_id!=null&&r.data.project_id!==route.projectId)return null;
      if(route.workspaceId!=null&&r.data.workspace_id!==route.workspaceId)return null;
      if(route.sourceVersion!=null&&r.data.version!==route.sourceVersion)return null;
      return `/reports/${encodeURIComponent(route.targetHandle)}?project_id=${route.projectId}&workspace_id=${r.data.workspace_id}`;
    }
    case "organizational_memory": {
      if(!route.targetHandle)return null;
      const r=await api.memoryDetail(route.targetHandle); const summary=r.state==="success"?r.data.item?.summary:undefined;
      if(!summary)return null;
      if(summary.project_id!=null&&summary.project_id!==route.projectId)return null;
      if(route.workspaceId!=null&&summary.workspace_id!==route.workspaceId)return null;
      if(route.sourceVersion!=null&&summary.version!==route.sourceVersion)return null;
      return `/memory/${encodeURIComponent(route.targetHandle)}?project_id=${route.projectId}&workspace_id=${summary.workspace_id}`;
    }
  }
}
