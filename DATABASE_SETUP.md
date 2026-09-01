# TRANSLARA — Microsoft SQL Server (MSSQL) Integration & Production Guide

This guide details how to configure, migrate, seed, and run **TRANSLARA** with **Microsoft SQL Server (MSSQL)** as the primary application database.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                 │
│   • Communicates ONLY with FastAPI Backend via REST/WS      │
│   • Zero database credentials exposed on client             │
│   • VITE_API_BASE_URL=http://localhost:8000                 │
│   • VITE_WS_BASE_URL=ws://localhost:8000                    │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON & WebSockets
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Port 8000)               │
│   • Pydantic Settings (.env configuration)                  │
│   • JWT Authentication & Native Bcrypt Password Hashing     │
│   • SQLAlchemy Session Pooling (pool_pre_ping=True)         │
│   • AI Pipeline (ASR, NMT, TTS, VAD, Entity Lock)           │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
                ▼                             ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│   MSSQL Primary Database    │ │   Local SQLite Cache        │
│ • Users, Roles, JWT         │ │ • Offline Classroom Phrases │
│ • Translation History       │ │ • Emergency Fallback Store  │
│ • Chat Sessions & Messages  │ └─────────────────────────────┘
│ • Video Jobs & Worksheets   │
│ • Registered Indian Langs   │
└─────────────────────────────┘
```

---

## 2. Prerequisites & Installation on Windows

### Step 1: Install Microsoft SQL Server
1. Download **SQL Server 2022 Developer or Express Edition** from [Microsoft SQL Server Downloads](https://www.microsoft.com/en-us/sql-server/sql-server-downloads).
2. Choose **Basic Installation** or **Custom Installation**.
3. During setup, select **Mixed Mode Authentication** (SQL Server authentication and Windows authentication) and specify a strong password for the `sa` account (e.g. `YourStrong@Passw0rd`).

### Step 2: Install SQL Server Management Studio (SSMS)
Download and install [SQL Server Management Studio (SSMS)](https://learn.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms).

### Step 3: Install Microsoft ODBC Driver 18 for SQL Server
SQLAlchemy connects to SQL Server via `pyodbc` using the official Microsoft ODBC driver:
- Download and install **[Microsoft ODBC Driver 18 for SQL Server (x64)](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)**.
*(Note: TRANSLARA also supports `ODBC Driver 17 for SQL Server` if already present).*

To verify available ODBC drivers on your machine, run in PowerShell:
```powershell
python -c "import pyodbc; print(pyodbc.drivers())"
```

### Step 4: Enable TCP/IP in SQL Server Configuration Manager
1. Open **SQL Server Configuration Manager**.
2. Expand **SQL Server Network Configuration** → **Protocols for MSSQLSERVER** (or your instance name).
3. Ensure **TCP/IP** is set to **Enabled**.
4. Double click **TCP/IP** → **IP Addresses** tab → Scroll to **IPAll** → Set **TCP Port** to `1433`.
5. Restart the **SQL Server** service.

---

## 3. Database Creation & User Setup

Open **SQL Server Management Studio (SSMS)**, connect to your server (`localhost`), open a new query window, and execute:

```sql
-- 1. Create TRANSLARA Database with UTF-8 Collation support
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'TRANSLARA')
BEGIN
    CREATE DATABASE TRANSLARA COLLATE Latin1_General_100_CI_AS_SC_UTF8;
END
GO

USE TRANSLARA;
GO

-- 2. Create Dedicated Application Login and User (Optional if using sa)
IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = 'translara_user')
BEGIN
    CREATE LOGIN translara_user WITH PASSWORD = 'YourStrong@Passw0rd', CHECK_POLICY = ON;
END
GO

IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = 'translara_user')
BEGIN
    CREATE USER translara_user FOR LOGIN translara_user;
    ALTER ROLE db_owner ADD MEMBER translara_user;
END
GO
```

---

## 4. Environment Configuration

### Backend Environment (`backend/.env`)

Copy `backend/.env.example` to `backend/.env`:
```powershell
cp backend/.env.example backend/.env
```

Set your MSSQL credentials in `backend/.env`:
```ini
APP_NAME=TRANSLARA
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

HOST=127.0.0.1
PORT=8000

# Microsoft SQL Server (MSSQL) Connection
DB_SERVER=localhost
DB_PORT=1433
DB_NAME=TRANSLARA
DB_USER=sa
DB_PASSWORD=YourStrong@Passw0rd
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUST_SERVER_CERTIFICATE=true

