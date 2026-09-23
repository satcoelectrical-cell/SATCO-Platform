import {populationFromPage,selectProject,selectWorkspace,validateContext} from "../productExperience/context";
import type {Project,Workspace} from "../api/types";
const project=(id:number):Project=>({id,project_code:`P-${id}`,name:`Project ${id}`,description:null,customer:{id,name:`Customer ${id}`},status:"active",priority:"medium",owner:null,primary_assignee:null,progress:0,target_completion_date:null,updated_at:"2026-09-22T00:00:00Z"});
const workspace=(id:number,project_id:number):Workspace=>({id,project_id,project_code:`P-${project_id}`,project_name:`Project ${project_id}`,discipline:"electrical",display_name:`Workspace ${id}`,description:null,status:"active",version:1,updated_at:"2026-09-22T00:00:00Z",allowed_actions:[]});
describe("PATCH-057 product context",()=>{
 it("never selects first visible Project implicitly",()=>expect(validateContext({projectId:null,workspaceId:null},[project(1),project(2)],[workspace(9,1)])).toEqual({projectId:null,workspaceId:null}));
 it("clears child context when Human changes Project",()=>expect(selectProject({projectId:1,workspaceId:9},2)).toEqual({projectId:2,workspaceId:null}));
 it("accepts only Workspace belonging to selected Project",()=>{expect(selectWorkspace({projectId:1,workspaceId:null},workspace(9,1)).workspaceId).toBe(9);expect(selectWorkspace({projectId:2,workspaceId:null},workspace(9,1)).workspaceId).toBeNull()});
 it("drops stale Project and Workspace selections",()=>{expect(validateContext({projectId:3,workspaceId:9},[project(1)],[])).toEqual({projectId:null,workspaceId:null});expect(validateContext({projectId:1,workspaceId:9},[project(1)],[])).toEqual({projectId:1,workspaceId:null})});
});
describe("PATCH-057 population completeness",()=>{
 it("does not manufacture totals for unavailable reads",()=>{expect(populationFromPage(null)).toEqual({items:[],completeness:"indeterminate",returnedCount:0,hasContinuation:false});expect(populationFromPage({state:"unavailable"})).toEqual({items:[],completeness:"unavailable",returnedCount:0,hasContinuation:false})});
 it("distinguishes partial from complete authorized population",()=>{expect(populationFromPage({state:"success",data:{items:[1,2],total:5,page:1,size:2}})).toMatchObject({completeness:"partial",returnedCount:2,authorizedTotal:5,hasContinuation:true});expect(populationFromPage({state:"success",data:{items:[1],total:1,page:1,size:20}})).toMatchObject({completeness:"complete",authorizedTotal:1,hasContinuation:false})});
});

import {projectOptions,workspaceOptions} from "../productExperience/context";
describe("PATCH-057 Human-readable selectors",()=>{
 it("derives labels from authorized Project records without asking for raw ids",()=>expect(projectOptions([project(7)])[0]).toEqual({value:"7",label:"P-7 — Project 7",description:"Customer 7"}));
 it("limits Workspace options to the explicitly selected Project",()=>expect(workspaceOptions([workspace(9,1),workspace(10,2)],1).map(item=>item.value)).toEqual(["9"]));
});
