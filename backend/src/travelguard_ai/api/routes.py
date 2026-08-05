from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from travelguard_ai.api.dependencies import TravelGuardServices, get_services
from travelguard_ai.api.schemas import DecisionRequest, DecisionResponse, HealthResponse, ReadyResponse
from travelguard_ai.camara import CamaraProviderUnavailableError
from travelguard_ai.models import Signals


router = APIRouter()
logger = logging.getLogger(__name__)


def _serialize_signals(raw: dict[str, Any]) -> dict[str, Any]:
    serialized: dict[str, Any] = {}
    for name, value in raw.items():
        if hasattr(value, "model_dump"):
            serialized[name] = value.model_dump(mode="json", exclude_none=True)
        else:
            serialized[name] = value
    return serialized


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse, tags=["health"])
async def ready(request: Request) -> ReadyResponse:
    services = getattr(request.app.state, "services", None)
    if services is None or not services.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": getattr(services, "startup_error_code", None) or "SERVICE_UNAVAILABLE",
                "message": "TravelGuard AI is not ready",
            },
        )

    return ReadyResponse(
        status="ready",
        provider=services.camara_provider.__class__.__name__,
        model=services.risk_engine.__class__.__name__,
    )


@router.post(
    "/v1/decision",
    response_model=DecisionResponse,
    responses={
        400: {"description": "Invalid request"},
        422: {"description": "Request validation error"},
        500: {"description": "Internal inference error"},
        503: {"description": "Provider or model unavailable"},
    },
    tags=["decisions"],
)
async def create_decision(
    payload: DecisionRequest,
    request: Request,
    services: TravelGuardServices = Depends(get_services),
) -> DecisionResponse:
    agent = services.decision_agent
    validation_errors = agent.validate(payload.transaction, payload.customer_profile)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_REQUEST",
                "message": ", ".join(validation_errors),
            },
        )

    signals = Signals(raw=payload.signals or {})
    started = time.perf_counter()

    try:
        result = await agent.decide_async(payload.transaction, payload.customer_profile, signals)
    except CamaraProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "PROVIDER_UNAVAILABLE",
                "message": str(exc) or "CAMARA provider unavailable",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_REQUEST",
                "message": str(exc),
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INFERENCE_ERROR",
                "message": "TravelGuard AI inference failed",
            },
        ) from exc

    latency_ms = (time.perf_counter() - started) * 1000.0
    request.state.decision = result.decision
    logger.info(
        "decision_api_completed",
        extra={
            "latency_ms": round(latency_ms, 2),
            "risk_score": result.risk_score,
            "confidence": result.confidence,
            "camara_calls": result.camara_calls,
            "signals_used": result.signals_used,
        },
    )

    return DecisionResponse(
        decision=result.decision,
        risk_score=result.risk_score,
        confidence=result.confidence,
        explanation=result.reasoning,
        signals_used=result.signals_used,
        camara_calls=result.camara_calls,
        network_signals=_serialize_signals(signals.raw),
        latency_ms=round(latency_ms, 2),
        request_id=request.state.request_id,
    )
