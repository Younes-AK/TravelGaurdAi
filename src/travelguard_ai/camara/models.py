from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class CamaraSignalBase(BaseModel):
    signal_name: str
    provider: str
    confidence: float = Field(ge=0.0, le=1.0)
    api_latency_ms: Optional[float] = Field(default=None, ge=0.0)
    raw_response: Optional[Dict[str, Any]] = None


class LocationSignal(CamaraSignalBase):
    signal_name: Literal["location"] = "location"
    country: str
    verified: bool
    accuracy: Literal["country", "region", "city", "gps"] = "country"


class RoamingSignal(CamaraSignalBase):
    signal_name: Literal["roaming"] = "roaming"
    country: str
    roaming: bool


class SimSwapSignal(CamaraSignalBase):
    signal_name: Literal["sim_swap"] = "sim_swap"
    days_since_swap: int = Field(ge=0)


class DeviceSwapSignal(CamaraSignalBase):
    signal_name: Literal["device_swap"] = "device_swap"
    swapped: bool


class DeviceLocationSignal(CamaraSignalBase):
    signal_name: Literal["device_location"] = "device_location"
    device_id: str
    country: str
    verified: bool
    distance_km: float = Field(ge=0.0)


class NumberVerificationSignal(CamaraSignalBase):
    signal_name: Literal["number_verification"] = "number_verification"
    phone_number: str
    verified: bool

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or not normalized.startswith("+"):
            raise ValueError("phone_number must be in E.164 format")
        return normalized


class CamaraSignalsBundle(BaseModel):
    location: Optional[LocationSignal] = None
    roaming: Optional[RoamingSignal] = None
    sim_swap: Optional[SimSwapSignal] = None
    device_swap: Optional[DeviceSwapSignal] = None
    device_location: Optional[DeviceLocationSignal] = None
    number_verification: Optional[NumberVerificationSignal] = None
