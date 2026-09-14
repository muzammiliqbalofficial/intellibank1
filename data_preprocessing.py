import pandas as pd
import sqlite3
import numpy as np
import random
import os

# Paths
raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

def main():
    print("Connecting to SQLite Database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Create Tables
    print("Creating tables...")
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT
        );
        CREATE TABLE IF NOT EXISTS Branches (
            branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_name TEXT,
            location TEXT,
            region TEXT
        );
        CREATE TABLE IF NOT EXISTS Customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT,
            tenure INTEGER,
            estimated_salary REAL,
            credit_score INTEGER,
            churn INTEGER
        );
        CREATE TABLE IF NOT EXISTS Accounts (
            account_number INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            type_of_account TEXT,
            balance REAL,
            FOREIGN KEY(customer_id) REFERENCES Customers(customer_id)
        );
        CREATE TABLE IF NOT EXISTS Transactions (
            trans_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            branch_id INTEGER,
            amount REAL,
            category TEXT,
            step INTEGER,
            is_fraud INTEGER,
            FOREIGN KEY(account_id) REFERENCES Accounts(account_number),
            FOREIGN KEY(branch_id) REFERENCES Branches(branch_id)
        );
    ''')

    # 2. Insert Branches (Pakistani context as per thesis)
    print("Populating Branches...")
    branches = [
        ('Clifton Branch', 'Karachi', 'South'),
        ('DHA Branch', 'Karachi', 'South'),
        ('Gulberg Branch', 'Lahore', 'Central'),
        ('Model Town Branch', 'Lahore', 'Central'),
        ('Blue Area Branch', 'Islamabad', 'North'),
        ('F-8 Branch', 'Islamabad', 'North')
    ]
    cursor.executemany("INSERT OR IGNORE INTO Branches (branch_name, location, region) VALUES (?, ?, ?)", branches)
    conn.commit()
    
    # Get branch IDs
    branch_ids = [row[0] for row in cursor.execute("SELECT branch_id FROM Branches").fetchall()]

    # 3. Process Customers (From Churn Dataset)
    print("Processing Customers...")
    churn_df = pd.read_csv(os.path.join(raw_data_dir, "Bank Customer Churn Prediction.csv"))
    
    # We map Kaggle data to our schema
    customers_data = churn_df[['customer_id', 'age', 'gender', 'tenure', 'estimated_salary', 'credit_score', 'churn']].copy()
    customers_data['name'] = ['Customer_' + str(i) for i in range(len(customers_data))]
    
    customers_data.to_sql('Customers', conn, if_exists='replace', index=False)
    
    # 4. Create Accounts for Customers
    print("Processing Accounts...")
    # Drop existing if we run multiple times to avoid duplicates
    cursor.execute("DELETE FROM Accounts")
    
    accounts_data = []
    account_id_counter = 100000
    for _, row in churn_df.iterrows():
        customer_id = row['customer_id']
        balance = row['balance']
        accounts_data.append((account_id_counter, customer_id, random.choice(['Savings', 'Current']), balance))
        account_id_counter += 1
        
    cursor.executemany("INSERT INTO Accounts (account_number, customer_id, type_of_account, balance) VALUES (?, ?, ?, ?)", accounts_data)
    conn.commit()

    account_ids = [row[0] for row in cursor.execute("SELECT account_number FROM Accounts").fetchall()]

    # 5. Process Transactions (From BankSim)
    print("Processing Transactions...")
    cursor.execute("DELETE FROM Transactions")
    
    # BankSim has 600k rows, we take ~50k for smooth prototype performance
    banksim_df = pd.read_csv(os.path.join(raw_data_dir, "bs140513_032310.csv"))
    
    fraud_df = banksim_df[banksim_df['fraud'] == 1]
    normal_df = banksim_df[banksim_df['fraud'] == 0].sample(n=45000, random_state=42)
    
    tx_df = pd.concat([fraud_df, normal_df]).sample(frac=1).reset_index(drop=True)
    
    # Link Transactions to our unified Accounts and Branches
    tx_df['account_id'] = np.random.choice(account_ids, size=len(tx_df))
    tx_df['branch_id'] = np.random.choice(branch_ids, size=len(tx_df))
    
    tx_to_db = tx_df[['account_id', 'branch_id', 'amount', 'category', 'step', 'fraud']].copy()
    tx_to_db.rename(columns={'fraud': 'is_fraud'}, inplace=True)
    
    tx_to_db.to_sql('Transactions', conn, if_exists='append', index=False)
    
    print("Database processing complete! DB Saved at:", db_path)
    conn.close()

if __name__ == "__main__":
    main()
