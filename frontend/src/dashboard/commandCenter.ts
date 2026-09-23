import { api } from "../api/client";
import type { ApiResult, Capture, MemorySummary, Project, TechnicalReport, Workspace } from "../api/types";
import { retentionApi } from "../services/retentionApi";

export type SourceState = "success" | "protected" | "invalid" | "conflict" | "unavailable" | "error" | "not_requested";
export type SliceState = "ready" | "empty" | "partial" | "indeterminate" | "stale" | "protected" | "unavailable" | "not_requested";

export interface CommandCenterData {
  projects: Project[]; workspaces: Workspace[]; captures: Capture[]; reports: TechnicalReport[]; memory: MemorySummary[];
  journalState: SourceState;
  sourceStates: Record<"projects"|"workspaces"|"captures"|"reports"|"memory",SourceState>;
  sliceStates: Record<"projects"|"workspaces"|"captures"|"reports"|"memory",SliceState>;
  intelligence: Record<"packages"|"xdi"|"standards"|"evidence"|"retention"|"performance"|"actions", { state:SliceState; visibleCount?:number; detail?:string }>;
  selectedProjectId:number|null; selectedWorkspaceId:number|null;
}
export interface CommandMetric { label:string; value:number; detail:string; tone:"gold"|"green"|"blue"|"neutral" }
const stateOf=(result:ApiResult<unknown>):SourceState=>result.state;
const sliceOf=(result:ApiResult<{items:unknown[];total?:number}>|null,items:unknown[]):SliceState=>{
 if(!result)return"not_requested"; if(result.state==="protected"||result.state==="invalid")return"protected";
 if(result.state!=="success")return"unavailable"; if(!items.length)return"empty";
 return typeof result.data.total==="number"&&result.data.total>items.length?"partial":"ready";
};

const summary=(result:any,items:unknown[],completeness:"complete"|"partial"|"indeterminate"="complete"):{state:SliceState;visibleCount?:number}=>{if(!result)return{state:"not_requested"};if(result.state==="protected"||result.state==="invalid")return{state:"protected"};if(result.state!=="success")return{state:"unavailable"};if(completeness==="indeterminate")return{state:"indeterminate",visibleCount:items.length};if(completeness==="partial")return{state:"partial",visibleCount:items.length};return{state:items.length?"ready":"empty",visibleCount:items.length}};
const scalarSummary=(result:any):{state:SliceState}=>{if(!result)return{state:"not_requested"};if(result.state==="protected"||result.state==="invalid")return{state:"protected"};return{state:result.state==="success"?"ready":"unavailable"}};

