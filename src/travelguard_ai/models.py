from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import math


class Transaction(BaseModel):
    transaction_id: str
    amount: float
    currency: str
    merchant_country: str
    merchant_name: Optional[str] = None
    timestamp: datetime
    device_id: Optional[str] = None
    ip_address: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if not isinstance(value, (int, float)):
            raise TypeError("amount must be numeric")
        if not math.isfinite(value):
            raise ValueError("amount must be finite")
        if value <= 0:
            raise ValueError("amount must be positive")
        return float(value)


class CustomerProfile(BaseModel):
    customer_id: str
    home_country: str
    trusted_devices: List[str] = Field(default_factory=list)
    last_sim_swap_days: Optional[int] = None
    travel_frequency: Optional[int] = 0
    avg_transaction_amount: Optional[float] = 0.0
    phone_number: Optional[str] = None

    @field_validator("travel_frequency")
    @classmethod
    def validate_travel_frequency(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value < 0:
            raise ValueError("travel_frequency must be non-negative")
        return value

    @field_validator("avg_transaction_amount")
    @classmethod
    def validate_avg_transaction_amount(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if not math.isfinite(value):
            raise ValueError("avg_transaction_amount must be finite")
        if value < 0:
            raise ValueError("avg_transaction_amount must be non-negative")
        return float(value)


class Signals(BaseModel):
    # Generic container for CAMARA signals
    raw: Dict[str, Any] = Field(default_factory=dict)


class RiskFeatureVector(BaseModel):
    features: Dict[str, float]

    @field_validator("features")
    @classmethod
    def validate_features(cls, value: Dict[str, float]) -> Dict[str, float]:
        if not value:
            raise ValueError("features must not be empty")
        for name, item in value.items():
            if not isinstance(item, (int, float)):
                raise TypeError(f"feature '{name}' must be numeric")
            if not math.isfinite(item):
                raise ValueError(f"feature '{name}' must be finite")
        return {key: float(val) for key, val in value.items()}


class RiskAssessment(BaseModel):
    risk_score: float
    fraud_probability: float
    confidence: float

    @field_validator("risk_score", "fraud_probability", "confidence")
    @classmethod
    def validate_unit_interval(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("assessment values must be finite")
        if value < 0.0 or value > 1.0:
            raise ValueError("assessment values must be within [0, 1]")
        return float(value)


class DecisionResult(BaseModel):
    decision: str
    risk_score: float
    confidence: float
    reasoning: List[str]
    signals_used: List[str]
    camara_calls: List[str]
