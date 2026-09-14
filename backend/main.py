from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import pandas as pd
import bcrypt
import pickle
import os
import json

app = FastAPI(title="IntelliBank API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")
models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(req: LoginRequest):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, role FROM Users WHERE username=?", (req.username,))
    record = cursor.fetchone()
    conn.close()
    if record and bcrypt.checkpw(req.password.encode('utf-8'), record[0].encode('utf-8')):
        return {"success": True, "role": record[1], "username": req.username}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/stats")
def get_stats():
    conn = sqlite3.connect(db_path)
    try:
        customers = pd.read_sql("SELECT COUNT(*) FROM Customers", conn).iloc[0,0]
        branches = pd.read_sql("SELECT COUNT(*) FROM Branches", conn).iloc[0,0]
        transactions = pd.read_sql("SELECT COUNT(*) FROM Transactions", conn).iloc[0,0]
        return {"customers": int(customers), "branches": int(branches), "transactions": int(transactions)}
    except Exception as e:
        return {"customers": 0, "branches": 0, "transactions": 0}
    finally:
        conn.close()

@app.post("/api/upload")
async def upload_file(table: str, file: UploadFile = File(...)):
    if table not in ["Transactions", "Customers", "Accounts"]:
        raise HTTPException(status_code=400, detail="Invalid table")
    try:
        df = pd.read_csv(file.file)
        conn = sqlite3.connect(db_path)
        df.to_sql(table, conn, if_exists='append', index=False)
        conn.close()
        return {"success": True, "message": f"Successfully uploaded {len(df)} records to {table}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fraud")
def get_fraud_data():
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql("""
            SELECT t.trans_id, b.branch_name, t.amount, t.category, t.step, t.is_fraud
            FROM Transactions t JOIN Branches b ON t.branch_id = b.branch_id
            ORDER BY t.trans_id DESC LIMIT 500
        """, conn)
        
        if df.empty:
            return {"data": [], "stats": {"total": 0, "alerts": 0}}
            
        model_path = os.path.join(models_dir, 'fraud_xgb_model.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            X_inf = df[['amount', 'category', 'step']]
            X_inf = pd.get_dummies(X_inf, columns=['category'], drop_first=True)
            for col in model_data['features']:
                if col not in X_inf.columns:
                    X_inf[col] = 0
            X_inf = X_inf[model_data['features']]
            df['risk_score'] = model_data['model'].predict_proba(X_inf)[:, 1] * 100
        else:
            df['risk_score'] = df['is_fraud'] * 100
            
        alerts = int(len(df[df['risk_score'] > 70]))
        return {
            "data": df.to_dict(orient="records"),
            "stats": {"total": len(df), "alerts": alerts}
        }
    except Exception as e:
        return {"error": str(e), "data": [], "stats": {"total": 0, "alerts": 0}}
    finally:
        conn.close()

@app.get("/api/churn")
def get_churn_data():
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql("""
            SELECT c.customer_id, c.name, c.age, c.tenure, a.balance, c.churn, c.gender, c.estimated_salary, c.credit_score, a.type_of_account
            FROM Customers c LEFT JOIN Accounts a ON c.customer_id = a.customer_id LIMIT 500
        """, conn)
        if df.empty:
            return {"data": [], "stats": {"high_risk": 0}}
        
        df['balance'] = df['balance'].fillna(0)
        df['type_of_account'] = df['type_of_account'].fillna('Savings')
        model_path = os.path.join(models_dir, 'churn_rf_model.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            X_inf = df[['age', 'gender', 'tenure', 'estimated_salary', 'credit_score', 'balance', 'type_of_account']]
            X_inf = pd.get_dummies(X_inf, columns=['gender', 'type_of_account'], drop_first=True)
            for col in model_data['features']:
                if col not in X_inf.columns:
                    X_inf[col] = 0
            X_inf = X_inf[model_data['features']]
            X_scaled = model_data['scaler'].transform(X_inf)
            df['churn_risk'] = model_data['model'].predict_proba(X_scaled)[:, 1] * 100
        else:
            df['churn_risk'] = df['churn'] * 100
            
        high_risk = int(len(df[df['churn_risk'] > 60]))
        return {"data": df[['name', 'age', 'tenure', 'balance', 'churn_risk']].to_dict(orient="records"), "stats": {"high_risk": high_risk}}
    except Exception as e:
        return {"error": str(e), "data": [], "stats": {"high_risk": 0}}
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
