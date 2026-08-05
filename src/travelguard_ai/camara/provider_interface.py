from __future__ import annotations

from typing import Optional, Protocol

from .models import (
    DeviceLocationSignal,
    DeviceSwapSignal,
    LocationSignal,
    NumberVerificationSignal,
    RoamingSignal,
    SimSwapSignal,
)


class CamaraProvider(Protocol):
    async def get_location(
        self,
        *,
        ip_address: str,
        device_id: Optional[str],
        customer_country: str,
        phone_number: Optional[str] = None,
    ) -> LocationSignal:
        ...

    async def get_roaming(self, *, ip_address: str, customer_country: str, phone_number: Optional[str] = None) -> RoamingSignal:
        ...

    async def get_sim_swap(self, *, customer_id: str, phone_number: Optional[str] = None) -> SimSwapSignal:
        ...

    async def get_device_swap(self, *, customer_id: str, phone_number: Optional[str] = None) -> DeviceSwapSignal:
        ...

    async def get_device_location(
        self,
        *,
        device_id: str,
        customer_country: str,
        phone_number: Optional[str] = None,
    ) -> DeviceLocationSignal:
        ...

    async def get_number_verification(self, *, phone_number: str) -> NumberVerificationSignal:
        ...
