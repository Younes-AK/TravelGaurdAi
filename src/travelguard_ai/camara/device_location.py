from __future__ import annotations

from .base_client import CamaraClient
from .models import DeviceLocationSignal


async def get_device_location_verification(
    client: CamaraClient,
    *,
    device_id: str,
    customer_country: str,
) -> DeviceLocationSignal:
    return await client.get_device_location(device_id=device_id, customer_country=customer_country)
