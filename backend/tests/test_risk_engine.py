import math

import pytest

from travelguard_ai.risk_engine import RiskEngine


def test_risk_engine_predict_shape():
    engine = RiskEngine()
    features = {
        "transaction_amount": 100.0,
        "amount_deviation": 20.0,
        "travel_frequency": 4.0,
        "trusted_device": 1.0,
        "location_verified": 0.9,
        "location_country_match": 1.0,
        "device_verified": 0.85,
        "device_match": 1.0,
        "sim_swap_days": 420.0,
        "roaming": 0.0,
        "average_amount": 80.0,
        "time_of_day": 12.0,
        "distance_from_home": 0.0,
        "log_amount": math.log1p(100.0),
        "capped_amount": 100.0,
        "amount_ratio_to_average": 1.25,
        "device_swap_detected": 0.0,
    }
    out = engine.predict(features)
    assert 0.0 <= out.risk_score <= 1.0
    assert 0.0 <= out.fraud_probability <= 1.0
    assert 0.0 <= out.confidence <= 1.0


@pytest.mark.parametrize(
    "bad_value",
    [float("nan"), float("inf"), float("-inf")],
)
def test_risk_engine_rejects_non_finite_values(bad_value):
    engine = RiskEngine()
    features = {
        "transaction_amount": 100.0,
        "amount_deviation": 20.0,
        "travel_frequency": 4.0,
        "trusted_device": 1.0,
        "location_verified": 0.9,
        "location_country_match": 1.0,
        "device_verified": 0.85,
        "device_match": 1.0,
        "sim_swap_days": 420.0,
        "roaming": 0.0,
        "average_amount": 80.0,
        "time_of_day": 12.0,
        "distance_from_home": 0.0,
        "log_amount": math.log1p(100.0),
        "capped_amount": 100.0,
        "amount_ratio_to_average": bad_value,
        "device_swap_detected": 0.0,
    }
    with pytest.raises(ValueError):
        engine.predict(features)


def test_risk_engine_rejects_missing_features():
    engine = RiskEngine()
    with pytest.raises(ValueError):
        engine.predict({"transaction_amount": 100.0})


def _feature_vector(**overrides):
    base = {
        "transaction_amount": 100.0,
        "amount_deviation": 20.0,
        "travel_frequency": 4.0,
        "trusted_device": 1.0,
        "location_verified": 0.9,
        "location_country_match": 1.0,
        "device_verified": 0.85,
        "device_match": 1.0,
        "sim_swap_days": 420.0,
        "roaming": 0.0,
        "average_amount": 80.0,
        "time_of_day": 12.0,
        "distance_from_home": 0.0,
        "log_amount": math.log1p(100.0),
        "capped_amount": 100.0,
        "amount_ratio_to_average": 1.25,
        "device_swap_detected": 0.0,
    }
    base.update(overrides)
    return base


def test_risk_engine_approves_genuine_frequent_traveler():
    """Ahmed's coffee purchase from the pitch deck: trusted device, frequent
    traveler, SIM stable for 247 days, small amount abroad — must score low."""
    engine = RiskEngine()
    features = _feature_vector(
        transaction_amount=4.20,
        average_amount=12.0,
        amount_deviation=4.20 - 12.0,
        amount_ratio_to_average=4.20 / 12.0,
        log_amount=math.log1p(4.20),
        capped_amount=4.20,
        travel_frequency=6.0,
        trusted_device=1.0,
        location_country_match=0.0,
        device_match=1.0,
        sim_swap_days=247.0,
        roaming=1.0,
        distance_from_home=0.7,
    )
    out = engine.predict(features)
    assert out.risk_score < 0.25


def test_risk_engine_flags_first_time_high_value_traveler_for_step_up():
    """First trip abroad, no travel history, large purchase relative to the
    customer's normal spend — should land in the step-up band, not auto-approve
    or auto-reject."""
    engine = RiskEngine()
    features = _feature_vector(
        transaction_amount=1850.0,
        average_amount=90.0,
        amount_deviation=1850.0 - 90.0,
        amount_ratio_to_average=1850.0 / 90.0,
        log_amount=math.log1p(1850.0),
        capped_amount=1850.0,
        travel_frequency=0.0,
        trusted_device=0.0,
        location_country_match=0.0,
        device_verified=0.75,
        device_match=0.0,
        sim_swap_days=12.0,
        roaming=1.0,
        distance_from_home=0.7,
    )
    out = engine.predict(features)
    assert 0.25 <= out.risk_score < 0.7


def test_confidence_is_not_identical_to_risk_score():
    engine = RiskEngine()
    features = _feature_vector(
        transaction_amount=1850.0,
        average_amount=90.0,
        amount_deviation=1850.0 - 90.0,
        amount_ratio_to_average=1850.0 / 90.0,
        travel_frequency=0.0,
        trusted_device=0.0,
        location_country_match=0.0,
        device_verified=0.75,
        device_match=0.0,
        sim_swap_days=12.0,
        roaming=1.0,
        distance_from_home=0.7,
    )
    out = engine.predict(features)
    assert out.confidence != out.risk_score
