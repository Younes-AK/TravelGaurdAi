from typing import Optional
from datetime import datetime, UTC
from types import SimpleNamespace

import pytest

from travelguard_ai.camara import CamaraClient, MockCamaraProvider, NokiaNetworkAsCodeConfig, NokiaNetworkAsCodeProvider
from travelguard_ai.camara.exceptions import CamaraProviderUnavailableError
from travelguard_ai.camara.open_gateway_provider import OpenGatewayCamaraProvider
from travelguard_ai.decision_agent import DecisionAgent
from travelguard_ai.models import CustomerProfile, Signals, Transaction


def _tx(amount: float = 50.0, device_id: Optional[str] = "dev-trusted") -> Transaction:
    return Transaction(
        transaction_id="tx1",
        amount=amount,
        currency="USD",
        merchant_country="MA",
        timestamp=datetime.now(UTC),
        device_id=device_id,
        ip_address="1.2.3.4",
    )


def _profile(phone_number: Optional[str] = "+212600000001") -> CustomerProfile:
    return CustomerProfile(
        customer_id="c1",
        home_country="US",
        trusted_devices=["dev-trusted"],
        avg_transaction_amount=45.0,
        travel_frequency=5,
        phone_number=phone_number,
    )


def test_decision_agent_approve_path_with_mock_provider():
    provider = MockCamaraProvider(seed=7)
    agent = DecisionAgent(camara_provider=provider)
    res = agent.decide(_tx(amount=50.0), _profile(), Signals(raw={}))
    assert res.decision in ("APPROVE", "STEP_UP", "REJECT")
    assert 0.0 <= res.risk_score <= 1.0
    assert len(res.camara_calls) >= 1


def test_decision_agent_recent_sim_swap_reject():
    provider = MockCamaraProvider(overrides={"sim_swap": {"provider": "mock", "confidence": 0.99, "days_since_swap": 0}})
    agent = DecisionAgent(camara_provider=provider)
    res = agent.decide(_tx(amount=700.0), _profile(), Signals(raw={}))
    assert res.decision == "REJECT"
    assert "recent_sim_swap" in res.reasoning


@pytest.mark.asyncio
async def test_decide_async_works():
    agent = DecisionAgent(camara_provider=MockCamaraProvider(seed=10))
    res = await agent.decide_async(_tx(), _profile(), Signals(raw={}))
    assert res.decision in ("APPROVE", "STEP_UP", "REJECT")


def test_open_gateway_provider_failure_can_be_captured_by_agent():
    provider = OpenGatewayCamaraProvider(base_url="https://example.com", api_key="key")
    agent = DecisionAgent(camara_provider=provider)
    res = agent.decide(_tx(amount=800.0), _profile(), Signals(raw={}))
    # Agent continues gracefully despite provider failures.
    assert any(item.startswith("camara_") for item in res.reasoning)


def test_decision_agent_rejects_invalid_amounts():
    with pytest.raises(ValueError):
        Transaction(
            transaction_id="tx-invalid",
            amount=float("inf"),
            currency="USD",
            merchant_country="US",
            # timestamp=datetime.utcnow(),
            timestamp=datetime.now(UTC),
        )


def test_decision_agent_rejects_invalid_customer_profile():
    with pytest.raises(ValueError):
        CustomerProfile(customer_id="c1", home_country="US", travel_frequency=-1)


@pytest.mark.asyncio
async def test_decision_agent_timeout_handling_continues():
    provider = MockCamaraProvider(timeout_seconds=0.001, artificial_delay_seconds=0.01)
    agent = DecisionAgent(camara_provider=provider, camara_timeout_seconds=0.001)
    result = await agent.decide_async(_tx(amount=650.0), _profile(), Signals(raw={}))
    assert result.decision in ("APPROVE", "STEP_UP", "REJECT")
    assert any(item.startswith("camara_") for item in result.reasoning)


class _AgentFakeNokiaSdk:
    def __init__(self):
        self.location = SimpleNamespace(verify_v1=self._location_verify)
        self.device_status = SimpleNamespace(retrieve_roaming_status=self._roaming_status)
        self.sim_swap = SimpleNamespace(check=self._sim_swap_check)
        self.device_swap = SimpleNamespace(check=self._device_swap_check)

    def _location_verify(self, *, device, area, max_age):
        return SimpleNamespace(verification_result="TRUE", match_rate=None)

    def _roaming_status(self, *, device):
        return SimpleNamespace(roaming=False, countryName=[])

    def _sim_swap_check(self, *, phone_number, max_age):
        return SimpleNamespace(swapped=False)

    def _device_swap_check(self, *, phone_number, max_age):
        return SimpleNamespace(swapped=False)


@pytest.mark.asyncio
async def test_decision_agent_end_to_end_with_nokia_provider():
    config = NokiaNetworkAsCodeConfig(
        base_url="network-as-code.nokia.rapidapi.com",
        client_id="client-id",
        client_secret="api-key",
        token_url="https://auth.example/token",
        timeout_seconds=1.0,
        max_retries=0,
    )
    provider = NokiaNetworkAsCodeProvider(
        config=config,
        sdk_client=_AgentFakeNokiaSdk(),
        number_verifier=lambda **_: {"verified": True},
    )
    agent = DecisionAgent(camara_provider=provider, camara_timeout_seconds=1.0)

    result = await agent.decide_async(_tx(amount=95.0), _profile(), Signals(raw={}))

    assert result.decision in ("APPROVE", "STEP_UP", "REJECT")
    assert set(result.camara_calls) == {
        "location",
        "roaming",
        "device_location",
        "sim_swap",
        "device_swap",
        "number_verification",
    }


@pytest.mark.asyncio
async def test_decision_agent_partial_signal_collection_lowers_confidence():
    provider = MockCamaraProvider(
        overrides={
            "roaming": {"provider": "mock", "confidence": 0.9, "country": "MA", "roaming": False},
            "sim_swap": {"provider": "mock", "confidence": 0.99, "days_since_swap": 120},
            "device_swap": {"provider": "mock", "confidence": 0.97, "swapped": False},
            "device_location": {"provider": "mock", "confidence": 0.9, "device_id": "dev-trusted", "country": "MA", "verified": True, "distance_km": 1.0},
            "number_verification": {"provider": "mock", "confidence": 0.98, "phone_number": "+212600000001", "verified": True},
            "location": {"provider": "mock", "confidence": 1.5},
        }
    )
    agent = DecisionAgent(camara_provider=provider)

    result = await agent.decide_async(_tx(amount=650.0), _profile(), Signals(raw={}))

    assert "location" not in result.camara_calls
    assert any(item.startswith("camara_location_failed") for item in result.reasoning)
    assert result.confidence <= 0.9
