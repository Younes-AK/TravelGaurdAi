from datetime import datetime, UTC

import pytest

from travelguard_ai.feature_builder import FeatureBuilder
from travelguard_ai.models import Transaction, CustomerProfile, Signals


def test_build_basic_features():
    tx = Transaction(
        transaction_id="tx1",
        amount=120.0,
        currency="USD",
        merchant_country="US",
        timestamp=datetime.now(UTC),
        device_id="dev1",
        ip_address="1.2.3.4",
    )
    profile = CustomerProfile(customer_id="c1", home_country="US", trusted_devices=["dev1"], avg_transaction_amount=60.0, travel_frequency=3)
    signals = Signals(raw={
        "location_verification": {"country": "US", "confidence": 0.95},
        "device_verification": {"device_known": True, "confidence": 0.9},
        "sim_swap_check": {"days_since_swap": 400},
        "roaming_check": {"roaming": False, "confidence": 0.6},
    })

    fb = FeatureBuilder()
    features = fb.build(tx, profile, signals)
    assert features["transaction_amount"] == 120.0
    assert features["trusted_device"] == 1.0
    assert features["location_verified"] > 0.9


def test_build_handles_missing_camara_signals():
    tx = Transaction(
        transaction_id="tx1",
        amount=120.0,
        currency="USD",
        merchant_country="US",
        timestamp=datetime.now(UTC),
        device_id="dev1",
        ip_address="1.2.3.4",
    )
    profile = CustomerProfile(customer_id="c1", home_country="US", trusted_devices=["dev1"], avg_transaction_amount=60.0, travel_frequency=3)
    features = FeatureBuilder().build(tx, profile, Signals(raw={}))
    assert features["location_verified"] == 0.0
    assert features["device_verified"] == 0.0
    assert features["sim_swap_days"] == 9999.0


def test_build_rejects_extreme_invalid_amounts():
    with pytest.raises(ValueError):
        tx = Transaction(
            transaction_id="tx1",
            amount=float("inf"),
            currency="USD",
            merchant_country="US",
            timestamp=datetime.now(UTC),
        )
        profile = CustomerProfile(customer_id="c1", home_country="US")
        FeatureBuilder().build(tx, profile, Signals(raw={}))
