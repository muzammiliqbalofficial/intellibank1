from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, JSON, BigInteger, Date, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    BANK_MANAGER = "bank_manager"
    BUSINESS_ANALYST = "business_analyst"


class AlertType(str, enum.Enum):
    FRAUD = "fraud"
    CHURN = "churn"
    SYSTEM = "system"


class AlertChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBSOCKET = "websocket"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), nullable=False, default=UserRole.BUSINESS_ANALYST)
    is_active = Column(Boolean, default=True)
    preferred_language = Column(String(5), default="en")
    theme_preference = Column(String(10), default="light")
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    branch = relationship("Branch", back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    nlp_queries = relationship("NLPQuery", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    reports = relationship("Report", back_populates="generated_by_user")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="sessions")


class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    city = Column(String(100))
    region = Column(String(100))
    address = Column(Text)
    manager_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="branch")
    customers = relationship("Customer", back_populates="branch")
    accounts = relationship("Account", back_populates="branch")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_number = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    cnic = Column(String(15), unique=True)
    email = Column(String(120))
    phone = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(String(10))
    address = Column(Text)
    city = Column(String(100))
    branch_id = Column(Integer, ForeignKey("branches.id"))
    credit_score = Column(Integer)
    is_churned = Column(Boolean, default=False)
    churn_probability = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    branch = relationship("Branch", back_populates="customers")
    accounts = relationship("Account", back_populates="customer")
    prediction_logs = relationship("PredictionLog", back_populates="customer")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    account_type = Column(String(30))
    balance = Column(Float, default=0.0)
    currency = Column(String(3), default="PKR")
    is_active = Column(Boolean, default=True)
    opened_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="accounts")
    branch = relationship("Branch", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, index=True)
    transaction_ref = Column(String(50), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(30))
    merchant_category = Column(String(50))
    merchant_name = Column(String(100))
    location = Column(String(100))
    is_fraud = Column(Boolean, default=False)
    fraud_score = Column(Float)
    fraud_flagged_at = Column(DateTime(timezone=True))
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="transactions")
    fraud_alerts = relationship("FraudAlert", back_populates="transaction")

    __table_args__ = (
        Index("ix_transactions_date_account", "transaction_date", "account_id"),
    )


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(BigInteger, ForeignKey("transactions.id"), nullable=False, index=True)
    fraud_score = Column(Float, nullable=False)
    alert_type = Column(Enum(AlertType), default=AlertType.FRAUD)
    channels_notified = Column(JSON)
    shap_values = Column(JSON)
    top_features = Column(JSON)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transaction = relationship("Transaction", back_populates="fraud_alerts")


class NLPQuery(Base):
    __tablename__ = "nlp_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_query = Column(Text, nullable=False)
    detected_language = Column(String(5))
    translated_query = Column(Text)
    generated_sql = Column(Text)
    query_result = Column(JSON)
    result_row_count = Column(Integer)
    execution_time_ms = Column(Float)
    is_successful = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="nlp_queries")


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    model_type = Column(String(30), nullable=False)
    model_version = Column(String(20))
    input_features = Column(JSON)
    prediction = Column(Float, nullable=False)
    prediction_label = Column(String(50))
    confidence = Column(Float)
    shap_values = Column(JSON)
    top_features = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="prediction_logs")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    report_type = Column(String(50))
    format = Column(String(10))
    file_path = Column(String(500))
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_scheduled = Column(Boolean, default=False)
    parameters = Column(JSON)
    file_size_kb = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    generated_by_user = relationship("User", back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100))
    resource_id = Column(String(50))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    is_success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_date", "user_id", "created_at"),
        Index("ix_audit_logs_action", "action"),
    )


class DataSnapshot(Base):
    __tablename__ = "data_snapshots"

    id           = Column(Integer, primary_key=True, index=True)
    uploaded_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename     = Column(String(255))
    row_count    = Column(Integer)
    summary_json = Column(JSON)
    revenue_json = Column(JSON)
    branch_json  = Column(JSON)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(30), nullable=False, index=True)
    model_version = Column(String(20))
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    dataset_size = Column(Integer)
    drift_detected = Column(Boolean, default=False)
    drift_score = Column(Float)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
