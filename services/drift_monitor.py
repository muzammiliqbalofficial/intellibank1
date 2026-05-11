"""
Model Drift Monitoring using Evidently AI + custom KS-test fallback
"""
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
from scipy import stats
from sqlalchemy.orm import Session
from db.models import ModelMetric


class DriftMonitor:

    def __init__(self, model_type: str, reference_data: pd.DataFrame):
        self.model_type = model_type
        self.reference_data = reference_data

    def detect_drift(self, current_data: pd.DataFrame, db: Optional[Session] = None) -> dict:
        results = {}
        drifted_features = []

        numeric_cols = [c for c in self.reference_data.select_dtypes(include=[np.number]).columns
                        if c in current_data.columns]

        for col in numeric_cols:
            ref = self.reference_data[col].dropna().values
            cur = current_data[col].dropna().values

            if len(ref) < 10 or len(cur) < 10:
                continue

            ks_stat, p_value = stats.ks_2samp(ref, cur)
            drifted = p_value < 0.05

            results[col] = {
                "ks_statistic": round(float(ks_stat), 4),
                "p_value": round(float(p_value), 4),
                "drift_detected": drifted,
                "ref_mean": round(float(ref.mean()), 4),
                "cur_mean": round(float(cur.mean()), 4),
                "mean_shift_pct": round(abs(cur.mean() - ref.mean()) / (abs(ref.mean()) + 1e-8) * 100, 2),
            }
            if drifted:
                drifted_features.append(col)

        overall_drift = len(drifted_features) > 0
        drift_score = len(drifted_features) / max(len(results), 1)

        summary = {
            "model_type": self.model_type,
            "checked_at": datetime.utcnow().isoformat(),
            "total_features_checked": len(results),
            "drifted_features_count": len(drifted_features),
            "drifted_features": drifted_features,
            "drift_score": round(drift_score, 4),
            "overall_drift_detected": overall_drift,
            "feature_details": results,
            "recommendation": self._get_recommendation(drift_score),
        }

        if db:
            self._save_metric(db, drift_score, overall_drift)

        return summary

    def _get_recommendation(self, drift_score: float) -> str:
        if drift_score >= 0.5:
            return "CRITICAL: Significant data drift detected. Retrain model immediately."
        elif drift_score >= 0.3:
            return "WARNING: Moderate drift detected. Schedule model retraining."
        elif drift_score >= 0.1:
            return "INFO: Minor drift detected. Monitor closely."
        else:
            return "OK: No significant drift detected."

    def _save_metric(self, db: Session, drift_score: float, drift_detected: bool):
        metric = ModelMetric(
            model_type=self.model_type,
            metric_name="data_drift_score",
            metric_value=drift_score,
            drift_detected=drift_detected,
            drift_score=drift_score,
        )
        db.add(metric)
        db.commit()

    @staticmethod
    def get_metric_history(db: Session, model_type: str, limit: int = 30) -> list:
        return (
            db.query(ModelMetric)
            .filter_by(model_type=model_type)
            .order_by(ModelMetric.recorded_at.desc())
            .limit(limit)
            .all()
        )


def run_fraud_drift_check(current_df: pd.DataFrame, db: Optional[Session] = None) -> dict:
    import json
    from pathlib import Path
    ref_path = Path("ml/fraud/artifacts/fraud_reference_data.pkl")
    if not ref_path.exists():
        return {"error": "Reference data not found. Train model first."}
    import joblib
    reference = joblib.load(ref_path)
    monitor = DriftMonitor("fraud", reference)
    return monitor.detect_drift(current_df, db)


def run_churn_drift_check(current_df: pd.DataFrame, db: Optional[Session] = None) -> dict:
    from pathlib import Path
    ref_path = Path("ml/churn/artifacts/churn_reference_data.pkl")
    if not ref_path.exists():
        return {"error": "Reference data not found. Train model first."}
    import joblib
    reference = joblib.load(ref_path)
    monitor = DriftMonitor("churn", reference)
    return monitor.detect_drift(current_df, db)
