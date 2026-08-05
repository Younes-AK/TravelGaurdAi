from typing import Optional
from datetime import datetime, UTC

import pytest

from travelguard_ai.camara import CamaraClient, MockCamaraProvider
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
