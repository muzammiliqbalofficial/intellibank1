-- IntelliBank PostgreSQL Schema
-- Run this to initialize the database

CREATE DATABASE intellibank_db;
\c intellibank_db;

-- Create application user
CREATE USER intellibank_user WITH ENCRYPTED PASSWORD 'strongpassword';
GRANT ALL PRIVILEGES ON DATABASE intellibank_db TO intellibank_user;
GRANT ALL ON SCHEMA public TO intellibank_user;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fast text search

-- Create types
CREATE TYPE user_role AS ENUM ('admin', 'bank_manager', 'business_analyst');
CREATE TYPE alert_type AS ENUM ('fraud', 'churn', 'system');

-- Tables are auto-created by SQLAlchemy init_db()
-- This file is for manual/reference setup

-- Sample seed data
INSERT INTO branches (name, code, city, region, address, manager_name) VALUES
('Karachi Main Branch', 'KHI-001', 'Karachi', 'Sindh', 'I.I. Chundrigar Road, Karachi', 'Ahmed Khan'),
('Lahore Central', 'LHR-001', 'Lahore', 'Punjab', 'Mall Road, Lahore', 'Sara Malik'),
('Islamabad Capital', 'ISB-001', 'Islamabad', 'Federal', 'Blue Area, Islamabad', 'Usman Ali'),
('Peshawar Branch', 'PEW-001', 'Peshawar', 'KPK', 'GT Road, Peshawar', 'Nadia Rehman'),
('Quetta Branch', 'QTA-001', 'Quetta', 'Balochistan', 'Zarghoon Road, Quetta', 'Tariq Baloch');
