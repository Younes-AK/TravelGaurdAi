from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Request


class ServiceUnavailableError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class TravelGuardServices:
    decision_agent: Optional[Any] = None
    risk_engine: Optional[Any] = None
    feature_builder: Optional[Any] = None
    camara_provider: Optional[Any] = None
    startup_error: Optional[Exception] = None
    startup_error_code: Optional[str] = None

    @property
    def ready(self) -> bool:
        return self.startup_error is None and self.decision_agent is not None


def create_travelguard_services() -> TravelGuardServices:
    try:
        from travelguard_ai.camara import build_camara_provider
        from travelguard_ai.decision_agent import DecisionAgent
        from travelguard_ai.risk_engine import RiskEngine

        camara_provider = build_camara_provider()
        risk_engine = RiskEngine()
        decision_agent = DecisionAgent(
            camara_provider=camara_provider,
            risk_engine=risk_engine,
        )

        return TravelGuardServices(
            decision_agent=decision_agent,
            risk_engine=risk_engine,
            feature_builder=decision_agent.fb,
            camara_provider=camara_provider,
        )
    except Exception as exc:
        return TravelGuardServices(
            startup_error=exc,
            startup_error_code="MODEL_UNAVAILABLE",
        )


def get_services(request: Request) -> TravelGuardServices:
    services = getattr(request.app.state, "services", None)
    if services is None:
        raise ServiceUnavailableError("SERVICE_UNAVAILABLE", "TravelGuard AI services are not initialized")
    if not services.ready:
        code = services.startup_error_code or "SERVICE_UNAVAILABLE"
        message = "TravelGuard AI model is unavailable" if code == "MODEL_UNAVAILABLE" else "TravelGuard AI is unavailable"
        raise ServiceUnavailableError(code, message)
    return services
