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
    if not df.empty and "transaction_date" in df.columns and "amount" in df.columns:
        rev = (df.groupby("transaction_date")["amount"]
                 .sum()
                 .reset_index()
                 .rename(columns={"transaction_date": "date", "amount": "revenue"}))
        rev["date"] = pd.to_datetime(rev["date"])
        return rev.sort_values("date")
    snap = st.session_state.get("_snap_revenue", [])
    if snap:
        rev = pd.DataFrame(snap)
        rev["date"] = pd.to_datetime(rev["date"])
        return rev.sort_values("date")
    return pd.DataFrame()


def save_snapshot(filename: str, user_id: int = None):
    """Save aggregated stats to DB so other sessions (manager) can read them."""
    try:
        from db.connection import SessionLocal
        from db.models import DataSnapshot
        df       = get_dataset()
        summary  = get_summary().copy()
        rev_df   = get_revenue_df()
        br_df    = get_branch_df()

        # Store chart-level aggregations so other sessions can render charts
        if not df.empty:
            if "is_fraud" in df.columns and "merchant_category" in df.columns:
                fm = df[df["is_fraud"] == 1].groupby("merchant_category").size().reset_index(name="count")
                summary["_fraud_merchant"] = fm.to_dict("records")
            if "is_fraud" in df.columns and "transaction_date" in df.columns:
                dd = df.groupby("transaction_date")["is_fraud"].sum().reset_index()
                dd.columns = ["date", "count"]
                dd["date"] = dd["date"].astype(str)
                summary["_daily_fraud"] = dd.to_dict("records")
            if "is_churned" in df.columns and "city" in df.columns and "customer_id" in df.columns:
                cc = (df.drop_duplicates("customer_id")
                        .groupby("city")["is_churned"].mean() * 100).round(1).reset_index()
                cc.columns = ["city", "churn_rate"]
                summary["_churn_city"] = cc.to_dict("records")

        db = SessionLocal()
        db.query(DataSnapshot).delete()
        snap = DataSnapshot(
            uploaded_by  = user_id,
            filename     = filename,
            row_count    = summary.get("total_rows", 0),
            summary_json = summary,
            revenue_json = rev_df.assign(date=rev_df["date"].astype(str)).to_dict("records") if not rev_df.empty else [],
            branch_json  = br_df.to_dict("records") if not br_df.empty else [],
        )
        db.add(snap)
        db.commit()
        db.close()
    except Exception:
        pass


def load_snapshot() -> bool:
    """Load aggregated data from DB into session_state (for users without uploaded data)."""
    if is_data_loaded():
        return True
    try:
        from db.connection import SessionLocal
        from db.models import DataSnapshot
        db   = SessionLocal()
        snap = db.query(DataSnapshot).order_by(DataSnapshot.created_at.desc()).first()
        db.close()
        if snap and snap.summary_json:
            st.session_state["data_loaded"]          = True
            st.session_state["data_summary"]         = snap.summary_json
            st.session_state["_snap_revenue"]        = snap.revenue_json or []
            st.session_state["_snap_branch"]         = snap.branch_json or []
            st.session_state["_snap_only"]           = True
            st.session_state["_snap_fraud_merchant"] = snap.summary_json.get("_fraud_merchant", [])
            st.session_state["_snap_daily_fraud"]    = snap.summary_json.get("_daily_fraud", [])
            st.session_state["_snap_churn_city"]     = snap.summary_json.get("_churn_city", [])
            return True
    except Exception:
        pass
    return False


def get_branch_df() -> pd.DataFrame:
    df = get_dataset()
    if df.empty or "branch_code" not in df.columns:
        snap = st.session_state.get("_snap_branch", [])
        return pd.DataFrame(snap) if snap else pd.DataFrame()

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
