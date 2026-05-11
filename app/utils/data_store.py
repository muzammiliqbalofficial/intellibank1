"""
Central data store — uploaded dataset shared across all Streamlit pages
via st.session_state so every page reads the same real data.
"""
import pandas as pd
import numpy as np
import streamlit as st


def save_dataset(df: pd.DataFrame):
    st.session_state["uploaded_df"]     = df
    st.session_state["data_loaded"]     = True
    st.session_state["data_summary"]    = _compute_summary(df)


def get_dataset() -> pd.DataFrame:
    return st.session_state.get("uploaded_df", pd.DataFrame())


def is_data_loaded() -> bool:
    return st.session_state.get("data_loaded", False)


def get_summary() -> dict:
    return st.session_state.get("data_summary", {})


def _compute_summary(df: pd.DataFrame) -> dict:
    s = {}
    s["total_rows"]       = len(df)
    s["total_customers"]  = df["customer_id"].nunique()  if "customer_id"       in df.columns else 0
    s["total_branches"]   = df["branch_code"].nunique()  if "branch_code"       in df.columns else 0

    if "amount" in df.columns:
        s["total_revenue"]    = round(df["amount"].sum(), 2)
        s["avg_transaction"]  = round(df["amount"].mean(), 2)

    if "is_fraud" in df.columns:
        s["fraud_count"]      = int(df["is_fraud"].sum())
        s["fraud_rate"]       = round(df["is_fraud"].mean() * 100, 2)

    if "is_churned" in df.columns:
        cust_df               = df.drop_duplicates("customer_id") if "customer_id" in df.columns else df
        s["churned_count"]    = int(cust_df["is_churned"].sum())
        s["churn_rate"]       = round(cust_df["is_churned"].mean() * 100, 2)

    if "transaction_date" in df.columns:
        dates                 = pd.to_datetime(df["transaction_date"])
        s["date_from"]        = str(dates.min().date())
        s["date_to"]          = str(dates.max().date())

    if "branch_code" in df.columns and "amount" in df.columns:
        branch_rev            = df.groupby("branch_code")["amount"].sum().sort_values(ascending=False)
        s["top_branch"]       = branch_rev.index[0]
        s["top_branch_rev"]   = round(float(branch_rev.iloc[0]), 2)

    return s


def get_fraud_df() -> pd.DataFrame:
    df = get_dataset()
    if df.empty:
        return pd.DataFrame()
    cols = ["amount", "merchant_category", "transaction_type",
            "hour", "day_of_week", "is_weekend", "is_fraud"]
    return df[[c for c in cols if c in df.columns]].copy()


def get_churn_df() -> pd.DataFrame:
    df = get_dataset()
    if df.empty:
        return pd.DataFrame()
    if "customer_id" not in df.columns:
        return df
    cust_cols = ["customer_id", "age", "gender", "city", "branch_code",
                 "credit_score", "tenure_years", "account_balance",
                 "estimated_salary", "num_products", "has_credit_card",
                 "is_active_member", "is_churned"]
    return df.drop_duplicates("customer_id")[[c for c in cust_cols if c in df.columns]].copy()


def get_revenue_df() -> pd.DataFrame:
    df = get_dataset()
    if df.empty or "transaction_date" not in df.columns or "amount" not in df.columns:
        return pd.DataFrame()
    rev = (df.groupby("transaction_date")["amount"]
             .sum()
             .reset_index()
             .rename(columns={"transaction_date": "date", "amount": "revenue"}))
    rev["date"] = pd.to_datetime(rev["date"])
    return rev.sort_values("date")


def get_branch_df() -> pd.DataFrame:
    df = get_dataset()
    if df.empty or "branch_code" not in df.columns:
        return pd.DataFrame()

    grp = df.groupby("branch_code").agg(
        total_revenue   = ("amount",       "sum"),
        transactions    = ("transaction_id","count"),
        fraud_count     = ("is_fraud",      "sum"),
        customers       = ("customer_id",   "nunique"),
        avg_balance     = ("account_balance","mean"),
    ).reset_index()

    grp["fraud_rate_pct"] = (grp["fraud_count"] / grp["transactions"] * 100).round(2)
    grp["total_revenue"]  = grp["total_revenue"].round(2)
    grp["avg_balance"]    = grp["avg_balance"].round(2)

    if "is_churned" in df.columns:
        churn_by_branch = (df.drop_duplicates("customer_id")
                             .groupby("branch_code")["is_churned"]
                             .mean() * 100).round(2).reset_index()
        churn_by_branch.columns = ["branch_code", "churn_rate_pct"]
        grp = grp.merge(churn_by_branch, on="branch_code", how="left")

    return grp
