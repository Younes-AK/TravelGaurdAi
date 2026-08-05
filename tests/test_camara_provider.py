import time
from types import SimpleNamespace

import pytest

from travelguard_ai.camara import (
    CamaraClient,
    MockCamaraProvider,
    NokiaNetworkAsCodeConfig,
    NokiaNetworkAsCodeProvider,
    OpenGatewayCamaraProvider,
    build_camara_provider,
)
from travelguard_ai.camara.exceptions import CamaraInvalidResponseError, CamaraProviderUnavailableError, CamaraTimeoutError


@pytest.mark.asyncio
async def test_mock_provider_location_api():
    client = CamaraClient(provider=MockCamaraProvider(seed=1))
    signal = await client.get_location(ip_address="1.2.3.4", device_id="dev1", customer_country="US")
    assert signal.signal_name == "location"
    assert signal.country
    assert 0.0 <= signal.confidence <= 1.0


@pytest.mark.asyncio
async def test_mock_provider_roaming_api():
    client = CamaraClient(provider=MockCamaraProvider(seed=2))
    signal = await client.get_roaming(ip_address="1.2.3.4", customer_country="US")
    assert signal.signal_name == "roaming"
    assert isinstance(signal.roaming, bool)


@pytest.mark.asyncio
async def test_mock_provider_sim_swap_api():
    client = CamaraClient(provider=MockCamaraProvider(seed=3))
    signal = await client.get_sim_swap(customer_id="cust")
    assert signal.signal_name == "sim_swap"
    assert signal.days_since_swap >= 0


@pytest.mark.asyncio
async def test_mock_provider_device_location_api():
    client = CamaraClient(provider=MockCamaraProvider(seed=4))
    signal = await client.get_device_location(device_id="dev1", customer_country="US")
    assert signal.signal_name == "device_location"
    assert signal.device_id == "dev1"


@pytest.mark.asyncio
async def test_mock_provider_number_verification_api():
    client = CamaraClient(provider=MockCamaraProvider(seed=5))
    signal = await client.get_number_verification(phone_number="+212600000001")
    assert signal.signal_name == "number_verification"
    assert signal.verified is True


@pytest.mark.asyncio
async def test_mock_provider_device_swap_api():
    client = CamaraClient(provider=MockCamaraProvider(seed=6))
    signal = await client.get_device_swap(customer_id="cust", phone_number="+212600000001")
    assert signal.signal_name == "device_swap"
    assert signal.swapped is False


@pytest.mark.asyncio
async def test_provider_switching_open_gateway_stub():
    client = CamaraClient(provider=OpenGatewayCamaraProvider(base_url="https://api.example.com", api_key="k"))
    with pytest.raises(CamaraProviderUnavailableError):
        await client.get_roaming(ip_address="1.2.3.4", customer_country="US")


@pytest.mark.asyncio
async def test_timeout_handling():
    provider = MockCamaraProvider(timeout_seconds=0.001, artificial_delay_seconds=0.01)
    client = CamaraClient(provider=provider)
    with pytest.raises(CamaraTimeoutError):
        await client.get_sim_swap(customer_id="cust")


@pytest.mark.asyncio
async def test_invalid_response_handling_missing_fields():
    provider = MockCamaraProvider(overrides={"location": {"provider": "mock", "confidence": 0.9}})
    client = CamaraClient(provider=provider)
    with pytest.raises(CamaraInvalidResponseError):
        await client.get_location(ip_address="1.2.3.4", device_id="dev1", customer_country="US")


class _FakeNokiaSdk:
    def __init__(self):
        self.location = SimpleNamespace(verify_v1=self._location_verify)
        self.device_status = SimpleNamespace(retrieve_roaming_status=self._roaming_status)
        self.sim_swap = SimpleNamespace(check=self._sim_swap_check)
        self.device_swap = SimpleNamespace(check=self._device_swap_check)
        self.calls = []

    def _location_verify(self, *, device, area, max_age):
        self.calls.append(("location.verify_v1", device, area, max_age))
        return SimpleNamespace(verification_result="TRUE", match_rate=None)

    def _roaming_status(self, *, device):
        self.calls.append(("device_status.retrieve_roaming_status", device))
        return SimpleNamespace(roaming=True, countryName=["MA"])

    def _sim_swap_check(self, *, phone_number, max_age):
        self.calls.append(("sim_swap.check", phone_number, max_age))
        return SimpleNamespace(swapped=True)

    def _device_swap_check(self, *, phone_number, max_age):
        self.calls.append(("device_swap.check", phone_number, max_age))
        return SimpleNamespace(swapped=False)


