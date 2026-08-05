from typing import Dict, Any, List, Sequence

import numpy as np


class Explainer:
    def __init__(self, model):
        self.model = model
        self._explainer = None
        self._shap_initialized = False

    def _init_shap(self) -> None:
        if self._shap_initialized:
            return
        self._shap_initialized = True
        try:
            import shap  # optional dependency; import only when SHAP path is explicitly used

            self._explainer = shap.TreeExplainer(self.model)
        except Exception:
            self._explainer = None

    def explain(
        self,
        feature_names: Sequence[str],
        features: Dict[str, float],
        top_k: int = 5,
        use_shap: bool = False,
    ) -> Dict[str, Any]:
        X = np.array([features[n] for n in feature_names], dtype=float).reshape(1, -1)
        if use_shap:
            self._init_shap()
        if use_shap and self._explainer:
            vals = self._explainer.shap_values(X)
            # shap_values may be list for multiclass
            arr = vals[1] if isinstance(vals, list) and len(vals) > 1 else vals
            importance = sorted(
                zip(feature_names, arr[0].tolist()), key=lambda x: abs(x[1]), reverse=True
            )[:top_k]
            return {"top_features": importance}
        else:
            # fallback: use model feature_importances_
            try:
                importances = getattr(self.model, "feature_importances_", None)
                if importances is None:
                    return {"top_features": []}
                importance = sorted(
                    zip(feature_names, np.asarray(importances, dtype=float).tolist()), key=lambda x: abs(x[1]), reverse=True
                )[:top_k]
                return {"top_features": importance}
            except Exception:
                return {"top_features": []}
