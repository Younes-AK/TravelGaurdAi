from __future__ import annotations

import asyncio
import random
from typing import Dict, Optional

from .exceptions import CamaraInvalidResponseError, CamaraTimeoutError
from .models import (
    DeviceLocationSignal,
    DeviceSwapSignal,
    LocationSignal,
    NumberVerificationSignal,
    RoamingSignal,
    SimSwapSignal,
)
from .provider_interface import CamaraProvider


class MockCamaraProvider(CamaraProvider):
    """Deterministic-friendly mock provider for CAMARA signal simulation."""

    def __init__(
        self,
        *,
        seed: int = 42,
        timeout_seconds: float = 1.0,
        artificial_delay_seconds: float = 0.01,
        overrides: Optional[Dict[str, dict]] = None,
    ):
        self._rng = random.Random(seed)
        self.timeout_seconds = timeout_seconds
        self.artificial_delay_seconds = artificial_delay_seconds
        self.overrides = overrides or {}

    async def _with_timeout(self, coro):
        try:
            return await asyncio.wait_for(coro, timeout=self.timeout_seconds)
        except asyncio.TimeoutError as exc:
            raise CamaraTimeoutError("CAMARA request timed out") from exc

    async def _delayed(self, payload: dict) -> dict:
        await asyncio.sleep(self.artificial_delay_seconds)
        return payload

    async def get_location(
        self,
        *,
        ip_address: str,
        device_id: Optional[str],
        customer_country: str,
        phone_number: Optional[str] = None,
    ) -> LocationSignal:
        payload = self.overrides.get(
            "location",
            {
                "provider": "mock",
                "confidence": round(0.85 + self._rng.random() * 0.14, 2),
                "country": customer_country if self._rng.random() > 0.25 else "Morocco",
                "verified": True,
                "accuracy": "country",
            },
        )
        result = await self._with_timeout(self._delayed(payload))
        try:
            return LocationSignal(**result)
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid location response") from exc

    async def get_roaming(self, *, ip_address: str, customer_country: str, phone_number: Optional[str] = None) -> RoamingSignal:
        payload = self.overrides.get(
            "roaming",
            {
                "provider": "mock",
                "confidence": round(0.82 + self._rng.random() * 0.17, 2),
                "country": "Morocco",
                "roaming": customer_country != "Morocco",
            },
        )
        result = await self._with_timeout(self._delayed(payload))
        try:
            return RoamingSignal(**result)
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid roaming response") from exc

    async def get_sim_swap(self, *, customer_id: str, phone_number: Optional[str] = None) -> SimSwapSignal:
        payload = self.overrides.get(
            "sim_swap",
            {
                "provider": "mock",
                "confidence": 0.99,
                "days_since_swap": self._rng.randint(0, 500),
            },
        )
        result = await self._with_timeout(self._delayed(payload))
        try:
            return SimSwapSignal(**result)
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid sim swap response") from exc

    async def get_device_swap(self, *, customer_id: str, phone_number: Optional[str] = None) -> DeviceSwapSignal:
        payload = self.overrides.get(
            "device_swap",
            {
                "provider": "mock",
                "confidence": 0.97,
                "swapped": False,
            },
        )
        result = await self._with_timeout(self._delayed(payload))
        try:
            return DeviceSwapSignal(**result)
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid device swap response") from exc

    async def get_device_location(
        self,
        *,
        device_id: str,
        customer_country: str,
        phone_number: Optional[str] = None,
    ) -> DeviceLocationSignal:
        payload = self.overrides.get(
            "device_location",
            {
                "provider": "mock",
                "confidence": round(0.80 + self._rng.random() * 0.18, 2),
                "device_id": device_id,
                "country": customer_country,
                "verified": True,
                "distance_km": round(self._rng.random() * 120.0, 2),
            },
        )
        result = await self._with_timeout(self._delayed(payload))
        try:
            return DeviceLocationSignal(**result)
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid device location response") from exc

    async def get_number_verification(self, *, phone_number: str) -> NumberVerificationSignal:
        payload = self.overrides.get(
            "number_verification",
            {
                "provider": "mock",
                "confidence": 0.98,
                "phone_number": phone_number,
                "verified": True,
            },
        )
        result = await self._with_timeout(self._delayed(payload))
        try:
            return NumberVerificationSignal(**result)
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid number verification response") from exc
