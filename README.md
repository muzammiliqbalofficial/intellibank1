# IntelliBank

A banking intelligence dashboard for exploring risk, revenue, and customer behavior from one place, built with Streamlit and a Python API backend.

## What it does

- **Fraud Detection** — flags suspicious transactions using a trained classifier, with SHAP-based explanations for why each one was flagged
- **Customer Churn** — predicts which customers are likely to leave
- **Revenue Forecasting** — time-series forecasting (Prophet) over historical revenue
- **Branch Comparison** — side-by-side performance metrics across branches
- **NLP Query** — ask questions about the data in plain language (Groq-backed), with multi-language input support
- **Audit Trail** — a record of what was queried, flagged, or exported, and by whom
- **Data Upload** — bring in your own dataset to run the above against

## Stack

- **Frontend:** Streamlit
- **API:** Python (routes + middleware, JWT auth via `python-jose`, `bcrypt`)
- **ML:** scikit-learn, XGBoost, imbalanced-learn (fraud detection has to handle heavy class imbalance), Prophet, SHAP
- **Data:** pandas, SQLAlchemy + PostgreSQL
- **Exports:** reportlab (PDF reports), xlsxwriter/openpyxl (Excel)

## Running it locally

```bash
pip install -r requirements.txt
python setup.py      # quick setup/check script
streamlit run app/main.py
```

You'll need a PostgreSQL connection string and any relevant API keys in a `.env` file (see `pydantic-settings` config in the app for what's expected).
