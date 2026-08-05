import asyncio
import logging
import time
from typing import Dict, Any, List, Optional

from .camara import CamaraClient, CamaraError, CamaraProvider, MockCamaraProvider
from .feature_builder import FeatureBuilder
from .risk_engine import RiskEngine
from .explainability import Explainer
from .models import CustomerProfile, DecisionResult, Signals, Transaction


logger = logging.getLogger(__name__)


class DecisionAgent:
    """Orchestrates signal collection, feature building, risk scoring, and final decision."""

    def __init__(
        self,
        camara_client: Optional[CamaraClient] = None,
        camara_provider: Optional[CamaraProvider] = None,
        risk_engine: Optional[RiskEngine] = None,
        use_shap_explanations: bool = False,
        camara_timeout_seconds: float = 0.5,
    ):
        provider = camara_provider or MockCamaraProvider(timeout_seconds=camara_timeout_seconds)
        self.camara = camara_client or CamaraClient(provider=provider)
        self.fb = FeatureBuilder()
        self.risk_engine = risk_engine or RiskEngine()
        self.explainer = Explainer(getattr(self.risk_engine, "model", None))
        self.use_shap_explanations = use_shap_explanations
        self.camara_timeout_seconds = camara_timeout_seconds

    def validate(self, tx: Transaction, profile: CustomerProfile) -> List[str]:
        errs = []
        if tx.amount <= 0:
            errs.append("amount_must_be_positive")
        if not tx.merchant_country:
            errs.append("merchant_country_missing")
        return errs

    def inspect_signals(self, tx: Transaction, profile: CustomerProfile, signals: Signals) -> Dict[str, Any]:
        # decide which CAMARA APIs to call while minimizing unnecessary calls
        calls: List[str] = []
        s = signals.raw

        loc = s.get("location") or s.get("location_verification")
        loc_conf = float((loc or {}).get("confidence", 0.0)) if isinstance(loc, dict) else float(getattr(loc, "confidence", 0.0))
        if not loc or loc_conf < 0.9:
            calls.append("location")

        roam = s.get("roaming") or s.get("roaming_check")
        if not roam:
            calls.append("roaming")

        if tx.device_id and not (s.get("device_location") or s.get("device_verification")):
            calls.append("device_location")

        if not (s.get("sim_swap") or s.get("sim_swap_check")):
            calls.append("sim_swap")

        if not s.get("device_swap"):
            calls.append("device_swap")

        if profile.phone_number and not s.get("number_verification"):
            calls.append("number_verification")

        return {"to_call": calls}

    async def _safe_camara_call(self, call_name: str, coro, signals: Dict[str, Any], called: List[str], reasoning: List[str]) -> None:
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(coro, timeout=self.camara_timeout_seconds)
            latency_ms = (time.perf_counter() - started) * 1000.0
            if hasattr(result, "model_copy") and getattr(result, "api_latency_ms", None) is None:
                result = result.model_copy(update={"api_latency_ms": round(latency_ms, 2)})
            signals[call_name] = result
            called.append(call_name)
            logger.info(
                "camara_signal_collected",
                extra={"api": call_name, "latency_ms": round(latency_ms, 2), "confidence": getattr(result, "confidence", None)},
            )
        except CamaraError as exc:
            reasoning.append(f"camara_{call_name}_failed:{exc.__class__.__name__}")
            logger.warning("camara_signal_failed", extra={"api": call_name, "error": exc.__class__.__name__})
        except Exception:
            reasoning.append(f"camara_{call_name}_failed:unexpected_error")
            logger.exception("camara_signal_failed_unexpected", extra={"api": call_name})

    async def call_camara_async(
        self,
        tx: Transaction,
        profile: CustomerProfile,
        inspect: Dict[str, Any],
        reasoning: List[str],
    ) -> List[str]:
        called = []
        profile_signals = getattr(profile, "_signals_cache", None)
        if profile_signals is None:
            return called

        for api in inspect.get("to_call", []):
            if api == "location":
                await self._safe_camara_call(
                    "location",
                    self.camara.get_location(
                        ip_address=tx.ip_address or "",
                        device_id=tx.device_id,
                        customer_country=tx.merchant_country,
                        phone_number=profile.phone_number,
                    ),
                    profile_signals,
                    called,
                    reasoning,
                )
            elif api == "roaming":
                await self._safe_camara_call(
                    "roaming",
                    self.camara.get_roaming(
                        ip_address=tx.ip_address or "",
                        customer_country=tx.merchant_country,
                        phone_number=profile.phone_number,
                    ),
                    profile_signals,
                    called,
                    reasoning,
                )
            elif api == "sim_swap":
                await self._safe_camara_call(
                    "sim_swap",
                    self.camara.get_sim_swap(customer_id=profile.customer_id, phone_number=profile.phone_number),
                    profile_signals,
                    called,
                    reasoning,
                )
            elif api == "device_swap":
                await self._safe_camara_call(
                    "device_swap",
                    self.camara.get_device_swap(customer_id=profile.customer_id, phone_number=profile.phone_number),
                    profile_signals,
                    called,
                    reasoning,
                )
            elif api == "device_location" and tx.device_id:
                await self._safe_camara_call(
                    "device_location",
                    self.camara.get_device_location(
                        device_id=tx.device_id,
                        customer_country=tx.merchant_country,
                        phone_number=profile.phone_number,
                    ),
                    profile_signals,
                    called,
                    reasoning,
                )
            elif api == "number_verification" and profile.phone_number:
                await self._safe_camara_call(
                    "number_verification",
                    self.camara.get_number_verification(phone_number=profile.phone_number),
                    profile_signals,
                    called,
                    reasoning,
                )
            else:
                continue
        return called

    async def decide_async(self, tx: Transaction, profile: CustomerProfile, signals: Signals) -> DecisionResult:
        # validate
        errors = self.validate(tx, profile)
        if errors:
            return DecisionResult(
                decision="REJECT",
                risk_score=1.0,
                confidence=0.99,
                reasoning=["input_validation_failed"] + errors,
                signals_used=[],
                camara_calls=[],
            )

        reasoning: List[str] = []

        # inspect
        inspect = self.inspect_signals(tx, profile, signals)

        # attach a cache to profile for merging
        setattr(profile, "_signals_cache", signals.raw)
        camara_calls = await self.call_camara_async(tx, profile, inspect, reasoning)

        # build features
        features = self.fb.build(tx, profile, signals)

        # risk score
        result = self.risk_engine.predict(features)
        risk = result.risk_score
        confidence = result.confidence
        failed_camara_calls = sum(1 for item in reasoning if item.startswith("camara_") and "_failed:" in item)
        if failed_camara_calls:
            confidence = max(0.0, confidence - (0.1 * failed_camara_calls))

        signals_used = list(signals.raw.keys())

        # business rules
        sim_signal = signals.raw.get("sim_swap") or signals.raw.get("sim_swap_check")
        if hasattr(sim_signal, "model_dump"):
            sim_signal = sim_signal.model_dump()
        sim_days = (sim_signal or {}).get("days_since_swap") if isinstance(sim_signal, dict) else None
        if sim_days is not None and sim_days < 2:
            reasoning.append("recent_sim_swap")
            return DecisionResult(
                decision="REJECT",
                risk_score=1.0,
                confidence=0.99,
                reasoning=reasoning,
                signals_used=signals_used,
                camara_calls=camara_calls,
            )

        # trusted device + low risk -> approve
        if features.get("trusted_device", 0.0) > 0 and risk < 0.25 and confidence > 0.8:
            reasoning.append("trusted_device_and_low_risk")
            return DecisionResult(
                decision="APPROVE",
                risk_score=risk,
                confidence=confidence,
                reasoning=reasoning,
                signals_used=signals_used,
                camara_calls=camara_calls,
            )

        # score-based policy
        if risk < 0.25:
            decision = "APPROVE"
            reasoning.append("low_risk_score")
        elif risk < 0.7:
            decision = "STEP_UP"
            reasoning.append("medium_risk_score")
        else:
            decision = "REJECT"
            reasoning.append("high_risk_score")

        # add explanations via SHAP if possible
        feature_names = sorted(features.keys())
        try:
            explanation = self.explainer.explain(
                feature_names,
                features,
                top_k=5,
                use_shap=self.use_shap_explanations,
            )
            for fn, val in explanation.get("top_features", []):
                reasoning.append(f"feature:{fn}:{float(val):.3f}")
        except Exception:
            pass

        logger.info(
            "decision_completed",
            extra={
                "decision": decision,
                "risk_score": risk,
                "confidence": confidence,
                "camara_calls": camara_calls,
                "signals_used": signals_used,
            },
        )

        return DecisionResult(
            decision=decision,
            risk_score=risk,
            confidence=confidence,
            reasoning=reasoning,
            signals_used=signals_used,
            camara_calls=camara_calls,
        )

    def decide(self, tx: Transaction, profile: CustomerProfile, signals: Signals) -> DecisionResult:
        return asyncio.run(self.decide_async(tx, profile, signals))
