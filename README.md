# IntelliBank: AI-Powered Banking Data Analyst

**Department:** Computer Science & Software Engineering (Iqra University)  
**Supervisor:** Engr. Sidra Rehman  

---

## Project Overview
IntelliBank is an AI-powered banking intelligence dashboard offering fraud detection, customer churn prediction, revenue forecasting, branch comparison, and role-based analytics.

---

## System Prerequisites
* Python 3.9+ (Recommended: Python 3.10 or 3.11)
* Pip (Python Package Installer)
* Node.js & npm (for React/Vite frontend)

---

## Installation & Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Frontend Setup (React / Vite)
```bash
cd frontend
npm install
npm run dev
```

---

## Running the Application

IntelliBank runs on a two-tier architecture (FastAPI Backend + Streamlit / Vite Frontend).

### Terminal 1: FastAPI Backend
```bash
python backend/main.py
```
> Backend runs at http://localhost:8000

### Terminal 2: Streamlit Dashboard
```bash
streamlit run app.py
```
> Dashboard runs at http://localhost:8501

---

## Demo Credentials (Role-Based Access)

| Role | Username | Password | Permissions / View |
| :--- | :--- | :--- | :--- |
| **System Administrator** | admin | admin123 | Full access, user management, audit logs |
| **Bank Manager** | manager | manager123 | Executive view & summary dashboards |
| **Business Analyst** | analyst | analyst123 | Predictive modeling hub & ML insights |

---

## Project Structure
* app.py: Core Streamlit frontend controller
* backend/main.py: FastAPI REST endpoint server
* database.db: Relational SQLite database with pre-populated records
* data_preprocessing.py: Data ingestion and DB preparation script
* models/: Pre-trained XGBoost and Random Forest binary models for fraud & churn predictions
* frontend/: React + Vite frontend dashboard
