from __future__ import annotations

from typing import Optional

from .exceptions import CamaraProviderUnavailableError
from .models import (
    DeviceLocationSignal,
    DeviceSwapSignal,
    LocationSignal,
    NumberVerificationSignal,
    RoamingSignal,
    SimSwapSignal,
)
from .provider_interface import CamaraProvider


class OpenGatewayCamaraProvider(CamaraProvider):
    """Stub for future GSMA Open Gateway / Nokia Network-as-Code integration."""

    def __init__(self, *, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    async def get_location(
        self,
        *,
        ip_address: str,
        device_id: Optional[str],
        customer_country: str,
        phone_number: Optional[str] = None,
    ) -> LocationSignal:
        raise CamaraProviderUnavailableError("Open Gateway provider not implemented yet")

    async def get_roaming(self, *, ip_address: str, customer_country: str, phone_number: Optional[str] = None) -> RoamingSignal:
        raise CamaraProviderUnavailableError("Open Gateway provider not implemented yet")

    async def get_sim_swap(self, *, customer_id: str, phone_number: Optional[str] = None) -> SimSwapSignal:
        raise CamaraProviderUnavailableError("Open Gateway provider not implemented yet")

    async def get_device_swap(self, *, customer_id: str, phone_number: Optional[str] = None) -> DeviceSwapSignal:
        raise CamaraProviderUnavailableError("Open Gateway provider not implemented yet")

    async def get_device_location(
        self,
        *,
        device_id: str,
        customer_country: str,
        phone_number: Optional[str] = None,
    ) -> DeviceLocationSignal:
        raise CamaraProviderUnavailableError("Open Gateway provider not implemented yet")

    async def get_number_verification(self, *, phone_number: str) -> NumberVerificationSignal:
        raise CamaraProviderUnavailableError("Open Gateway provider not implemented yet")