def _nokia_provider(**kwargs):
    config = NokiaNetworkAsCodeConfig(
        base_url="network-as-code.nokia.rapidapi.com",
        client_id="client-id",
        client_secret="api-key",
        token_url="https://auth.example/token",
        timeout_seconds=kwargs.pop("timeout_seconds", 1.0),
        max_retries=kwargs.pop("max_retries", 0),
    )
    return NokiaNetworkAsCodeProvider(config=config, **kwargs)


@pytest.mark.asyncio
async def test_nokia_provider_maps_official_sdk_methods():
    sdk = _FakeNokiaSdk()
    client = CamaraClient(provider=_nokia_provider(sdk_client=sdk))

    location = await client.get_location(
        ip_address="",
        device_id="dev1",
        customer_country="MA",
        phone_number="+99999991001",
    )
    roaming = await client.get_roaming(ip_address="", customer_country="MA", phone_number="+99999991001")
    sim_swap = await client.get_sim_swap(customer_id="cust", phone_number="+99999991001")
    device_swap = await client.get_device_swap(customer_id="cust", phone_number="+99999991001")

    assert location.verified is True
    assert roaming.roaming is True
    assert sim_swap.days_since_swap == 0
    assert device_swap.swapped is False
    assert ("location.verify_v1", {"phone_number": "+99999991001"}, {"area_type": "CIRCLE"}, 3600) in sdk.calls
    assert ("sim_swap.check", "+99999991001", 240) in sdk.calls
    assert ("device_swap.check", "+99999991001", 240) in sdk.calls


@pytest.mark.asyncio
async def test_nokia_number_verification_uses_oauth_hook():
    seen = {}

    def verifier(**kwargs):
        seen.update(kwargs)
        return {"verified": True}

    client = CamaraClient(provider=_nokia_provider(sdk_client=_FakeNokiaSdk(), number_verifier=verifier))
    signal = await client.get_number_verification(phone_number="+99999991001")

    assert signal.verified is True
    assert seen["client_id"] == "client-id"
    assert seen["token_url"] == "https://auth.example/token"


@pytest.mark.asyncio
async def test_nokia_number_verification_requires_consent_verifier():
    client = CamaraClient(provider=_nokia_provider(sdk_client=_FakeNokiaSdk()))
    with pytest.raises(CamaraProviderUnavailableError):
        await client.get_number_verification(phone_number="+99999991001")


@pytest.mark.asyncio
async def test_nokia_provider_timeout_policy():
    sdk = _FakeNokiaSdk()

    def slow_check(*, phone_number, max_age):
        time.sleep(0.05)
        return SimpleNamespace(swapped=False)

    sdk.sim_swap = SimpleNamespace(check=slow_check)
    client = CamaraClient(provider=_nokia_provider(sdk_client=sdk, timeout_seconds=0.001))

    with pytest.raises(CamaraTimeoutError):
        await client.get_sim_swap(customer_id="cust", phone_number="+99999991001")


@pytest.mark.asyncio
async def test_nokia_provider_retry_policy():
    sdk = _FakeNokiaSdk()
    attempts = {"count": 0}

    def flaky_check(*, phone_number, max_age):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary")
        return SimpleNamespace(swapped=False)

    sdk.sim_swap = SimpleNamespace(check=flaky_check)
    client = CamaraClient(provider=_nokia_provider(sdk_client=sdk, max_retries=1))

    signal = await client.get_sim_swap(customer_id="cust", phone_number="+99999991001")
    assert signal.days_since_swap == 9999
    assert attempts["count"] == 2


def test_provider_selection_from_environment(monkeypatch):
    monkeypatch.setenv("CAMARA_PROVIDER", "mock")
    assert build_camara_provider().__class__.__name__ == "MockCamaraProvider"

    monkeypatch.setenv("CAMARA_PROVIDER", "nokia")
    monkeypatch.setenv("NAC_BASE_URL", "network-as-code.nokia.rapidapi.com")
    monkeypatch.setenv("NAC_CLIENT_ID", "client")
    monkeypatch.setenv("NAC_CLIENT_SECRET", "secret")
    monkeypatch.setenv("NAC_TOKEN_URL", "https://auth.example/token")
    assert build_camara_provider().__class__.__name__ == "NokiaNetworkAsCodeProvider"
