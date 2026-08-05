from __future__ import annotations

from .base_client import CamaraClient
from .models import RoamingSignal


async def get_roaming_status(client: CamaraClient, *, ip_address: str, customer_country: str) -> RoamingSignal:
    return await client.get_roaming(ip_address=ip_address, customer_country=customer_country)
