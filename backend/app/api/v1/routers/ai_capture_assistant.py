"""Thin authenticated PATCH-035 transport."""

from dataclasses import asdict
from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.dependencies.ai_capture_assistant import AICaptureAssistantApplication, get_ai_capture_assistant_application
from app.ports.ai_capture_assistant import CaptureAdviceRequest, CopilotScope
from app.schemas.ai_capture_assistant import CaptureAdviceRequestSchema, CaptureAdviceResponseSchema


class AICaptureAssistantRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError:
                return JSONResponse(status_code=422, content={"outcome": "invalid_request"})

        return handler


router = APIRouter(tags=["AI Capture Assistant"], route_class=AICaptureAssistantRoute)


@router.post(
    "/engineering-copilot/capture-advice",
    response_model=CaptureAdviceResponseSchema,
)
def advise_capture(
    data: CaptureAdviceRequestSchema,
    application: AICaptureAssistantApplication = Depends(get_ai_capture_assistant_application),
):
    result = application.service.advise_capture(
        application.actor,
        CopilotScope(application.actor.organization_id, data.project_id, data.workspace_id),
        CaptureAdviceRequest(data.capture_id, data.human_instruction, data.output_kind),
    )
    return asdict(result)
