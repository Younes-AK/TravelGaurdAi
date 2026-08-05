from __future__ import annotations

import os

from .mock_provider import MockCamaraProvider
from .nokia_provider import NokiaNetworkAsCodeConfig, NokiaNetworkAsCodeProvider
from .provider_interface import CamaraProvider


def build_camara_provider() -> CamaraProvider:
    provider_name = os.getenv("CAMARA_PROVIDER", "mock").strip().lower()
    if provider_name == "mock":
        return MockCamaraProvider()
    if provider_name == "nokia":
        return NokiaNetworkAsCodeProvider(
            config=NokiaNetworkAsCodeConfig(
                base_url=os.getenv("NAC_BASE_URL", "network-as-code.nokia.rapidapi.com"),
                client_id=os.getenv("NAC_CLIENT_ID", ""),
                client_secret=os.getenv("NAC_CLIENT_SECRET", ""),
                token_url=os.getenv("NAC_TOKEN_URL", ""),
                timeout_seconds=float(os.getenv("NAC_TIMEOUT_SECONDS", "5.0")),
                max_retries=int(os.getenv("NAC_MAX_RETRIES", "2")),
            )
        )
    raise ValueError("CAMARA_PROVIDER must be either 'mock' or 'nokia'")
