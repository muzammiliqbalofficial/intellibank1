"""
Generate sample datasets for testing and demo
Run: python data/sample/generate_sample_data.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)
OUTPUT_DIR = Path(__file__).parent

# ── Fraud / Transaction Data ──────────────────────────────────────────────────
def generate_transactions(n=5000):
    dates = pd.date_range("2023-01-01", "2024-12-31", periods=n)
    fraud_mask = np.random.choice([0, 1], n, p=[0.97, 0.03])
    amounts = np.where(fraud_mask == 1,
                       np.random.uniform(10000, 500000, n),
                       np.random.exponential(8000, n))
    df = pd.DataFrame({
        "transaction_ref": [f"TXN{i:07d}" for i in range(n)],
        "amount": amounts.round(2),
        "merchant_category": np.random.choice(
            ["grocery", "electronics", "travel", "online", "atm", "restaurant"], n),
        "transaction_type": np.random.choice(["debit", "credit", "transfer"], n),
        "location": np.random.choice(["karachi", "lahore", "islamabad", "peshawar"], n),
        "hour": np.random.randint(0, 24, n),
        "day_of_week": np.random.randint(0, 7, n),
        "is_weekend": np.random.randint(0, 2, n),
        "transaction_date": dates,
        "is_fraud": fraud_mask,
    })
    df.to_csv(OUTPUT_DIR / "sample_transactions.csv", index=False)
    print(f"Generated {n} transactions ({fraud_mask.sum()} fraudulent)")
    return df


# ── Customer / Churn Data ─────────────────────────────────────────────────────
def generate_customers(n=2000):
    df = pd.DataFrame({
        "customer_number": [f"C{i:06d}" for i in range(n)],
        "CreditScore": np.random.randint(300, 850, n),
        "Age": np.random.randint(18, 75, n),
        "Tenure": np.random.randint(0, 10, n),
        "Balance": np.random.uniform(0, 300000, n).round(2),
        "NumOfProducts": np.random.randint(1, 5, n),
        "HasCrCard": np.random.randint(0, 2, n),
        "IsActiveMember": np.random.randint(0, 2, n),
        "EstimatedSalary": np.random.uniform(30000, 500000, n).round(2),
        "Geography": np.random.choice(["Karachi", "Lahore", "Islamabad", "Peshawar"], n),
        "Gender": np.random.choice(["Male", "Female"], n),
        "Exited": np.random.choice([0, 1], n, p=[0.80, 0.20]),
    })
    df.to_csv(OUTPUT_DIR / "sample_customers.csv", index=False)
    print(f"Generated {n} customers ({df['Exited'].sum()} churned)")
    return df


# ── Revenue Data ──────────────────────────────────────────────────────────────
def generate_revenue(n_days=730):
    dates = pd.date_range("2022-01-01", periods=n_days, freq="D")
    trend = np.linspace(200000, 800000, n_days)
    seasonality = 80000 * np.sin(2 * np.pi * np.arange(n_days) / 365)
    weekly = 30000 * np.sin(2 * np.pi * np.arange(n_days) / 7)
    noise = np.random.normal(0, 20000, n_days)
    revenue = (trend + seasonality + weekly + noise).clip(min=50000)
    df = pd.DataFrame({"date": dates, "revenue": revenue.round(2)})
    df.to_csv(OUTPUT_DIR / "sample_revenue.csv", index=False)
    print(f"Generated {n_days} days of revenue data")
    return df


if __name__ == "__main__":
    generate_transactions()
    generate_customers()
    generate_revenue()
    print(f"\nSample data saved to {OUTPUT_DIR}")
