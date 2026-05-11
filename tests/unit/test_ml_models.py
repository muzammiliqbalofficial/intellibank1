import pytest
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestFraudPreprocessing:
    def test_preprocess_adds_log_amount(self):
        from ml.fraud.train import preprocess
        df = pd.DataFrame({"amount": [100.0, 500.0], "is_fraud": [0, 1]})
        result = preprocess(df)
        assert "log_amount" in result.columns

    def test_preprocess_fills_nulls(self):
        from ml.fraud.train import preprocess
        df = pd.DataFrame({"amount": [100.0, None, 300.0], "is_fraud": [0, 0, 1]})
        result = preprocess(df)
        assert result["amount"].isnull().sum() == 0

    def test_risk_level_mapping(self):
        from ml.fraud.predict import _risk_level
        assert _risk_level(0.90) == "CRITICAL"
        assert _risk_level(0.65) == "HIGH"
        assert _risk_level(0.45) == "MEDIUM"
        assert _risk_level(0.20) == "LOW"


class TestChurnPreprocessing:
    def test_preprocess_creates_balance_ratio(self):
        from ml.churn.train import preprocess
        df = pd.DataFrame({
            "credit_score": [650], "age": [40], "tenure": [5],
            "balance": [100000], "num_products": [2],
            "has_credit_card": [1], "is_active_member": [1],
            "estimated_salary": [500000],
            "geography": ["Karachi"], "gender": ["Male"],
        })
        result = preprocess(df)
        assert "balance_salary_ratio" in result.columns
        assert "gender_encoded" in result.columns

    def test_risk_segment_mapping(self):
        from ml.churn.predict import _risk_segment, _retention_urgency
        assert _risk_segment(0.80) == "High Risk"
        assert _risk_segment(0.55) == "Medium Risk"
        assert _risk_segment(0.30) == "Low Risk"
        assert _risk_segment(0.10) == "Loyal"
        assert "Immediate" in _retention_urgency(0.80)


class TestForecastPreparation:
    def test_prepare_prophet_df(self):
        from ml.forecast.train import prepare_prophet_df
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "revenue": [100000, 120000, 95000],
        })
        result = prepare_prophet_df(df)
        assert "ds" in result.columns
        assert "y" in result.columns
        assert len(result) == 3


class TestFraudTraining:
    def test_full_train_pipeline(self):
        from ml.fraud.train import train
        np.random.seed(42)
        n = 500
        df = pd.DataFrame({
            "amount": np.random.exponential(200, n),
            "merchant_category": np.random.choice(["grocery", "electronics", "online"], n),
            "transaction_type": np.random.choice(["debit", "credit"], n),
            "is_fraud": np.random.choice([0, 1], n, p=[0.95, 0.05]),
        })
        model, scaler, metrics = train(df)
        assert metrics["roc_auc"] > 0.5
        assert "feature_names" in metrics


class TestChurnTraining:
    def test_full_churn_train(self):
        from ml.churn.train import train
        np.random.seed(42)
        n = 500
        df = pd.DataFrame({
            "credit_score": np.random.randint(300, 850, n),
            "age": np.random.randint(18, 80, n),
            "tenure": np.random.randint(0, 10, n),
            "balance": np.random.uniform(0, 200000, n),
            "num_products": np.random.randint(1, 4, n),
            "has_credit_card": np.random.randint(0, 2, n),
            "is_active_member": np.random.randint(0, 2, n),
            "estimated_salary": np.random.uniform(20000, 200000, n),
            "geography": np.random.choice(["Karachi", "Lahore"], n),
            "gender": np.random.choice(["Male", "Female"], n),
            "churned": np.random.choice([0, 1], n, p=[0.80, 0.20]),
        })
        model, rf, scaler, metrics = train(df)
        assert metrics["roc_auc"] > 0.5
