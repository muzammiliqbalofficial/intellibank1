"""
XGBoost Fraud Detection Model
Dataset: BankSim / European Credit Card Dataset (Kaggle)
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (classification_report, confusion_matrix,
                              roc_auc_score, precision_recall_curve, average_precision_score)
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import joblib
import json
import os
from pathlib import Path

MODEL_DIR = Path(__file__).parent / "artifacts"
MODEL_DIR.mkdir(exist_ok=True)


def preprocess(df: pd.DataFrame):
    df = df.copy()

    # Drop columns with too many nulls or irrelevant
    drop_cols = [c for c in ["transaction_ref", "merchant_name", "created_at"] if c in df.columns]
    df.drop(columns=drop_cols, inplace=True)

    # Fill missing
    num_cols = df.select_dtypes(include=[np.number]).columns
    cat_cols = df.select_dtypes(include=["object"]).columns

    for col in num_cols:
        df[col].fillna(df[col].mean(), inplace=True)

    # Label encode categoricals (excluding target)
    le = LabelEncoder()
    for col in cat_cols:
        if col != "is_fraud":
            df[col] = le.fit_transform(df[col].astype(str))

    # Feature engineering
    if "amount" in df.columns:
        df["log_amount"] = np.log1p(df["amount"])
        df["amount_zscore"] = (df["amount"] - df["amount"].mean()) / (df["amount"].std() + 1e-8)

    if "transaction_date" in df.columns:
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        df["hour"] = df["transaction_date"].dt.hour
        df["day_of_week"] = df["transaction_date"].dt.dayofweek
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df.drop(columns=["transaction_date"], inplace=True)

    return df


def train(df: pd.DataFrame, target_col: str = "is_fraud"):
    df = preprocess(df)

    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # SMOTE oversampling for class imbalance
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)

    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_res)
    X_test_scaled = scaler.transform(X_test)

    # XGBoost with class weight
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        use_label_encoder=False,
        eval_metric="aucpr",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train_scaled, y_train_res,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False,
    )

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "avg_precision": float(average_precision_score(y_test, y_prob)),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
        "feature_names": feature_cols,
        "n_train": len(X_train_res),
        "n_test": len(X_test),
    }

    print(f"Fraud Model — ROC-AUC: {metrics['roc_auc']:.4f} | Avg Precision: {metrics['avg_precision']:.4f}")

    # Save artifacts
    joblib.dump(model, MODEL_DIR / "fraud_model.pkl")
    joblib.dump(scaler, MODEL_DIR / "fraud_scaler.pkl")
    with open(MODEL_DIR / "fraud_features.json", "w") as f:
        json.dump(feature_cols, f)
    with open(MODEL_DIR / "fraud_metrics.json", "w") as f:
        json.dump({k: v for k, v in metrics.items() if k != "classification_report"}, f)

    return model, scaler, metrics


def load_model():
    model = joblib.load(MODEL_DIR / "fraud_model.pkl")
    scaler = joblib.load(MODEL_DIR / "fraud_scaler.pkl")
    with open(MODEL_DIR / "fraud_features.json") as f:
        features = json.load(f)
    return model, scaler, features


if __name__ == "__main__":
    # Demo training with synthetic data
    np.random.seed(42)
    n = 50000
    df = pd.DataFrame({
        "amount": np.random.exponential(200, n),
        "merchant_category": np.random.choice(["grocery", "electronics", "travel", "online", "atm"], n),
        "location": np.random.choice(["karachi", "lahore", "islamabad", "peshawar"], n),
        "transaction_type": np.random.choice(["debit", "credit", "transfer"], n),
        "is_fraud": np.random.choice([0, 1], n, p=[0.97, 0.03]),
    })
    train(df)
