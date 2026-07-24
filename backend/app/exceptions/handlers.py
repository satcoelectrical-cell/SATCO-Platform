from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .base import SatcoException


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(SatcoException)
    async def satco_exception_handler(request, exc: SatcoException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                },
            },
        )
