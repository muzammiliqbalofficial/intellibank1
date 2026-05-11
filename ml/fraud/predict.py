import pandas as pd
import numpy as np
from typing import Union
from ml.fraud.train import load_model, preprocess
from ml.fraud.explain import explain_prediction


_model, _scaler, _features = None, None, None


def _load():
    global _model, _scaler, _features
    if _model is None:
        _model, _scaler, _features = load_model()


def predict_single(transaction: dict) -> dict:
    _load()
    df = pd.DataFrame([transaction])
    df = preprocess(df)

    # Align columns to training features
    for col in _features:
        if col not in df.columns:
            df[col] = 0
    df = df[_features]

    scaled = _scaler.transform(df)
    prob = float(_model.predict_proba(scaled)[0, 1])
    prediction = int(prob >= 0.5)

    shap_result = explain_prediction(scaled, _model, _features)

    return {
        "fraud_probability": round(prob, 4),
        "is_fraud": bool(prediction),
        "confidence": round(max(prob, 1 - prob), 4),
        "risk_level": _risk_level(prob),
        "shap_values": shap_result["shap_values"],
        "top_features": shap_result["top_features"],
    }


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    _load()
    processed = preprocess(df.copy())

    for col in _features:
        if col not in processed.columns:
            processed[col] = 0
    processed = processed[_features]

    scaled = _scaler.transform(processed)
    probs = _model.predict_proba(scaled)[:, 1]

    df = df.copy()
    df["fraud_probability"] = probs.round(4)
    df["is_fraud_predicted"] = (probs >= 0.5).astype(int)
    df["risk_level"] = [_risk_level(p) for p in probs]
    return df


def _risk_level(prob: float) -> str:
    if prob >= 0.80:
        return "CRITICAL"
    elif prob >= 0.60:
        return "HIGH"
    elif prob >= 0.40:
        return "MEDIUM"
    else:
        return "LOW"
