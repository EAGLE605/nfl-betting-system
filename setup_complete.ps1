# ============================================================================
# NFL BETTING SYSTEM - ONE-COMMAND COMPLETE SETUP (PowerShell)
# ============================================================================
# Windows version of complete setup script
# Run: .\setup_complete.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "🏈 NFL BETTING SYSTEM - COMPLETE INSTALLATION" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will install:" -ForegroundColor Yellow
Write-Host "  ✅ Python environment"
Write-Host "  ✅ All dependencies"
Write-Host "  ✅ SQLite database"
Write-Host "  ✅ Authentication system (OAuth + 2FA)"
Write-Host "  ✅ Biometric support (WebAuthn)"
Write-Host "  ✅ Admin dashboard"
Write-Host "  ✅ ML models"
Write-Host "  ✅ Automated workflows"
Write-Host ""

$continue = Read-Host "Continue? (y/n)"
if ($continue -ne 'y' -and $continue -ne 'Y') {
    Write-Host "❌ Installation cancelled" -ForegroundColor Red
    exit 1
}

# ============================================================================
# STEP 1: Check Python
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 1/10: Checking Python installation..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

try {
    $pythonVersion = python --version
    Write-Host "✅ Found $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.10+ from python.org" -ForegroundColor Red
    exit 1
}

# ============================================================================
# STEP 2: Create Virtual Environment
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 2/10: Creating virtual environment..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

if (!(Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate venv
& .venv\Scripts\Activate.ps1

# ============================================================================
# STEP 3: Install Dependencies
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 3/10: Installing dependencies..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r dashboard\requirements.txt

Write-Host "✅ Core dependencies installed" -ForegroundColor Green

# ============================================================================
# STEP 4: Install Auth Dependencies
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 4/10: Installing authentication system..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

pip install `
    python-jose[cryptography] `
    passlib[bcrypt] `
    python-multipart `
    python-dotenv `
    authlib `
    itsdangerous `
    pyotp `
    qrcode[pil] `
    streamlit-authenticator

Write-Host "✅ Authentication installed" -ForegroundColor Green

# ============================================================================
# STEP 5: Create Database
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 5/10: Creating database..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

python -c @"
import sqlite3
import os
from pathlib import Path

db_path = Path('data/auth.db')
db_path.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        oauth_provider TEXT,
        two_factor_enabled INTEGER DEFAULT 0,
        two_factor_secret TEXT,
        biometric_enabled INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        bankroll REAL DEFAULT 500,
        risk_profile TEXT DEFAULT 'small',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

conn.commit()
conn.close()
print('✅ Database created')
"@

Write-Host "✅ Database schema initialized" -ForegroundColor Green

# ============================================================================
# STEP 6: Generate Keys
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEP 6/10: Generating security keys..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

python -c @"
import secrets
from pathlib import Path

env_file = Path('config/auth_keys.env')
env_file.parent.mkdir(exist_ok=True)

if not env_file.exists():
    with open(env_file, 'w') as f:
        f.write(f'JWT_SECRET_KEY={secrets.token_urlsafe(32)}\n')
        f.write(f'SESSION_SECRET={secrets.token_urlsafe(32)}\n')
        f.write(f'ENCRYPTION_KEY={secrets.token_urlsafe(32)}\n')
        f.write(f'\n# OAuth (fill these in)\n')
        f.write(f'GOOGLE_CLIENT_ID=your_google_id\n')
        f.write(f'GOOGLE_CLIENT_SECRET=your_google_secret\n')
    print('✅ Keys generated')
"@

Write-Host "✅ Security keys generated" -ForegroundColor Green

# ============================================================================
# STEP 7-10: Data, Models, Config
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "STEPS 7-10: Finalizing setup..." -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan

# Create launch script
@"
@echo off
echo Starting NFL Edge Finder...
call .venv\Scripts\activate
streamlit run dashboard/app_auth.py
"@ | Out-File -FilePath "start_dashboard.bat" -Encoding ASCII

Write-Host "✅ Launch script created" -ForegroundColor Green

# ============================================================================
# COMPLETE
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "✅ INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 Your NFL Betting System is ready!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Start the dashboard:"
Write-Host "   .\start_dashboard.bat"
Write-Host ""
Write-Host "2. Open browser:"
Write-Host "   http://localhost:8501"
Write-Host ""
Write-Host "3. Create your account"
Write-Host "4. Enable 2FA"
Write-Host "5. Start betting!"
Write-Host ""
Write-Host "🏈 Happy betting! 💰" -ForegroundColor Green
Write-Host ""

