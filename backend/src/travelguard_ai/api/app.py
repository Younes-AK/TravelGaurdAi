from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from travelguard_ai.api.dependencies import ServiceUnavailableError, create_travelguard_services
from travelguard_ai.api.middleware import RequestLoggingMiddleware
from travelguard_ai.api.routes import router


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.services = create_travelguard_services()
    yield


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def create_app() -> FastAPI:
    app = FastAPI(
        title="TravelGuard AI Decision Service",
        version="0.1.0",
        description="Demo-ready API layer for bank transaction risk decisions.",
        lifespan=lifespan,
    )
    allowed_origins = [
        origin.strip()
        for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "*").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(router)

    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": exc.code,
                "message": exc.message,
                "request_id": _request_id(request),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request body failed schema validation",
                "details": jsonable_encoder(exc.errors()),
                "request_id": _request_id(request),
            },
        )

    return app


app = create_app()
