from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from .exceptions import CamaraInvalidResponseError, CamaraNetworkError, CamaraProviderUnavailableError, CamaraTimeoutError
from .models import (
    DeviceLocationSignal,
    DeviceSwapSignal,
    LocationSignal,
    NumberVerificationSignal,
    RoamingSignal,
    SimSwapSignal,
)
from .provider_interface import CamaraProvider


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NokiaNetworkAsCodeConfig:
    base_url: str
    client_id: str
    client_secret: str
    token_url: str
    timeout_seconds: float = 5.0
    max_retries: int = 2
    sim_swap_max_age_hours: int = 240
    device_swap_max_age_hours: int = 240
    location_max_age_seconds: int = 3600

    @property
    def rapidapi_host(self) -> str:
        parsed = urlparse(self.base_url)
        return parsed.netloc or parsed.path


class NokiaNetworkAsCodeProvider(CamaraProvider):
    """CAMARA provider backed by Nokia Network as Code's official Python SDK.

    The public Nokia docs show SDK-level methods rather than stable REST paths for
    these capabilities, so this adapter deliberately calls the SDK surface instead
    of inventing endpoints.
    """

    provider_name = "nokia-network-as-code"

    def __init__(
        self,
        *,
        config: NokiaNetworkAsCodeConfig,
        sdk_client: Optional[Any] = None,
        number_verifier: Optional[Callable[..., Any]] = None,
    ):
        self.config = config
        self._sdk_client = sdk_client
        self._number_verifier = number_verifier

    @property
    def sdk_client(self) -> Any:
        if self._sdk_client is None:
            if not self.config.client_secret:
                raise CamaraProviderUnavailableError("NAC_CLIENT_SECRET must contain the Nokia application API key")
            try:
                from network_as_code import NetworkAsCodeApi
            except ImportError as exc:
                raise CamaraProviderUnavailableError(
                    "Install the official Nokia SDK with `pip install network_as_code` before using CAMARA_PROVIDER=nokia"
                ) from exc

            self._sdk_client = NetworkAsCodeApi(
                rapidapi_host=self.config.rapidapi_host,
                api_key=self.config.client_secret,
            )
        return self._sdk_client

    async def _call_sdk(self, api_name: str, func: Callable[[], Any]) -> tuple[Any, float]:
        attempts = self.config.max_retries + 1
        last_exc: Optional[BaseException] = None

        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            try:
                result = await asyncio.wait_for(asyncio.to_thread(func), timeout=self.config.timeout_seconds)
                latency_ms = (time.perf_counter() - started) * 1000.0
                logger.info(
                    "camara_api_success",
                    extra={"api": api_name, "latency_ms": round(latency_ms, 2), "attempt": attempt},
                )
                return result, latency_ms
            except asyncio.TimeoutError as exc:
                last_exc = exc
                logger.warning("camara_api_timeout", extra={"api": api_name, "attempt": attempt})
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "camara_api_failure",
                    extra={"api": api_name, "attempt": attempt, "error": exc.__class__.__name__},
                )

            if attempt < attempts:
                await asyncio.sleep(min(0.05 * attempt, 0.2))

        if isinstance(last_exc, asyncio.TimeoutError):
            raise CamaraTimeoutError(f"{api_name} timed out") from last_exc
        raise CamaraNetworkError(f"{api_name} failed after {attempts} attempts") from last_exc

    @staticmethod
    def _attr(payload: Any, name: str, default: Any = None) -> Any:
        if isinstance(payload, dict):
            return payload.get(name, default)
        return getattr(payload, name, default)

    @classmethod
    def _raw(cls, payload: Any) -> dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "model_dump"):
            return payload.model_dump(mode="json")
        public = {
            key: value
            for key, value in vars(payload).items()
            if not key.startswith("_") and isinstance(value, (str, int, float, bool, list, dict, type(None)))
        }
        return public

    @staticmethod
    def _require_phone(phone_number: Optional[str], api_name: str) -> str:
        if not phone_number:
            raise CamaraProviderUnavailableError(f"{api_name} requires an E.164 phone number")
        return phone_number

    async def get_location(
        self,
        *,
        ip_address: str,
        device_id: Optional[str],
        customer_country: str,
        phone_number: Optional[str] = None,
        home_country: Optional[str] = None,
    ) -> LocationSignal:
        phone = self._require_phone(phone_number, "location_verification")

        def call() -> Any:
            return self.sdk_client.location.verify_v1(
                device={"phone_number": phone},
                # TODO(Nokia sandbox): replace this minimal official example area
                # with a merchant-country geofence configured from bank data.
                area={"area_type": "CIRCLE"},
                max_age=self.config.location_max_age_seconds,
            )

        result, latency_ms = await self._call_sdk("location_verification", call)
        verification_result = str(self._attr(result, "verification_result", "UNKNOWN")).upper()
        match_rate = self._attr(result, "match_rate")
        confidence = 0.3
        if verification_result == "TRUE":
            confidence = 0.96
        elif verification_result == "FALSE":
            confidence = 0.92
        elif verification_result == "PARTIAL":
            confidence = max(0.5, min(0.9, float(match_rate or 70) / 100.0))

        try:
            return LocationSignal(
                provider=self.provider_name,
                confidence=confidence,
                country=customer_country,
                verified=verification_result in {"TRUE", "PARTIAL"},
                accuracy="region" if verification_result == "PARTIAL" else "country",
                api_latency_ms=round(latency_ms, 2),
                raw_response=self._raw(result),
            )
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid Nokia location verification response") from exc

    async def get_roaming(
        self,
        *,
        ip_address: str,
        customer_country: str,
        phone_number: Optional[str] = None,
        home_country: Optional[str] = None,
    ) -> RoamingSignal:
        phone = self._require_phone(phone_number, "device_roaming_status")

        def call() -> Any:
            return self.sdk_client.device_status.retrieve_roaming_status(device={"phone_number": phone})

        result, latency_ms = await self._call_sdk("device_roaming_status", call)
        roaming = bool(self._attr(result, "roaming", False))
        country_names = self._attr(result, "countryName", None) or self._attr(result, "country_name", None) or []
        country = country_names[0] if roaming and country_names else customer_country

        try:
            return RoamingSignal(
                provider=self.provider_name,
                confidence=0.94,
                country=country,
                roaming=roaming,
                api_latency_ms=round(latency_ms, 2),
                raw_response=self._raw(result),
            )
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid Nokia roaming response") from exc

    async def get_sim_swap(
        self,
        *,
        customer_id: str,
        phone_number: Optional[str] = None,
        known_sim_age_days: Optional[int] = None,
    ) -> SimSwapSignal:
        phone = self._require_phone(phone_number, "sim_swap")

        def call() -> Any:
            return self.sdk_client.sim_swap.check(phone_number=phone, max_age=self.config.sim_swap_max_age_hours)

        result, latency_ms = await self._call_sdk("sim_swap", call)
        swapped = bool(self._attr(result, "swapped", False))
        latest_change = self._attr(result, "latest_sim_change")
        days_since_swap = 0 if swapped else 9999
        if latest_change:
            if isinstance(latest_change, str):
                latest_change = datetime.fromisoformat(latest_change.replace("Z", "+00:00"))
            days_since_swap = max(0, (datetime.now(UTC) - latest_change).days)

        try:
            return SimSwapSignal(
                provider=self.provider_name,
                confidence=0.95,
                days_since_swap=days_since_swap,
                api_latency_ms=round(latency_ms, 2),
                raw_response=self._raw(result),
            )
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid Nokia SIM swap response") from exc

    async def get_device_swap(self, *, customer_id: str, phone_number: Optional[str] = None) -> DeviceSwapSignal:
        phone = self._require_phone(phone_number, "device_swap")

        def call() -> Any:
            return self.sdk_client.device_swap.check(phone_number=phone, max_age=self.config.device_swap_max_age_hours)

        result, latency_ms = await self._call_sdk("device_swap", call)
        try:
            return DeviceSwapSignal(
                provider=self.provider_name,
                confidence=0.95,
                swapped=bool(self._attr(result, "swapped", False)),
                api_latency_ms=round(latency_ms, 2),
                raw_response=self._raw(result),
            )
        except Exception as exc:
            raise CamaraInvalidResponseError("Invalid Nokia device swap response") from exc

    async def get_device_location(
        self,
        *,
        device_id: str,
        customer_country: str,
        phone_number: Optional[str] = None,
        trusted_device: Optional[bool] = None,
    ) -> DeviceLocationSignal:
        location = await self.get_location(
            ip_address="",
            device_id=device_id,
            customer_country=customer_country,
            phone_number=phone_number,
        )
        return DeviceLocationSignal(
            provider=self.provider_name,
            confidence=location.confidence,
            device_id=device_id,
            country=location.country,
            verified=location.verified,
            distance_km=0.0 if location.verified else 9999.0,
            api_latency_ms=location.api_latency_ms,
            raw_response=location.raw_response,
        )

    async def get_number_verification(self, *, phone_number: str) -> NumberVerificationSignal:
        if self._number_verifier is None:
            raise CamaraProviderUnavailableError(
                "Number Verification requires Nokia's 3-legged OAuth consent flow; "
                "TODO: exchange the user authorization code via NAC_TOKEN_URL and inject a consent-aware verifier"
            )

        def call() -> Any:
            return self._number_verifier(
                phone_number=phone_number,
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                token_url=self.config.token_url,
            )

        result, latency_ms = await self._call_sdk("number_verification", call)
        verified = bool(self._attr(result, "verified", self._attr(result, "device_phone_number_verified", False)))
        return NumberVerificationSignal(
            provider=self.provider_name,
            confidence=0.96 if verified else 0.75,
            phone_number=phone_number,
            verified=verified,
            api_latency_ms=round(latency_ms, 2),
            raw_response=self._raw(result),
        )
