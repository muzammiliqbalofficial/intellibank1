import sqlite3
import bcrypt
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")

def init_clean_db():
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Tables
    cursor.executescript('''
        CREATE TABLE Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT
        );
        CREATE TABLE Branches (
            branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_name TEXT,
            location TEXT,
            region TEXT
        );
        CREATE TABLE Customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT,
            tenure INTEGER,
            estimated_salary REAL,
            credit_score INTEGER,
            churn INTEGER
        );
        CREATE TABLE Accounts (
            account_number INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            type_of_account TEXT,
            balance REAL,
            FOREIGN KEY(customer_id) REFERENCES Customers(customer_id)
        );
        CREATE TABLE Transactions (
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

    # Seed Admin Users
    hashed_pw = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute("INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', hashed_pw, 'System Administrator'))
    hashed_pw_m = bcrypt.hashpw('manager123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute("INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)", ('manager', hashed_pw_m, 'Bank Manager'))
    hashed_pw_a = bcrypt.hashpw('analyst123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute("INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)", ('analyst', hashed_pw_a, 'Business Analyst'))

    # Seed Branches
    branches = [
        ('Clifton Branch', 'Karachi', 'South'),
        ('DHA Branch', 'Karachi', 'South'),
        ('Gulberg Branch', 'Lahore', 'Central'),
        ('Model Town Branch', 'Lahore', 'Central'),
        ('Blue Area Branch', 'Islamabad', 'North'),
        ('F-8 Branch', 'Islamabad', 'North')
    ]
    cursor.executemany("INSERT INTO Branches (branch_name, location, region) VALUES (?, ?, ?)", branches)

    conn.commit()
    conn.close()
    print("Database Initialized (Empty State for Dynamic Uploads).")

if __name__ == "__main__":
    init_clean_db()
