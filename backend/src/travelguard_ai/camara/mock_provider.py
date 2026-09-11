from __future__ import annotations

import asyncio
import random
from typing import Dict, Optional
from zlib import crc32

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
        self._base_seed = seed
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

    def _seeded_random(self, *parts: Optional[str]) -> random.Random:
        """Deterministic per-identity RNG so repeated calls for the same customer
        return stable signals instead of re-rolling every request. Derived only
        from the provider's fixed construction seed plus the call's identity, so
        it never drifts as other, unrelated calls advance shared RNG state."""
        key = "|".join(part or "" for part in parts)
        local_seed = crc32(key.encode("utf-8")) ^ (self._base_seed * 2_654_435_761)
        return random.Random(local_seed & 0xFFFFFFFF)

    async def get_location(
        self,
        *,
        ip_address: str,
        device_id: Optional[str],
        customer_country: str,
        phone_number: Optional[str] = None,
        home_country: Optional[str] = None,
    ) -> LocationSignal:
        rng = self._seeded_random("location", phone_number, device_id, customer_country)
        payload = self.overrides.get(
            "location",
            {
                "provider": "mock",
                "confidence": round(0.85 + rng.random() * 0.14, 2),
                # The network confirms the device is where the transaction claims to be.
                "country": customer_country,
                "verified": True,
                "accuracy": "country",
            },
        )
        result = await self._with_timeout(self._delayed(payload))
        try:
            return LocationSignal(**result)
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid location response") from exc

    async def get_roaming(
        self,
        *,
        ip_address: str,
        customer_country: str,
        phone_number: Optional[str] = None,
        home_country: Optional[str] = None,
    ) -> RoamingSignal:
        rng = self._seeded_random("roaming", phone_number, customer_country)
        is_roaming = bool(home_country) and customer_country != home_country
        payload = self.overrides.get(
            "roaming",
            {
                "provider": "mock",
                "confidence": round(0.82 + rng.random() * 0.17, 2),
                "country": customer_country,
                "roaming": is_roaming,
            },
        )
        result = await self._with_timeout(self._delayed(payload))
        try:
            return RoamingSignal(**result)
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid roaming response") from exc

    async def get_sim_swap(
        self,
        *,
        customer_id: str,
        phone_number: Optional[str] = None,
        known_sim_age_days: Optional[int] = None,
    ) -> SimSwapSignal:
        rng = self._seeded_random("sim_swap", customer_id, phone_number)
        if known_sim_age_days is not None:
            # The bank's declared SIM age is what this demo/test scenario is
            # simulating as network ground truth; jitter it slightly for realism.
            days_since_swap = max(0, known_sim_age_days + rng.randint(-1, 1))
        else:
            days_since_swap = rng.randint(0, 500)
        payload = self.overrides.get(
            "sim_swap",
            {
                "provider": "mock",
                "confidence": 0.99,
                "days_since_swap": days_since_swap,
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
                # False by default; demo scenarios that need a takeover pattern
                # supply this signal explicitly via overrides/request signals
                # rather than relying on random chance (which would make the
                # demo occasionally, unpredictably reject a legitimate case).
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
        trusted_device: Optional[bool] = None,
    ) -> DeviceLocationSignal:
        rng = self._seeded_random("device_location", device_id, phone_number, customer_country)
        if trusted_device is False:
            confidence = round(0.4 + rng.random() * 0.2, 2)
            verified = False
            distance_km = round(50.0 + rng.random() * 400.0, 2)
        elif trusted_device is True:
            confidence = round(0.9 + rng.random() * 0.09, 2)
            verified = True
            distance_km = round(rng.random() * 15.0, 2)
        else:
            confidence = round(0.80 + rng.random() * 0.18, 2)
            verified = True
            distance_km = round(rng.random() * 40.0, 2)
        payload = self.overrides.get(
            "device_location",
            {
                "provider": "mock",
                "confidence": confidence,
                "device_id": device_id,
                "country": customer_country,
                "verified": verified,
                "distance_km": distance_km,
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