DATABASE_URL=mssql+pyodbc://sa:YourStrong%40Passw0rd@localhost:1433/TRANSLARA?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes

# JWT Authentication
JWT_SECRET_KEY=translara_production_secret_key_change_in_env_2026_sih
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

AI_MODEL_DIR=./models
DATA_DIR=./data
MOCK_MODE=false
DEMO_MODE=false
```

### Frontend Environment (`frontend/.env`)

Copy `frontend/.env.example` to `frontend/.env`:
```powershell
cp frontend/.env.example frontend/.env
```

```ini
VITE_APP_NAME=TRANSLARA
VITE_APP_ENV=development
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

> [!CRITICAL]
> **Zero Database Credentials in Frontend**: The frontend communicates **only** with the FastAPI backend API via `VITE_API_BASE_URL`. Never put MSSQL connection strings or passwords in `frontend/.env`.

---

## 5. Python Dependency Installation

Install the required Python packages:
```powershell
pip install -r backend/requirements.txt
```

---

## 6. Database Migrations (Alembic) & Seeding

### Run Alembic Migrations
To apply the initial schema to Microsoft SQL Server:
```powershell
# From the project root:
alembic upgrade head
```

To create new autogenerated migrations in the future:
```powershell
alembic revision --autogenerate -m "add new field"
alembic upgrade head
```

### Seed Initial Languages & Classroom Vocabulary
Populate standard Indian languages (Tamil, Malayalam, Telugu, Kannada, Hindi, Santhali, Ho, Mundari, etc.) and classroom phrases:
```powershell
python -m backend.database.seed
```

---

## 7. Starting the Application

### Start Backend API Server
Execute from the project root:
```powershell
python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
```

Or execute from the `backend/` directory:
```powershell
cd backend
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

### Start Frontend Dev Server
In a separate terminal:
```powershell
cd frontend
npm run dev
```

---

## 8. Verifying the System

### 1. Health Check
```powershell
curl http://127.0.0.1:8000/health
```
Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "ai_engine": "ready",
  "app_name": "TRANSLARA",
  "version": "1.0.0",
  "mock_mode": false,
  "demo_mode": false
}
```

### 2. Language Registry
```powershell
curl http://127.0.0.1:8000/api/languages
```

### 3. User Registration & Login
```powershell
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{"name":"Teacher Anand","email":"anand@school.edu","password":"TeacherPassword123!","role":"teacher","preferred_source_lang":"ta","preferred_target_lang":"ml"}'

# Login
curl -X POST http://127.0.0.1:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"anand@school.edu","password":"TeacherPassword123!"}'
```

### 4. Translation & History Logging
```powershell
curl -X POST http://127.0.0.1:8000/api/translate `
  -H "Content-Type: application/json" `
  -d '{"text":"வணக்கம் மாணவர்களே","source_language":"ta","target_language":"ml"}'
```

### 5. Run Automated Test Suite
```powershell
python -m pytest backend/tests/test_mssql_database.py backend/tests/test_api_endpoints.py -v
```

---

## 9. Troubleshooting & FAQ

### Q: `Login failed for user 'sa'` (Error 18456)
- **Cause**: SQL Server Authentication is disabled or incorrect password.
- **Fix**: Open SSMS → Right click Server instance → Properties → Security → Select **SQL Server and Windows Authentication mode** → Restart SQL Server service.

### Q: `SSL Provider: [error:0A000086:SSL routines:tls_post_process_server_certificate:certificate verify failed]`
- **Cause**: ODBC Driver 18 defaults to strict encryption and requires trusted certificates.
- **Fix**: Ensure `TrustServerCertificate=yes` is included in the connection string and `DB_TRUST_SERVER_CERTIFICATE=true` in `backend/.env`.

### Q: `Can't open lib 'ODBC Driver 18 for SQL Server'`
- **Cause**: Driver not installed or named differently.
- **Fix**: Run `python -c "import pyodbc; print(pyodbc.drivers())"`. If you have `ODBC Driver 17 for SQL Server`, set `DB_DRIVER=ODBC Driver 17 for SQL Server` in `backend/.env`.

### Q: Does TRANSLARA work offline if MSSQL is unreachable?
- **Yes**: If MSSQL is not running during local development, TRANSLARA gracefully logs a notice and switches to the local SQLite phrase store and AI model pipeline without crashing the server.
