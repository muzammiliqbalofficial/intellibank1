import numpy as np
import shap

_explainer = None


def _get_explainer(rf_model):
    global _explainer
    if _explainer is None:
        _explainer = shap.TreeExplainer(rf_model)
    return _explainer


def explain_churn_prediction(X_scaled: np.ndarray, rf_model, feature_names: list) -> dict:
    explainer = _get_explainer(rf_model)
    shap_values = explainer.shap_values(X_scaled)
    feature_names = list(feature_names)

    # Handle different SHAP versions and RF output formats
    if isinstance(shap_values, list):
        # Classic format: list of arrays per class
        raw = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        sv = np.array(raw[0] if raw.ndim == 2 else raw, dtype=float)
    elif hasattr(shap_values, 'values'):
        # Explanation object (SHAP >= 0.41)
        vals = shap_values.values
        sv = np.array(vals[0, :, 1] if vals.ndim == 3 else vals[0], dtype=float)
    else:
        arr = np.array(shap_values, dtype=float)
        if arr.ndim == 3:
            sv = arr[0, :, 1]
        elif arr.ndim == 2:
            sv = arr[0]
        else:
            sv = arr

    abs_sv = np.abs(sv)
    top_idx = np.argsort(abs_sv)[::-1][:10]

    top_features = [
        {
            "feature": feature_names[int(i)],
            "shap_value": round(float(sv[int(i)]), 4),
            "abs_impact": round(float(abs_sv[int(i)]), 4),
            "direction": "increases_churn_risk" if sv[int(i)] > 0 else "decreases_churn_risk",
            "readable": _readable_feature(feature_names[int(i)], sv[int(i)]),
        }
        for i in top_idx
    ]

    return {
        "shap_values": {feature_names[i]: round(float(sv[i]), 4) for i in range(len(feature_names))},
        "top_features": top_features,
    }


def _readable_feature(feature: str, shap_val: float) -> str:
    direction = "increasing" if shap_val > 0 else "decreasing"
    labels = {
        "credit_score": f"Credit score is {direction} churn probability",
        "age": f"Customer age is {direction} churn probability",
        "tenure": f"Tenure is {direction} churn probability",
        "balance": f"Account balance is {direction} churn probability",
        "num_products": f"Number of products is {direction} churn probability",
        "is_active_member": f"Activity status is {direction} churn probability",
        "balance_salary_ratio": f"Balance-to-salary ratio is {direction} churn probability",
    }
    return labels.get(feature, f"{feature} is {direction} churn probability")
