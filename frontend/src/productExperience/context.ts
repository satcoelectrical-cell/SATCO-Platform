import type { ApiResult, Paginated, Project, Workspace } from "../api/types";
export type PopulationCompleteness = "complete" | "partial" | "indeterminate" | "unavailable";
export interface PopulationView<T> { items:T[]; completeness:PopulationCompleteness; returnedCount:number; authorizedTotal?:number; hasContinuation:boolean }
export function populationFromPage<T>(result:ApiResult<Paginated<T>>|null):PopulationView<T>{
 if(!result||result.state!=="success")return{items:[],completeness:result?.state==="unavailable"?"unavailable":"indeterminate",returnedCount:0,hasContinuation:false};
 const {items,total,page,size}=result.data; const complete=Number.isFinite(total)&&total>=0&&page*size>=total;
 return{items,completeness:complete?"complete":"partial",returnedCount:items.length,authorizedTotal:total,hasContinuation:!complete};
}
export interface ProductContext { projectId:number|null; workspaceId:number|null }
export function selectProject(context:ProductContext,projectId:number|null):ProductContext{return context.projectId===projectId?context:{projectId,workspaceId:null}}
export function selectWorkspace(context:ProductContext,workspace:Workspace|null):ProductContext{
 if(!workspace)return{...context,workspaceId:null}; if(context.projectId!==workspace.project_id)return context; return{...context,workspaceId:workspace.id};
}
export function validateContext(context:ProductContext,projects:Project[],workspaces:Workspace[]):ProductContext{
 const project=projects.find(item=>item.id===context.projectId); if(!project)return{projectId:null,workspaceId:null};
 if(context.workspaceId==null)return{projectId:project.id,workspaceId:null};
 const workspace=workspaces.find(item=>item.id===context.workspaceId&&item.project_id===project.id); return{projectId:project.id,workspaceId:workspace?.id??null};
}

export interface AuthorizedOption { value:string; label:string; description?:string }
export function projectOptions(projects:Project[]):AuthorizedOption[]{return projects.map(item=>({value:String(item.id),label:`${item.project_code} — ${item.name}`,description:item.customer.name}))}
export function workspaceOptions(workspaces:Workspace[],projectId:number|null):AuthorizedOption[]{return projectId==null?[]:workspaces.filter(item=>item.project_id===projectId).map(item=>({value:String(item.id),label:item.display_name,description:item.discipline}))}
