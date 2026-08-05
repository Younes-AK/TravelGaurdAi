from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from travelguard_ai.models import CustomerProfile, Transaction


class DecisionRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction": {
                    "transaction_id": "tx-2026-0001",
                    "amount": 725.5,
                    "currency": "USD",
                    "merchant_country": "MA",
                    "timestamp": "2026-08-05T12:30:00Z",
                    "device_id": "device-123",
                    "ip_address": "203.0.113.10",
                },
                "customer_profile": {
                    "customer_id": "cust-001",
                    "home_country": "US",
                    "trusted_devices": ["device-123"],
                    "last_sim_swap_days": 180,
                    "travel_frequency": 4,
                    "avg_transaction_amount": 110.0,
                    "phone_number": "+15555550123",
                },
                "signals": {
                    "location": {
                        "provider": "bank-cache",
                        "confidence": 0.92,
                        "country": "MA",
                        "verified": True,
                    }
                },
            }
        }
    )

    transaction: Transaction
    customer_profile: CustomerProfile
    signals: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional pre-collected CAMARA or bank signals keyed by signal name.",
    )


class DecisionResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decision": "STEP_UP",
                "risk_score": 0.4123,
                "confidence": 0.88,
                "explanation": [
                    "medium_risk_score",
                    "feature:amount_ratio_to_average:6.595",
                    "feature:trusted_device:1.000",
                ],
                "signals_used": ["location", "roaming", "device_location", "sim_swap"],
                "camara_calls": ["roaming", "device_location", "sim_swap"],
                "network_signals": {
                    "roaming": {"provider": "mock", "confidence": 0.94, "roaming": True},
                    "sim_swap": {"provider": "mock", "confidence": 0.99, "days_since_swap": 180},
                },
                "latency_ms": 42.7,
                "request_id": "8b44c8c0b8a64a5cab4e5ccf5a3bc99e",
            }
        }
    )

    decision: str
    risk_score: float
    confidence: float
    explanation: List[str]
    signals_used: List[str]
    camara_calls: List[str]
    network_signals: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: float
    request_id: str


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    provider: str
    model: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: Optional[str] = None
