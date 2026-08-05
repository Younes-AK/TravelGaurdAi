from __future__ import annotations

from typing import Optional

from .base_client import CamaraClient
from .models import LocationSignal


async def get_location_verification(
    client: CamaraClient,
    *,
    ip_address: str,
    device_id: Optional[str],
    customer_country: str,
) -> LocationSignal:
    return await client.get_location(
        ip_address=ip_address,
        device_id=device_id,
        customer_country=customer_country,
    )
