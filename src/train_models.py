import sqlite3
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from prophet import Prophet

# Paths
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")
models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

if not os.path.exists(models_dir):
    os.makedirs(models_dir)

def train_churn_model(conn):
    print("Training Customer Churn Prediction Model (Random Forest)...")
    # Fetch Data
    query = """
    SELECT age, gender, tenure, estimated_salary, credit_score, balance, type_of_account, churn
    FROM Customers
    LEFT JOIN Accounts ON Customers.customer_id = Accounts.customer_id
    """
    df = pd.read_sql_query(query, conn)
    
    # Fill missing values (if any due to joins)
    df['balance'] = df['balance'].fillna(0)
    df['type_of_account'] = df['type_of_account'].fillna('Savings')
    
    # Encoding categorical variables
    df = pd.get_dummies(df, columns=['gender', 'type_of_account'], drop_first=True)
    
    X = df.drop('churn', axis=1)
    y = df['churn']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale numerical features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Train Random Forest
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train_scaled, y_train)
    
    # Save model and scaler
    with open(os.path.join(models_dir, 'churn_rf_model.pkl'), 'wb') as f:
        pickle.dump({'model': rf_model, 'scaler': scaler, 'features': X.columns.tolist()}, f)
    
    print("Churn Model Trained and Saved!")


def train_fraud_model(conn):
    print("Training Fraud Detection Model (XGBoost + SMOTE)...")
    # Fetch Data
    query = """
    SELECT amount, category, step, is_fraud 
    FROM Transactions
    """
    df = pd.read_sql_query(query, conn)
    
    # Encoding categorical variable 'category'
    df = pd.get_dummies(df, columns=['category'], drop_first=True)
    
    X = df.drop('is_fraud', axis=1)
    y = df['is_fraud']
    
    # Handle Class Imbalance with SMOTE
    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X, y)
    
    X_train, X_test, y_train, y_test = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42)
    
    # Train XGBoost
    xgb_model = XGBClassifier(eval_metric='logloss', random_state=42)
    xgb_model.fit(X_train, y_train)
    
    with open(os.path.join(models_dir, 'fraud_xgb_model.pkl'), 'wb') as f:
        pickle.dump({'model': xgb_model, 'features': X.columns.tolist()}, f)
    
    print("Fraud Detection Model Trained and Saved!")


def train_revenue_model(conn):
    print("Training Revenue Forecasting Model (Facebook Prophet)...")
    # Fetch total daily transaction volumes
    query = """
    SELECT step, sum(amount) as total_amount
    FROM Transactions
    WHERE is_fraud = 0
    GROUP BY step
    """
    df = pd.read_sql_query(query, conn)
    
    # Prophet requires 'ds' (Date) and 'y' (Target)
    # Since BankSim only has 'step' (days 0 to 180), we convert step to dates starting from 2023-01-01
    start_date = pd.to_datetime('2023-01-01')
    df['ds'] = start_date + pd.to_timedelta(df['step'], unit='D')
    df['y'] = df['total_amount']
    df = df[['ds', 'y']]
    
    prophet_model = Prophet()
    prophet_model.fit(df)
    
    with open(os.path.join(models_dir, 'revenue_prophet_model.pkl'), 'wb') as f:
        pickle.dump(prophet_model, f)
        
    print("Revenue Forecasting Model Trained and Saved!")

def main():
    conn = sqlite3.connect(db_path)
    train_churn_model(conn)
    train_fraud_model(conn)
    train_revenue_model(conn)
    conn.close()
    print("All Phase 2 Operations Completed Successfully!")

if __name__ == "__main__":
    main()
