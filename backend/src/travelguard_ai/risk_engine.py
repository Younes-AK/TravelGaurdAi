from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Sequence
import math
import pickle

import numpy as np
from sklearn.datasets import make_classification

try:
    from xgboost import XGBClassifier
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
)


@dataclass(frozen=True)
class FeatureFrame:
    values: np.ndarray
    feature_names: Sequence[str]


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

        X, y = make_classification(
            n_samples=4000,
            n_features=len(self.feature_names),
            n_informative=8,
            n_redundant=2,
            n_repeated=0,
            weights=[0.85, 0.15],
            class_sep=1.5,
            flip_y=0.01,
            random_state=42,
        )

        model = XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            n_estimators=120,
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
        probability = min(max(probability, 0.0), 1.0)
        return float(max(probability, 1.0 - probability))

    def predict(self, features: Dict[str, float]) -> RiskAssessment:
        frame = self._validate_and_order_features(features)
        probability = float(self.model.predict_proba(frame.values)[0][1])
        probability = min(max(probability, 0.0), 1.0)
        confidence = self._stable_confidence(probability)
        return RiskAssessment(risk_score=probability, fraud_probability=probability, confidence=confidence)
