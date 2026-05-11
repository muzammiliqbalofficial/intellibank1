"""
IntelliBank — Quick Setup Script
Run: python setup.py
"""
import os
import sys
import subprocess
import shutil


def run(cmd, desc=""):
    print(f"\n{'='*60}")
    print(f"  {desc or cmd}")
    print('='*60)
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║          IntelliBank — Setup & Initialization            ║
║          AI-Powered Banking Data Analyst                 ║
╚══════════════════════════════════════════════════════════╝
    """)

    # 1. Create .env from example
    if not os.path.exists(".env"):
        shutil.copy(".env.example", ".env")
        print("✓ Created .env from .env.example — please fill in your credentials")
    else:
        print("✓ .env already exists")

    # 2. Install dependencies
    if not run("pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # 3. Create artifact directories
    os.makedirs("ml/fraud/artifacts", exist_ok=True)
    os.makedirs("ml/churn/artifacts", exist_ok=True)
    os.makedirs("ml/forecast/artifacts", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    print("✓ Created model artifact directories")

    # 4. Train models with demo data
    print("\n→ Training ML models with demo data (this takes ~2 minutes)...")
    run("python ml/fraud/train.py", "Training Fraud Detection (XGBoost)")
    run("python ml/churn/train.py", "Training Churn Prediction (RF + LR)")
    run("python ml/forecast/train.py", "Training Revenue Forecast (Prophet)")

    # 5. Seed demo user (if DB available)
    print("\n→ Attempting to seed demo user...")
    seed_script = """
import sys
sys.path.insert(0, '.')
try:
    from db.connection import init_db, SessionLocal
    from services.auth_service import AuthService
    from db.models import UserRole
    init_db()
    db = SessionLocal()
    try:
        AuthService.create_user(db, 'admin', 'admin@intellibank.com',
                                'admin123', 'System Admin', UserRole.ADMIN)
        AuthService.create_user(db, 'manager', 'manager@intellibank.com',
                                'manager123', 'Bank Manager', UserRole.BANK_MANAGER)
        AuthService.create_user(db, 'analyst', 'analyst@intellibank.com',
                                'analyst123', 'Business Analyst', UserRole.BUSINESS_ANALYST)
        print('Demo users created: admin/admin123, manager/manager123, analyst/analyst123')
    except Exception as e:
        print(f'Seed skipped (users may exist): {e}')
    finally:
        db.close()
except Exception as e:
    print(f'DB not available, skipping seed: {e}')
"""
    result = subprocess.run([sys.executable, "-c", seed_script], capture_output=True, text=True)
    print(result.stdout)

    print("""
╔══════════════════════════════════════════════════════════╗
║                   Setup Complete!                        ║
╠══════════════════════════════════════════════════════════╣
║  Start Streamlit:  streamlit run app/main.py            ║
║  Start API:        uvicorn api.main:app --reload        ║
║  Run Docker:       docker-compose up                     ║
║  Run Tests:        pytest                                ║
║                                                          ║
║  Demo Login:       admin / admin123                      ║
╚══════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
