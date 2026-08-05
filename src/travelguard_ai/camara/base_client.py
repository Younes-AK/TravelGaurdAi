from __future__ import annotations

from typing import Optional

from .models import (
    DeviceLocationSignal,
    DeviceSwapSignal,
    LocationSignal,
    NumberVerificationSignal,
    RoamingSignal,
    SimSwapSignal,
)
from .provider_interface import CamaraProvider


class CamaraClient:
    """High-level async CAMARA client delegating to an injected provider."""

    def __init__(self, provider: CamaraProvider):
        self.provider = provider

    async def get_location(
        self,
        *,
        ip_address: str,
        device_id: Optional[str],
        customer_country: str,
        phone_number: Optional[str] = None,
    ) -> LocationSignal:
        return await self.provider.get_location(
            ip_address=ip_address,
            device_id=device_id,
            customer_country=customer_country,
            phone_number=phone_number,
        )

    async def get_roaming(self, *, ip_address: str, customer_country: str, phone_number: Optional[str] = None) -> RoamingSignal:
        return await self.provider.get_roaming(
            ip_address=ip_address,
            customer_country=customer_country,
            phone_number=phone_number,
        )

    async def get_sim_swap(self, *, customer_id: str, phone_number: Optional[str] = None) -> SimSwapSignal:
        return await self.provider.get_sim_swap(customer_id=customer_id, phone_number=phone_number)

    async def get_device_swap(self, *, customer_id: str, phone_number: Optional[str] = None) -> DeviceSwapSignal:
        return await self.provider.get_device_swap(customer_id=customer_id, phone_number=phone_number)

    async def get_device_location(
        self,
        *,
        device_id: str,
        customer_country: str,
        phone_number: Optional[str] = None,
    ) -> DeviceLocationSignal:
        return await self.provider.get_device_location(
            device_id=device_id,
            customer_country=customer_country,
            phone_number=phone_number,
        )

    async def get_number_verification(self, *, phone_number: str) -> NumberVerificationSignal:
        return await self.provider.get_number_verification(phone_number=phone_number)
