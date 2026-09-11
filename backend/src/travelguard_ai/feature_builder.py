from .models import Transaction, CustomerProfile, Signals
from typing import Dict, Any
import math


def _as_signal_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {}


class FeatureBuilder:
    """Converts transaction/profile/signals into ML features."""

    def build(self, tx: Transaction, profile: CustomerProfile, signals: Signals) -> Dict[str, float]:
        s = signals.raw
        features: Dict[str, float] = {}

        features["transaction_amount"] = float(tx.amount)
        avg_amount = float(profile.avg_transaction_amount or 0.0)
        features["amount_deviation"] = float(tx.amount - avg_amount)
        features["travel_frequency"] = float(profile.travel_frequency or 0)
        features["trusted_device"] = 1.0 if tx.device_id and tx.device_id in (profile.trusted_devices or []) else 0.0

        # location features
        loc = _as_signal_dict(s.get("location_verification") or s.get("location"))
        if loc:
            features["location_verified"] = float(loc.get("confidence", 0.0))
            features["location_country_match"] = 1.0 if loc.get("country") == profile.home_country else 0.0
        else:
            features["location_verified"] = 0.0
            features["location_country_match"] = 0.0

        # device
        dev = _as_signal_dict(s.get("device_verification") or s.get("device_location"))
        if dev:
            features["device_verified"] = float(dev.get("confidence", 0.0))
            if "device_known" in dev:
                features["device_match"] = 1.0 if dev.get("device_known") else 0.0
            else:
                features["device_match"] = 1.0 if dev.get("verified") else 0.0
        else:
            features["device_verified"] = 0.0
            features["device_match"] = 0.0

        # sim swap
        sim = _as_signal_dict(s.get("sim_swap_check") or s.get("sim_swap"))
        if sim:
            days = sim.get("days_since_swap")
            features["sim_swap_days"] = float(days if days is not None else 9999)
        else:
            features["sim_swap_days"] = 9999.0

        # roaming
        roam = _as_signal_dict(s.get("roaming_check") or s.get("roaming"))
        features["roaming"] = float(roam.get("roaming", False)) if roam else 0.0

        device_swap = _as_signal_dict(s.get("device_swap"))
        features["device_swap_detected"] = float(device_swap.get("swapped", False)) if device_swap else 0.0

        # historical features
        features["average_amount"] = float(profile.avg_transaction_amount or 0.0)
        features["time_of_day"] = float(tx.timestamp.hour)

        # distance from home: prefer the CAMARA device-location distance signal,
        # fall back to a coarse country-mismatch heuristic when it wasn't collected
        distance_km = dev.get("distance_km") if dev else None
        if distance_km is not None:
            features["distance_from_home"] = float(min(float(distance_km) / 500.0, 1.0))
        else:
            features["distance_from_home"] = 1.0 if tx.merchant_country != profile.home_country else 0.0

        # stable, bounded transform for extremely large values
        amount = features["transaction_amount"]
        features["log_amount"] = math.log1p(amount) if amount > 0 else 0.0
        features["capped_amount"] = min(amount, 1_000_000.0)
        features["amount_ratio_to_average"] = amount / avg_amount if avg_amount > 0 else 1.0

        # explicit finiteness check before returning anything to the model
        for name, value in features.items():
            if not math.isfinite(value):
                raise ValueError(f"feature '{name}' must be finite")

        return features
