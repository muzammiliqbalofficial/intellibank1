import pandas as pd
import numpy as np
from ml.churn.train import load_model, preprocess, CHURN_FEATURES
from ml.churn.explain import explain_churn_prediction

_model, _rf_model, _scaler, _features = None, None, None, None


def _load():
    global _model, _rf_model, _scaler, _features
    if _model is None:
        _model, _rf_model, _scaler, _features = load_model()


def predict_single(customer: dict) -> dict:
    _load()
    df = pd.DataFrame([customer])
    df = preprocess(df)

    for col in _features:
        if col not in df.columns:
            df[col] = 0
    df = df[_features].fillna(0)

    scaled = _scaler.transform(df)
    prob = float(_model.predict_proba(scaled)[0, 1])
    prediction = int(prob >= 0.5)

    shap_result = explain_churn_prediction(scaled, _rf_model, _features)

    return {
        "churn_probability": round(prob, 4),
        "will_churn": bool(prediction),
        "confidence": round(max(prob, 1 - prob), 4),
        "risk_segment": _risk_segment(prob),
        "retention_urgency": _retention_urgency(prob),
        "shap_values": shap_result["shap_values"],
        "top_factors": shap_result["top_features"],
    }


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    _load()
    processed = preprocess(df.copy())

    for col in _features:
        if col not in processed.columns:
            processed[col] = 0
    processed = processed[_features].fillna(0)

    scaled = _scaler.transform(processed)
    probs = _model.predict_proba(scaled)[:, 1]

    result = df.copy()
    result["churn_probability"] = probs.round(4)
    result["will_churn"] = (probs >= 0.5).astype(int)
    result["risk_segment"] = [_risk_segment(p) for p in probs]
    return result


def _risk_segment(prob: float) -> str:
    if prob >= 0.75:
        return "High Risk"
    elif prob >= 0.50:
        return "Medium Risk"
    elif prob >= 0.25:
        return "Low Risk"
    else:
        return "Loyal"


def _retention_urgency(prob: float) -> str:
    if prob >= 0.75:
        return "Immediate Action Required"
    elif prob >= 0.50:
        return "Schedule Retention Call"
    elif prob >= 0.25:
        return "Monitor Closely"
    else:
        return "No Action Needed"
