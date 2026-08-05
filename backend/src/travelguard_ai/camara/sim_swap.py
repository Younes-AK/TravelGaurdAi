from __future__ import annotations

from .base_client import CamaraClient
from .models import SimSwapSignal


async def get_sim_swap_status(client: CamaraClient, *, customer_id: str) -> SimSwapSignal:
    return await client.get_sim_swap(customer_id=customer_id)
