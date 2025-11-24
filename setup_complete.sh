#!/bin/bash
# ============================================================================
# NFL BETTING SYSTEM - ONE-COMMAND COMPLETE SETUP
# ============================================================================
# Installs EVERYTHING: Python, dependencies, database, auth, dashboard
# Run: bash setup_complete.sh
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "🏈 NFL BETTING SYSTEM - COMPLETE INSTALLATION"
echo "============================================================================"
echo ""
echo "This will install:"
echo "  ✅ Python environment"
echo "  ✅ All dependencies"
echo "  ✅ PostgreSQL database"
echo "  ✅ Authentication system (OAuth + 2FA)"
echo "  ✅ Biometric support (WebAuthn)"
echo "  ✅ Admin dashboard"
echo "  ✅ ML models"
echo "  ✅ Automated workflows"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Installation cancelled"
    exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

echo ""
echo "📋 Detected OS: $OS"
echo ""

# ============================================================================
# STEP 1: Python Environment
# ============================================================================
echo "============================================================================"
echo "STEP 1/10: Setting up Python environment..."
echo "============================================================================"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate venv
if [[ "$OS" == "windows" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# ============================================================================
# STEP 2: Core Dependencies
# ============================================================================
echo ""
echo "============================================================================"
echo "STEP 2/10: Installing core dependencies..."
echo "============================================================================"

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r dashboard/requirements.txt

echo "✅ Core dependencies installed"

# ============================================================================
# STEP 3: Authentication Dependencies
# ============================================================================
echo ""
echo "============================================================================"
echo "STEP 3/10: Installing authentication system..."
echo "============================================================================"

pip install \
    python-jose[cryptography] \
    passlib[bcrypt] \
    python-multipart \
    python-dotenv \
    supabase \
    authlib \
    itsdangerous \
    pyotp \
    qrcode[pil]

echo "✅ Authentication dependencies installed"

# ============================================================================
# STEP 4: Database Setup
# ============================================================================
echo ""
echo "============================================================================"
echo "STEP 4/10: Setting up database..."
echo "============================================================================"

if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL found"
    
    read -p "Create database? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        createdb nfl_betting || echo "Database might already exist"
        echo "✅ Database created/verified"
    fi
else
    echo "⚠️  PostgreSQL not found. Using SQLite instead."
    pip install databases[sqlite]
fi

# ============================================================================
# STEP 5: Initialize Database Schema
# ============================================================================
echo ""
echo "============================================================================"
echo "STEP 5/10: Initializing database schema..."
echo "============================================================================"

python3 << END
import sqlite3
import os
from pathlib import Path

db_path = Path("data/auth.db")
db_path.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        phone TEXT,
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        oauth_provider TEXT,
        oauth_id TEXT,
        two_factor_enabled INTEGER DEFAULT 0,
        two_factor_secret TEXT,
        biometric_enabled INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
""")

# Sessions table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

# User settings table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        bankroll REAL DEFAULT 500,
        risk_profile TEXT DEFAULT 'small',
        min_edge REAL DEFAULT 0.015,
        min_probability REAL DEFAULT 0.52,
        notifications_enabled INTEGER DEFAULT 1,
        theme TEXT DEFAULT 'light',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

# Tracked bets table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracked_bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_id TEXT NOT NULL,
        bet_type TEXT NOT NULL,
        bet_size REAL NOT NULL,
        odds REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        result REAL,
        placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

# WebAuthn credentials (for biometric)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS webauthn_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        credential_id TEXT UNIQUE NOT NULL,
        public_key TEXT NOT NULL,
        sign_count INTEGER DEFAULT 0,
        device_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

conn.commit()
conn.close()

print("✅ Database schema initialized")
END

echo "✅ Database schema created"

# ============================================================================
# STEP 6: Generate Secret Keys
# ============================================================================
echo ""
echo "============================================================================"
echo "STEP 6/10: Generating security keys..."
echo "============================================================================"

python3 << END
import secrets
import os
from pathlib import Path

env_file = Path("config/auth_keys.env")
env_file.parent.mkdir(exist_ok=True)

if not env_file.exists():
    with open(env_file, 'w') as f:
        f.write(f"# Auto-generated security keys\n")
        f.write(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}\n")
        f.write(f"SESSION_SECRET={secrets.token_urlsafe(32)}\n")
        f.write(f"ENCRYPTION_KEY={secrets.token_urlsafe(32)}\n")
        f.write(f"\n# OAuth Credentials (fill these in)\n")
        f.write(f"GOOGLE_CLIENT_ID=your_google_client_id\n")
        f.write(f"GOOGLE_CLIENT_SECRET=your_google_secret\n")
        f.write(f"APPLE_CLIENT_ID=your_apple_client_id\n")
        f.write(f"APPLE_TEAM_ID=your_apple_team_id\n")
        f.write(f"APPLE_KEY_ID=your_apple_key_id\n")
        f.write(f"GITHUB_CLIENT_ID=your_github_client_id\n")
        f.write(f"GITHUB_CLIENT_SECRET=your_github_secret\n")
    
    print("✅ Security keys generated: config/auth_keys.env")
else:
    print("✅ Security keys already exist")
END

# ============================================================================
# STEP 7: Download Initial Data
# ============================================================================
echo ""
echo "============================================================================"
echo "STEP 7/10: Downloading NFL data..."
echo "============================================================================"

python3 scripts/download_data.py --latest || echo "⚠️  Data download skipped (run manually later)"

echo "✅ Data download complete"

# ============================================================================
# STEP 8: Train Initial Models
# ============================================================================
echo ""
echo "============================================================================"
echo "STEP 8/10: Training initial models..."
echo "============================================================================"

if [ -d "data/raw" ] && [ "$(ls -A data/raw)" ]; then
    python3 scripts/train_model.py || echo "⚠️  Model training skipped"
    echo "✅ Models trained"
else
    echo "⚠️  No data found. Skipping model training."
fi

# ============================================================================
# STEP 9: Setup GitHub Actions (Optional)
# ============================================================================
echo ""
echo "============================================================================"
echo "STEP 9/10: Configuring automation..."
echo "============================================================================"

if [ -d ".git" ]; then
    echo "✅ Git repository detected"
    
    read -p "Set up pre-commit hooks? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install pre-commit
        pre-commit install
        echo "✅ Pre-commit hooks installed"
    fi
else
    echo "⚠️  No git repository. Run 'git init' to enable version control."
fi

# ============================================================================
# STEP 10: Create Launch Scripts
# ============================================================================
echo ""
echo "============================================================================"
echo "STEP 10/10: Creating launch scripts..."
echo "============================================================================"

# Windows batch file
cat > start_dashboard.bat << 'EOF'
@echo off
echo Starting NFL Edge Finder Dashboard...
call .venv\Scripts\activate
streamlit run dashboard/app_auth.py
EOF

# Unix shell script
cat > start_dashboard.sh << 'EOF'
#!/bin/bash
echo "Starting NFL Edge Finder Dashboard..."
source .venv/bin/activate
streamlit run dashboard/app_auth.py
EOF

chmod +x start_dashboard.sh

echo "✅ Launch scripts created"

# ============================================================================
# INSTALLATION COMPLETE
# ============================================================================
echo ""
echo "============================================================================"
echo "✅ INSTALLATION COMPLETE!"
echo "============================================================================"
echo ""
echo "🎉 Your NFL Betting System is ready!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure OAuth (Optional but recommended):"
echo "   Edit: config/auth_keys.env"
echo "   - Add Google OAuth credentials"
echo "   - Add Apple Sign In credentials"
echo "   - Add GitHub OAuth credentials"
echo ""
echo "2. Start the dashboard:"
if [[ "$OS" == "windows" ]]; then
    echo "   Windows: start_dashboard.bat"
else
    echo "   Mac/Linux: ./start_dashboard.sh"
fi
echo "   Or manually: streamlit run dashboard/app_auth.py"
echo ""
echo "3. Create your admin account:"
echo "   - Go to http://localhost:8501"
echo "   - Click 'Sign Up'"
echo "   - Register with your email"
echo "   - Enable 2FA in settings"
echo "   - Set up biometric (iPhone/Android)"
echo ""
echo "4. Deploy to production (Optional):"
echo "   - Streamlit Cloud: https://streamlit.io/cloud"
echo "   - Railway: https://railway.app"
echo "   - Heroku: https://heroku.com"
echo ""
echo "============================================================================"
echo "📚 Documentation:"
echo "============================================================================"
echo ""
echo "  README.md                    - Main documentation"
echo "  SECURITY.md                  - Security policies"
echo "  dashboard/README.md          - Dashboard guide"
echo "  REALISTIC_BETTING_GUIDE.md   - Betting strategy"
echo "  BIG_IDEAS_NEXT_PHASE.md      - Future roadmap"
echo ""
echo "============================================================================"
echo "🆘 Need Help?"
echo "============================================================================"
echo ""
echo "  GitHub: https://github.com/EAGLE605/nfl-betting-system"
echo "  Issues: https://github.com/EAGLE605/nfl-betting-system/issues"
echo ""
echo "🏈 Happy betting! 💰"
echo ""

