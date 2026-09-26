# IntelliBank: AI-Powered Banking Data Analyst

**Department:** Computer Science & Software Engineering (Iqra University)  
**Supervisor:** Engr. Sidra Rehman  

---

## Project Overview
IntelliBank is an AI-powered banking intelligence dashboard offering fraud detection, customer churn prediction, revenue forecasting, branch comparison, and role-based analytics.

---

## System Prerequisites
* Python 3.9+ (Recommended: Python 3.10 or 3.11)
* Pip
* Node.js & npm (for React/Vite frontend)

---

## Installation & Setup

```bash
pip install -r requirements.txt
cd frontend
npm install
npm run dev
```

## Running the Application

IntelliBank uses a FastAPI backend with Streamlit / Vite frontend components.

```bash
python backend/main.py
```

Backend: `http://localhost:8000`

```bash
streamlit run app.py
```

Dashboard: `http://localhost:8501`

---

## Demo Credentials (Local Development Only)

> **Security notice:** The accounts below are intentionally weak **demo credentials for the local academic project only**. They must never be reused for a public or production deployment. A real deployment should replace them with proper authentication, hashed credentials, secret management, and server-side authorization.

| Role | Username | Password | Permissions / View |
| :--- | :--- | :--- | :--- |
| **System Administrator** | admin | admin123 | Full access, user management, audit logs |
| **Bank Manager** | manager | manager123 | Executive view & summary dashboards |
| **Business Analyst** | analyst | analyst123 | Predictive modeling hub & ML insights |

---

## Project Structure
* `app.py`: Core Streamlit frontend controller
* `backend/main.py`: FastAPI REST endpoint server
* `database.db`: SQLite database with pre-populated demo records
* `data_preprocessing.py`: Data ingestion and DB preparation
* `models/`: Pre-trained XGBoost and Random Forest models for fraud & churn predictions
* `frontend/`: React + Vite frontend dashboard
