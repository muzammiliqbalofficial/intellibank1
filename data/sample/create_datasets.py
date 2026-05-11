"""
IntelliBank — Single Unified Banking Dataset Generator
Run: python data/sample/create_datasets.py

One file contains everything:
- Customer demographics
- Account info
- Transaction history
- Fraud labels
- Churn labels
- Revenue (aggregated from transactions)
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)
OUT = Path(__file__).parent

N_CUSTOMERS   = 500
TXN_PER_CUST  = 6      # avg transactions per customer → ~3000 rows total

print("Generating unified IntelliBank dataset...")

# ── Step 1: Customer base ─────────────────────────────────────────────────────
cust_ids    = [f"C{i:05d}" for i in range(1, N_CUSTOMERS + 1)]
ages        = np.random.randint(22, 70, N_CUSTOMERS)
tenures     = np.random.randint(0, 11, N_CUSTOMERS)
balances    = np.random.uniform(5000, 500000, N_CUSTOMERS).round(2)
salaries    = np.random.uniform(40000, 600000, N_CUSTOMERS).round(2)
products    = np.random.randint(1, 5, N_CUSTOMERS)
active      = np.random.randint(0, 2, N_CUSTOMERS)
credit      = np.random.randint(350, 850, N_CUSTOMERS)
genders     = np.random.choice(["Male", "Female"], N_CUSTOMERS, p=[0.55, 0.45])
cities      = np.random.choice(
    ["Karachi", "Lahore", "Islamabad", "Peshawar", "Quetta", "Multan"],
    N_CUSTOMERS, p=[0.30, 0.25, 0.20, 0.10, 0.08, 0.07]
)
branches    = np.where(cities == "Karachi",   "KHI-001",
              np.where(cities == "Lahore",    "LHR-001",
              np.where(cities == "Islamabad", "ISB-001",
              np.where(cities == "Peshawar",  "PEW-001",
              np.where(cities == "Quetta",    "QTA-001", "MUL-001")))))

# Churn logic: low balance + inactive + old + short tenure → high churn risk
churn_prob = (
    0.05
    + 0.18 * (ages        > 55).astype(float)
    + 0.20 * (balances    < 15000).astype(float)
    + 0.18 * (active      == 0).astype(float)
    + 0.12 * (tenures     < 2).astype(float)
    + 0.10 * (credit      < 500).astype(float)
    - 0.08 * (products    >= 3).astype(float)
)
churn_prob = np.clip(churn_prob, 0.03, 0.92)
is_churned = (np.random.rand(N_CUSTOMERS) < churn_prob).astype(int)

# ── Step 2: Expand to transaction rows ───────────────────────────────────────
rows = []
txn_counter = 1
start_date  = pd.Timestamp("2023-01-01")
end_date    = pd.Timestamp("2024-12-31")
date_range  = (end_date - start_date).days

for i in range(N_CUSTOMERS):
    n_txn = np.random.randint(3, TXN_PER_CUST * 2)

    for _ in range(n_txn):
        txn_date  = start_date + pd.Timedelta(days=int(np.random.rand() * date_range))
        hour      = int(np.random.choice(
            [0,1,2,3,22,23] if np.random.rand() < 0.05 else list(range(8, 22))
        ))
        dow       = txn_date.dayofweek
        is_wknd   = int(dow >= 5)

        # Fraud logic: large amount + odd hour + online/atm = fraud
        merch     = np.random.choice(
            ["grocery","electronics","travel","online","atm","restaurant","healthcare"],
            p=[0.22,0.13,0.10,0.22,0.15,0.13,0.05]
        )
        txn_type  = np.random.choice(["debit","credit","transfer","withdrawal"],
                                      p=[0.40,0.25,0.25,0.10])

        base_fraud = (
            0.01
            + 0.15 * (hour < 5 or hour >= 22)
            + 0.12 * (merch in ["online","atm"])
            + 0.08 * (is_wknd == 1)
        )
        is_fraud = int(np.random.rand() < min(base_fraud, 0.18))

        if is_fraud:
            amount = round(np.random.uniform(80000, 900000), 2)
        else:
            amount = round(np.random.exponential(12000) + 500, 2)

        rows.append({
            # ── Customer info ──────────────────────────────
            "customer_id":        cust_ids[i],
            "age":                int(ages[i]),
            "gender":             genders[i],
            "city":               cities[i],
            "branch_code":        branches[i],
            "credit_score":       int(credit[i]),
            "tenure_years":       int(tenures[i]),
            "account_balance":    float(balances[i]),
            "estimated_salary":   float(salaries[i]),
            "num_products":       int(products[i]),
            "has_credit_card":    int(np.random.randint(0, 2)),
            "is_active_member":   int(active[i]),
            "is_churned":         int(is_churned[i]),   # ← churn target
            # ── Transaction info ───────────────────────────
            "transaction_id":     f"TXN{txn_counter:07d}",
            "transaction_date":   txn_date.strftime("%Y-%m-%d"),
            "amount":             amount,
            "merchant_category":  merch,
            "transaction_type":   txn_type,
            "hour":               hour,
            "day_of_week":        int(dow),
            "is_weekend":         is_wknd,
            "is_fraud":           is_fraud,              # ← fraud target
        })
        txn_counter += 1

df = pd.DataFrame(rows).sort_values("transaction_date").reset_index(drop=True)

# ── Step 3: Save ──────────────────────────────────────────────────────────────
out_path = OUT / "intellibank_dataset.csv"
df.to_csv(out_path, index=False)

total     = len(df)
fraud_n   = df["is_fraud"].sum()
churn_n   = df[df.drop_duplicates("customer_id").index]["is_churned"].sum() if False else is_churned.sum()

print(f"\n✓ intellibank_dataset.csv")
print(f"  Rows        : {total:,}")
print(f"  Customers   : {N_CUSTOMERS:,}")
print(f"  Fraud txns  : {fraud_n:,}  ({fraud_n/total:.1%})")
print(f"  Churned     : {is_churned.sum():,}  ({is_churned.mean():.1%})")
print(f"  Date range  : 2023-01-01  →  2024-12-31")
print(f"\nColumns ({len(df.columns)}):")
print("  " + ",  ".join(df.columns.tolist()))
print(f"\nSaved to: {out_path}")
