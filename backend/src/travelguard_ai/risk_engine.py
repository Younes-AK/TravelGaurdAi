from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Sequence
import math
import pickle

import numpy as np

try:
    from xgboost import XGBRegressor
except Exception as exc:  # pragma: no cover - hard fail if xgboost is unavailable at runtime
    raise ImportError(
        "XGBoost is required for TravelGuard AI risk scoring. Install the runtime dependencies so libxgboost can load."
    ) from exc

from .models import RiskAssessment, RiskFeatureVector


FEATURE_NAMES: Sequence[str] = (
    "transaction_amount",
    "amount_deviation",
    "travel_frequency",
    "trusted_device",
    "location_verified",
    "location_country_match",
    "device_verified",
    "device_match",
    "sim_swap_days",
    "roaming",
    "average_amount",
    "time_of_day",
    "distance_from_home",
    "log_amount",
    "capped_amount",
    "amount_ratio_to_average",
    "device_swap_detected",
)


@dataclass(frozen=True)
class FeatureFrame:
    values: np.ndarray
    feature_names: Sequence[str]


def _synthetic_training_frame(n_samples: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Sample a synthetic-but-semantically-grounded fraud dataset.

    Feature combinations and their fraud-probability weights are hand-crafted to
    encode the same signal-fusion rules TravelGuard's pitch describes (recent
    SIM/device swap dominates; a roaming, frequent traveler with a stable SIM is
    safe; a first-time traveler making an unusually large purchase sits in
    between). The target is the continuous fraud probability itself (not a
    Bernoulli-sampled label) so XGBoost regresses toward the intended fusion
    function directly instead of fitting noisy binary draws in sparsely-sampled
    corners of the feature space — it's still a real trained model producing a
    smooth, generalized surface, just fit on a cleaner signal.
    """
    rng = np.random.default_rng(seed)
    n = n_samples

    trusted_device = rng.random(n) < 0.55
    travel_frequency = rng.poisson(3.0, n).astype(np.float64)
    roaming = rng.random(n) < 0.5
    device_swap_detected = rng.random(n) < 0.04

    recent_swap_mask = rng.random(n) < 0.06
    sim_swap_days = np.where(
        recent_swap_mask,
        rng.integers(0, 3, n),
        rng.integers(3, 500, n),
    ).astype(np.float64)

    location_verified = np.clip(rng.normal(0.85, 0.15, n), 0.0, 1.0)
    device_verified = np.clip(rng.normal(0.82, 0.18, n), 0.0, 1.0)

    match_prob = np.where(roaming, 0.15, 0.8)
    location_country_match = (rng.random(n) < match_prob).astype(np.float64)

    device_match_prob = np.where(trusted_device, 0.9, 0.35)
    device_match = (rng.random(n) < device_match_prob).astype(np.float64)

    average_amount = np.clip(rng.lognormal(mean=4.2, sigma=0.9, size=n), 5.0, 5000.0)
    amount_multiplier = rng.lognormal(mean=0.0, sigma=0.9, size=n)
    transaction_amount = np.clip(average_amount * amount_multiplier, 0.5, 200_000.0)

    amount_deviation = transaction_amount - average_amount
    amount_ratio_to_average = transaction_amount / np.maximum(average_amount, 1e-6)
    log_amount = np.log1p(transaction_amount)
    capped_amount = np.minimum(transaction_amount, 1_000_000.0)

    time_of_day = rng.integers(0, 24, n).astype(np.float64)

    distance_base = rng.random(n)
    distance_from_home = np.where(roaming, np.clip(distance_base * 0.6 + 0.4, 0.0, 1.0), np.clip(distance_base * 0.3, 0.0, 1.0))

    trusted_f = trusted_device.astype(np.float64)
    roaming_f = roaming.astype(np.float64)
    device_swap_f = device_swap_detected.astype(np.float64)

    first_time_abroad = (roaming_f == 1.0) & (travel_frequency == 0.0)
    genuine_traveler = (roaming_f == 1.0) & (location_country_match == 0.0) & (travel_frequency > 0.0)
    signal_conflict = (roaming_f == 1.0) & (location_country_match == 1.0)
    recent_sim = sim_swap_days < 2.0
    amount_excess = np.clip(amount_ratio_to_average - 3.0, 0.0, 6.0)

    score = (
        4.5 * recent_sim.astype(np.float64)
        + 3.5 * device_swap_f
        + 1.6 * signal_conflict.astype(np.float64)
        - 1.4 * genuine_traveler.astype(np.float64)
        + 1.1 * first_time_abroad.astype(np.float64)
        + 0.18 * amount_excess
        - 1.1 * trusted_f
        - 0.7 * device_match
        + 0.9 * (1.0 - device_verified)
        + 0.7 * (1.0 - location_verified)
        - 0.01 * np.minimum(sim_swap_days, 400.0)
        + 0.15 * distance_from_home
        - 2.6
    )
    logits = score + rng.normal(0.0, 0.4, n)
    probability = 1.0 / (1.0 + np.exp(-logits))

    columns = {
        "transaction_amount": transaction_amount,
        "amount_deviation": amount_deviation,
        "travel_frequency": travel_frequency,
        "trusted_device": trusted_f,
        "location_verified": location_verified,
        "location_country_match": location_country_match,
        "device_verified": device_verified,
        "device_match": device_match,
        "sim_swap_days": sim_swap_days,
        "roaming": roaming_f,
        "average_amount": average_amount,
        "time_of_day": time_of_day,
        "distance_from_home": distance_from_home,
        "log_amount": log_amount,
        "capped_amount": capped_amount,
        "amount_ratio_to_average": amount_ratio_to_average,
        "device_swap_detected": device_swap_f,
    }
    X = np.column_stack([columns[name] for name in FEATURE_NAMES]).astype(np.float32)
    return X, probability.astype(np.float32)


class RiskEngine:
    """XGBoost-backed risk engine with strict feature validation and deterministic training."""

    def __init__(self, model_path: Optional[str] = None):
        self.feature_names = list(FEATURE_NAMES)
        self.model = self._load_or_train_model(model_path)

    def _load_or_train_model(self, model_path: Optional[str]):
        if model_path:
            with open(model_path, "rb") as handle:
                model = pickle.load(handle)
            return model

        X, y = _synthetic_training_frame(n_samples=20000, seed=42)

        model = XGBRegressor(
            objective="reg:logistic",
            eval_metric="rmse",
            n_estimators=200,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=1,
            tree_method="hist",
        )
        model.fit(X, y)
        return model

    def _validate_and_order_features(self, features: Dict[str, float]) -> FeatureFrame:
        if not features:
            raise ValueError("features must not be empty")

        validated = RiskFeatureVector(features=features).features

        missing = [name for name in self.feature_names if name not in validated]
        if missing:
            raise ValueError(f"missing required features: {', '.join(missing)}")

        ordered = np.array([validated[name] for name in self.feature_names], dtype=np.float32)
        if ordered.size == 0:
            raise ValueError("features must not be empty")
        if not np.all(np.isfinite(ordered)):
            raise ValueError("features must be finite")

        return FeatureFrame(values=ordered.reshape(1, -1), feature_names=self.feature_names)

    def _stable_confidence(self, probability: float) -> float:
        """How decisive the score is, not the score itself: 0 at the 50/50
        boundary, rising toward 1 as the model leans firmly toward safe or risky."""
        probability = min(max(probability, 0.0), 1.0)
        certainty = 2.0 * abs(probability - 0.5)
        return float(min(max(certainty, 0.0), 1.0))

    def predict(self, features: Dict[str, float]) -> RiskAssessment:
        frame = self._validate_and_order_features(features)
        probability = float(self.model.predict(frame.values)[0])
        probability = min(max(probability, 0.0), 1.0)
        confidence = self._stable_confidence(probability)
        return RiskAssessment(risk_score=probability, fraud_probability=probability, confidence=confidence)
