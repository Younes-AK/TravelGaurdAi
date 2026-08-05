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
    }
    with pytest.raises(ValueError):
        engine.predict(features)


def test_risk_engine_rejects_missing_features():
    engine = RiskEngine()
    with pytest.raises(ValueError):
        engine.predict({"transaction_amount": 100.0})
