from __future__ import annotations

from .base_client import CamaraClient
from .models import NumberVerificationSignal


async def get_number_verification(client: CamaraClient, *, phone_number: str) -> NumberVerificationSignal:
    return await client.get_number_verification(phone_number=phone_number)
