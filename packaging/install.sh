#!/bin/bash
# NFL Betting System - Unix/Mac Installation Script
# Run: curl -sSL https://raw.githubusercontent.com/.../install.sh | bash

set -e

echo "=========================================="
echo "  NFL Betting System Installer"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
        echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
        PYTHON_CMD="python"
    else
        echo -e "${RED}✗${NC} Python not found. Please install Python 3.9+"
        exit 1
    fi
}

# Check Node.js
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION found"
    else
        echo -e "${YELLOW}!${NC} Node.js not found. Frontend will not work."
        echo "   Install from: https://nodejs.org/"
    fi
}

# Install directory
INSTALL_DIR="${HOME}/.nfl-betting"
BIN_DIR="${HOME}/.local/bin"

echo "Installation directory: $INSTALL_DIR"
echo ""

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Clone or copy files
if [ -d ".git" ]; then
    echo "Copying from current directory..."
    cp -r . "$INSTALL_DIR/"
else
    echo "Downloading from repository..."
    git clone https://github.com/EAGLE605/nfl-betting-system.git "$INSTALL_DIR" 2>/dev/null || {
        echo "Note: Git clone failed. Please manually copy files."
    }
fi

cd "$INSTALL_DIR"

# Check dependencies
echo ""
echo "Checking dependencies..."
check_python
check_node

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies
pip install fastapi uvicorn xgboost scikit-learn nfl-data-py duckdb

# Install frontend dependencies
if command -v npm &> /dev/null; then
    echo ""
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Create CLI wrapper
echo ""
echo "Creating CLI command..."
cat > "$BIN_DIR/nfl-betting" << 'EOF'
#!/bin/bash
INSTALL_DIR="${HOME}/.nfl-betting"
source "$INSTALL_DIR/venv/bin/activate"
python "$INSTALL_DIR/cli.py" "$@"
EOF
chmod +x "$BIN_DIR/nfl-betting"

# Create desktop entry (Linux)
if [ -d "${HOME}/.local/share/applications" ]; then
    cat > "${HOME}/.local/share/applications/nfl-betting.desktop" << EOF
[Desktop Entry]
Name=NFL Betting Card
Comment=NFL Betting Predictions
Exec=$BIN_DIR/nfl-betting serve
Icon=$INSTALL_DIR/frontend/public/icon-192.png
Terminal=false
Type=Application
Categories=Utility;
EOF
fi

# Add to PATH if needed
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}Note:${NC} Add this to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$PATH:$BIN_DIR\""
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Quick Start:"
echo "  1. Activate environment:"
echo "     source $INSTALL_DIR/venv/bin/activate"
echo ""
echo "  2. Run the system:"
echo "     nfl-betting run     # Full pipeline"
echo "     nfl-betting serve   # Start API server"
echo "     nfl-betting card    # Generate picks"
echo ""
echo "  3. Start frontend (in new terminal):"
echo "     cd $INSTALL_DIR/frontend"
echo "     npm run dev"
echo ""
echo "  4. Open browser:"
echo "     http://localhost:3000"
echo ""
echo "For iOS/iPad PWA:"
echo "  1. Open Safari on your device"
echo "  2. Go to http://YOUR_IP:3000"
echo "  3. Tap Share -> Add to Home Screen"
echo ""
