"""Thin authenticated PATCH-048 Project Context transport."""
from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError
from app.dependencies.project_context import ProjectContextApplication, get_project_context_application
from uuid import UUID
from app.schemas.project_context import (
    ContextNodeKind, ContextNodeResult, ContextNodeSelector, ContextRelationshipKind,
    EngineeringRelationshipDiscriminator, ExpandOneHopRequest,
    GetContextNodeRequest, GraphDirection, OneHopResult, ProjectContextInvalidRequest,
    ProjectContextRequest, ProjectContextResult, ProjectContextScope,
    ProjectContextSectionKind, ProjectContextSectionRequest,
)
router=APIRouter(tags=["Project Context"])
@router.get("/projects/{project_id}/context",response_model=ProjectContextResult)
def assemble_project_context(project_id:int, workspace_id:int|None=None, section:ProjectContextSectionKind|None=None, page_size:int=100, continuation:str|None=None, application:ProjectContextApplication=Depends(get_project_context_application)):
    try:
        sections=() if section is None else (ProjectContextSectionRequest(kind=section,page_size=page_size,continuation=continuation),)
        if section is None and continuation is not None: raise ValueError("section continuation requires section")
        request=ProjectContextRequest(scope=ProjectContextScope(project_id=project_id,workspace_id=workspace_id),sections=sections)
    except ValidationError: return ProjectContextInvalidRequest()
    return application.service.assemble_project_context(actor=application.actor,request=request,current_user=application.current_user)


def _selector(node_kind: str, selector: str) -> ContextNodeSelector:
    kind=ContextNodeKind(node_kind)
    value=int(selector) if kind in {ContextNodeKind.PROJECT,ContextNodeKind.WORKSPACE,ContextNodeKind.ENGINEERING_CONTEXT} else UUID(selector)
    return ContextNodeSelector(kind=kind,value=value)


def _relationship_kind(value: str):
    if value.startswith("engineering:"):
        _, family, relationship_type = value.split(":", 2)
        return EngineeringRelationshipDiscriminator(
            family=family, relationship_type=relationship_type
        )
    return ContextRelationshipKind(value)


@router.get("/projects/{project_id}/engineering-context/nodes/{node_kind}/{selector}",response_model=ContextNodeResult)
def get_context_node(project_id:int,node_kind:str,selector:str,workspace_id:int|None=None,application:ProjectContextApplication=Depends(get_project_context_application)):
    try: request=GetContextNodeRequest(scope=ProjectContextScope(project_id=project_id,workspace_id=workspace_id),selector=_selector(node_kind,selector))
    except (ValidationError,ValueError): return ProjectContextInvalidRequest()
    return application.service.get_context_node(actor=application.actor,request=request,current_user=application.current_user)


@router.get("/projects/{project_id}/engineering-context/nodes/{node_kind}/{selector}/related",response_model=OneHopResult)
def expand_one_hop(project_id:int,node_kind:str,selector:str,workspace_id:int|None=None,relationship_kind:list[str]=Query(default=[]),direction:GraphDirection=GraphDirection.BOTH,page_size:int=91,continuation:str|None=None,application:ProjectContextApplication=Depends(get_project_context_application)):
    try: request=ExpandOneHopRequest(scope=ProjectContextScope(project_id=project_id,workspace_id=workspace_id),start=_selector(node_kind,selector),relationship_kinds=tuple(_relationship_kind(value) for value in relationship_kind),direction=direction,page_size=page_size,continuation=continuation)
    except (ValidationError,ValueError): return ProjectContextInvalidRequest()
    return application.service.expand_one_hop(actor=application.actor,request=request,current_user=application.current_user)
