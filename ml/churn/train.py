"""
Customer Churn Prediction — Random Forest + Logistic Regression ensemble
Dataset: Kaggle Bank Customer Churn (Telco-style banking dataset)
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, roc_auc_score,
                              average_precision_score, confusion_matrix,
                              roc_curve, precision_recall_curve)
from imblearn.over_sampling import SMOTE
import joblib
import json
from pathlib import Path

MODEL_DIR = Path(__file__).parent / "artifacts"
MODEL_DIR.mkdir(exist_ok=True)

CHURN_FEATURES = [
    "credit_score", "age", "tenure", "balance", "num_products",
    "has_credit_card", "is_active_member", "estimated_salary",
    "geography_encoded", "gender_encoded",
    "balance_salary_ratio", "products_per_year",
]


def preprocess(df: pd.DataFrame):
    df = df.copy()

    # Standard feature mapping (Kaggle-style column names)
    col_map = {
        "CreditScore": "credit_score",
        "Age": "age",
        "Tenure": "tenure",
        "Balance": "balance",
        "NumOfProducts": "num_products",
        "HasCrCard": "has_credit_card",
        "IsActiveMember": "is_active_member",
        "EstimatedSalary": "estimated_salary",
        "Geography": "geography",
        "Gender": "gender",
        "Exited": "churned",
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    # IntelliBank dataset alternative column names
    if "balance"   not in df.columns and "account_balance" in df.columns:
        df["balance"] = df["account_balance"]
    if "tenure"    not in df.columns and "tenure_years"    in df.columns:
        df["tenure"] = df["tenure_years"]
    if "geography" not in df.columns and "city"            in df.columns:
        df["geography"] = df["city"]
    if "churned"   not in df.columns and "is_churned"      in df.columns:
        df["churned"] = df["is_churned"]

    # Fill nulls
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        df[col].fillna(df[col].median(), inplace=True)

    # Encode categoricals
    if "geography" in df.columns:
        le = LabelEncoder()
        df["geography_encoded"] = le.fit_transform(df["geography"].astype(str))
        joblib.dump(le, MODEL_DIR / "geography_encoder.pkl")
    else:
        df["geography_encoded"] = 0

    if "gender" in df.columns:
        df["gender_encoded"] = (df["gender"].str.lower() == "male").astype(int)
    else:
        df["gender_encoded"] = 0

    # Feature engineering — safe fallbacks if columns missing
    bal = df["balance"]           if "balance"          in df.columns else pd.Series(0,        index=df.index)
    sal = df["estimated_salary"]  if "estimated_salary" in df.columns else pd.Series(1,        index=df.index)
    ten = df["tenure"]            if "tenure"           in df.columns else pd.Series(1,        index=df.index)
    prd = df["num_products"]      if "num_products"     in df.columns else pd.Series(1,        index=df.index)

    df["balance_salary_ratio"] = bal / (sal + 1)
    df["products_per_year"]    = prd / (ten + 1)

    return df


def train(df: pd.DataFrame, target_col: str = "churned"):
    df = preprocess(df)

    feature_cols = [c for c in CHURN_FEATURES if c in df.columns]
    X = df[feature_cols].fillna(0)
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_res)
    X_test_scaled = scaler.transform(X_test)

    rf = RandomForestClassifier(
        n_estimators=200, max_depth=10, min_samples_split=5,
        class_weight="balanced", random_state=42, n_jobs=-1
    )
    lr = LogisticRegression(
        C=1.0, class_weight="balanced", max_iter=1000, random_state=42
    )

    # Soft voting ensemble
    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("lr", lr)],
        voting="soft",
        weights=[0.7, 0.3],
    )
    ensemble.fit(X_train_scaled, y_train_res)

    y_pred = ensemble.predict(X_test_scaled)
    y_prob = ensemble.predict_proba(X_test_scaled)[:, 1]

    # ROC curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    step = max(1, len(fpr) // 60)
    roc_data = {"fpr": fpr[::step].tolist(), "tpr": tpr[::step].tolist()}

    # Precision-Recall curve
    prec, rec, _ = precision_recall_curve(y_test, y_prob)
    step2 = max(1, len(prec) // 60)
    pr_data = {"precision": prec[::step2].tolist(), "recall": rec[::step2].tolist()}

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)

    metrics = {
        "roc_auc":               float(roc_auc_score(y_test, y_prob)),
        "avg_precision":         float(average_precision_score(y_test, y_prob)),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
        "confusion_matrix":      cm.tolist(),
        "roc_curve":             roc_data,
        "pr_curve":              pr_data,
        "feature_names":         feature_cols,
        "n_train":               len(X_train),
        "n_test":                len(X_test),
        "n_train_after_smote":   len(X_train_res),
        "test_churn_count":      int(y_test.sum()),
        "test_loyal_count":      int((y_test == 0).sum()),
    }

    print(f"Churn Model — ROC-AUC: {metrics['roc_auc']:.4f} | Avg Precision: {metrics['avg_precision']:.4f}")

    joblib.dump(ensemble, MODEL_DIR / "churn_model.pkl")
    joblib.dump(scaler, MODEL_DIR / "churn_scaler.pkl")
    with open(MODEL_DIR / "churn_features.json", "w") as f:
        json.dump(feature_cols, f)
    with open(MODEL_DIR / "churn_metrics.json", "w") as f:
        json.dump(metrics, f)

    # Save RF separately for SHAP
    rf.fit(X_train_scaled, y_train_res)
    joblib.dump(rf, MODEL_DIR / "churn_rf_model.pkl")

    return ensemble, scaler, metrics


def load_model():
    model = joblib.load(MODEL_DIR / "churn_model.pkl")
    rf_model = joblib.load(MODEL_DIR / "churn_rf_model.pkl")
    scaler = joblib.load(MODEL_DIR / "churn_scaler.pkl")
    with open(MODEL_DIR / "churn_features.json") as f:
        features = json.load(f)
    return model, rf_model, scaler, features


if __name__ == "__main__":
    np.random.seed(42)
    n = 10000
    df = pd.DataFrame({
        "credit_score": np.random.randint(300, 850, n),
        "age": np.random.randint(18, 80, n),
        "tenure": np.random.randint(0, 10, n),
        "balance": np.random.uniform(0, 250000, n),
        "num_products": np.random.randint(1, 5, n),
        "has_credit_card": np.random.randint(0, 2, n),
        "is_active_member": np.random.randint(0, 2, n),
        "estimated_salary": np.random.uniform(20000, 200000, n),
        "geography": np.random.choice(["Karachi", "Lahore", "Islamabad"], n),
        "gender": np.random.choice(["Male", "Female"], n),
        "churned": np.random.choice([0, 1], n, p=[0.80, 0.20]),
    })
    train(df)
