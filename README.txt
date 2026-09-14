========================================================================
                      INTELLIBANK — INSTALLATION GUIDE
========================================================================

Project Title: IntelliBank: AI-Powered Banking Data Analyst
Department: Computer Science & Software Engineering (Iqra University)
Supervisor: Engr. Sidra Rehman

This document provides step-by-step instructions to install, configure, 
and run the IntelliBank application locally on Windows, macOS, or Linux.

------------------------------------------------------------------------
1. SYSTEM PREREQUISITES
------------------------------------------------------------------------
Before setting up the project, make sure you have the following installed:
* Python 3.9 or higher (Recommended: Python 3.10 or 3.11)
  Download link: https://www.python.org/downloads/
* Pip (Python Package Installer, usually comes with Python)
* Internet Connection (required for the first installation of packages)

------------------------------------------------------------------------
2. INSTALLATION PROCEDURES
------------------------------------------------------------------------
Follow these steps to install the system dependencies:

Step 1: Extract the zip file containing the project source code.
Step 2: Open your Terminal / Command Prompt (cmd) and navigate to the 
        extracted project folder:
        
        cd path/to/IntelliBank

Step 3: Install all required Python packages by running the following command:

        pip install -r requirements.txt

Wait until all packages are successfully downloaded and installed.

------------------------------------------------------------------------
3. RUNNING THE APPLICATION
------------------------------------------------------------------------
IntelliBank runs on a two-tier architecture (FastAPI Backend + Streamlit Frontend). 
You must start BOTH services in separate terminal windows:

--- TERMINAL 1 (FastAPI Backend Service) ---
1. Open a terminal and navigate to the project root folder.
2. Run the following command to start the FastAPI server:

   python backend/main.py

   * By default, the backend API will run on http://localhost:8000

--- TERMINAL 2 (Streamlit Frontend Dashboard) ---
1. Open a NEW separate terminal window and navigate to the project root folder.
2. Run the following command to launch the dashboard:

   streamlit run app.py

   * This will compile and automatically open the application in your 
     default web browser (typically on http://localhost:8501)

------------------------------------------------------------------------
4. SYSTEM ACCESS CREDENTIALS (DEMO LOGIN)
------------------------------------------------------------------------
The system has role-based access controls. To test the three distinct 
user dashboards, log in using the following credentials:

* Role 1: System Administrator
  - Username: admin
  - Password: admin123

* Role 2: Bank Manager (Executive View)
  - Username: manager
  - Password: manager123

* Role 3: Business Analyst (Predictive Modeling Hub)
  - Username: analyst
  - Password: analyst123

------------------------------------------------------------------------
5. PROJECT STRUCTURE & DATABASE
------------------------------------------------------------------------
* database.db: Relational SQLite database (pre-populated with 10,000+ 
  customer records and transaction entries). No database server installation 
  or configuration (PostgreSQL/MySQL) is required.
* models/ folder: Contains pre-trained XGBoost and Random Forest binary 
  pickles for fraud and churn predictions.
* app.py: Core Streamlit frontend controller.
* backend/main.py: FastAPI REST endpoint server.

========================================================================
For technical support or issues, please contact the development team.
========================================================================
