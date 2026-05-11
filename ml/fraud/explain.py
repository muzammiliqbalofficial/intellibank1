import numpy as np
import shap
from typing import Optional


_explainer = None


def _get_explainer(model):
    global _explainer
    if _explainer is None:
        _explainer = shap.TreeExplainer(model)
    return _explainer


def explain_prediction(X_scaled: np.ndarray, model, feature_names: list) -> dict:
    explainer = _get_explainer(model)
    shap_values = explainer.shap_values(X_scaled)

    # For binary classification, shap_values may be list [class0, class1]
    if isinstance(shap_values, list):
        sv = shap_values[1][0]
    else:
        sv = shap_values[0]

    # Build top features
    abs_sv = np.abs(sv)
    top_idx = np.argsort(abs_sv)[::-1][:10]

    top_features = [
        {
            "feature": feature_names[i],
            "shap_value": round(float(sv[i]), 4),
            "abs_impact": round(float(abs_sv[i]), 4),
            "direction": "increases_risk" if sv[i] > 0 else "decreases_risk",
        }
        for i in top_idx
    ]

    return {
        "shap_values": {feature_names[i]: round(float(sv[i]), 4) for i in range(len(feature_names))},
        "top_features": top_features,
        "base_value": round(float(explainer.expected_value[1] if isinstance(explainer.expected_value, np.ndarray) else explainer.expected_value), 4),
    }


def explain_batch(X_scaled: np.ndarray, model, feature_names: list) -> dict:
    """Returns mean absolute SHAP values across a batch — for global feature importance."""
    explainer = _get_explainer(model)
    shap_values = explainer.shap_values(X_scaled)

    if isinstance(shap_values, list):
        sv = shap_values[1]
    else:
        sv = shap_values

    mean_abs = np.abs(sv).mean(axis=0)
    ranked = np.argsort(mean_abs)[::-1]

    return {
        "global_importance": [
            {"feature": feature_names[i], "mean_abs_shap": round(float(mean_abs[i]), 4)}
            for i in ranked
        ]
    }