export async function loadCommandCenter(context:{projectId?:number|null;workspaceId?:number|null}={}):Promise<ApiResult<CommandCenterData>>{
 const projectsResult=await api.projects(); if(projectsResult.state!=="success")return projectsResult;
 const projects=projectsResult.data.items; const selectedProject=context.projectId==null?null:projects.find(p=>p.id===context.projectId)??null;
 const selectedProjectId=selectedProject?.id??null;
 let workspaceResult:Awaited<ReturnType<typeof api.workspaces>>|null=null;
 let captureResult:Awaited<ReturnType<typeof api.captures>>|null=null;
 let journalResult:Awaited<ReturnType<typeof api.journal>>|null=null;
 if(selectedProjectId!=null)[workspaceResult,captureResult,journalResult]=await Promise.all([api.workspaces(selectedProjectId),api.captures(selectedProjectId),api.journal(selectedProjectId)]);
 const workspaces=workspaceResult?.state==="success"?workspaceResult.data.items:[];
 const captures=captureResult?.state==="success"?captureResult.data.items:[];
 const selectedWorkspace=context.workspaceId==null?null:workspaces.find(w=>w.id===context.workspaceId&&w.project_id===selectedProjectId)??null;
 let reportsResult:Awaited<ReturnType<typeof api.reports>>|null=null; let memoryResult:Awaited<ReturnType<typeof api.memory>>|null=null;
 let packagesResult:any=null,xdiResult:any=null,standardsResult:any=null,evidenceResult:any=null,retentionResult:any=null,performanceResult:any=null,actionsResult:any=null;
 if(selectedProjectId!=null)[packagesResult,xdiResult,standardsResult,performanceResult,actionsResult]=await Promise.all([api.effectiveDisciplinePackages(selectedProjectId),api.crossDisciplineAssessments(selectedProjectId),api.projectStandards(selectedProjectId),api.engineeringPerformanceHealth(selectedProjectId,selectedWorkspace?.id??null),api.engineeringPerformanceActions(selectedProjectId,selectedWorkspace?.id??null)]);
 if(selectedProjectId!=null&&selectedWorkspace)[reportsResult,memoryResult,evidenceResult,retentionResult]=await Promise.all([api.reports(selectedWorkspace.id,selectedProjectId),api.memory(selectedWorkspace.id,selectedProjectId),api.evidence(selectedProjectId,selectedWorkspace.id),retentionApi.workbench(selectedProjectId,selectedWorkspace.id)]);
 const reports=reportsResult?.state==="success"?reportsResult.data.items:[];
 const memory=memoryResult?.state==="success"?(memoryResult.data.page?.items??[]):[];
 return{state:"success",data:{projects,workspaces,captures,reports,memory,selectedProjectId,selectedWorkspaceId:selectedWorkspace?.id??null,journalState:journalResult?stateOf(journalResult):"not_requested",
  sourceStates:{projects:"success",workspaces:workspaceResult?stateOf(workspaceResult):"not_requested",captures:captureResult?stateOf(captureResult):"not_requested",reports:reportsResult?stateOf(reportsResult):"not_requested",memory:memoryResult?stateOf(memoryResult):"not_requested"},
  sliceStates:{projects:sliceOf(projectsResult,projects),workspaces:sliceOf(workspaceResult,workspaces),captures:sliceOf(captureResult,captures),reports:sliceOf(reportsResult,reports),memory:memory.length? "ready":memoryResult? (memoryResult.state==="success"?"empty":memoryResult.state==="protected"?"protected":"unavailable"):"not_requested"},
  intelligence:{packages:summary(packagesResult,packagesResult?.state==="success"?packagesResult.data.items:[]),xdi:summary(xdiResult,xdiResult?.state==="success"?xdiResult.data.items:[],xdiResult?.state==="success"&&xdiResult.data.next_cursor?"partial":"complete"),standards:summary(standardsResult,standardsResult?.state==="success"?standardsResult.data.items:[],standardsResult?.state==="success"&&standardsResult.data.next_cursor?"partial":"complete"),evidence:summary(evidenceResult,evidenceResult?.state==="success"?evidenceResult.data.items:[],evidenceResult?.state==="success"&&evidenceResult.data.total>evidenceResult.data.items.length?"partial":"complete"),retention:summary(retentionResult,retentionResult?.state==="success"?retentionResult.data.evidence:[],"indeterminate"),performance:scalarSummary(performanceResult),actions:summary(actionsResult,actionsResult?.state==="success"?(actionsResult.data.actions??[]):[])}}};
}
export function commandMetrics(data:CommandCenterData,now=new Date()):CommandMetric[]{
 const cutoff=now.getTime()-7*24*60*60*1000; const recent=data.projects.filter(p=>{const v=Date.parse(p.updated_at);return Number.isFinite(v)&&v>=cutoff&&v<=now.getTime()}).length;
 return[{label:"Visible projects",value:data.projects.length,detail:"Visible records · not a global total",tone:"gold"},{label:"High priority",value:data.projects.filter(p=>["high","critical"].includes(p.priority.toLowerCase())).length,detail:"Within visible records",tone:"blue"},{label:"Recently updated",value:recent,detail:"Visible Project updates · 7 days",tone:"green"},{label:"Capture contexts",value:data.captures.length,detail:data.selectedProjectId?"Selected Project · visible records":"Select a Project",tone:"neutral"}];
}
export function orderedProjectWork(projects:Project[]):Project[]{const rank=(priority:string)=>({critical:0,high:1,medium:2,low:3}[priority.toLowerCase()]??4);return[...projects].sort((a,b)=>rank(a.priority)-rank(b.priority)||Date.parse(b.updated_at)-Date.parse(a.updated_at)||a.id-b.id).slice(0,5)}
