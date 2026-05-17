# NFL Betting System - Windows PowerShell Installation Script
# Run: Set-ExecutionPolicy Bypass -Scope Process; .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  NFL Betting System Installer (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Installation directory
$INSTALL_DIR = "$env:USERPROFILE\.nfl-betting"
$BIN_DIR = "$env:USERPROFILE\.local\bin"

Write-Host "Installation directory: $INSTALL_DIR"
Write-Host ""

# Check Python
function Check-Python {
    try {
        $version = python --version 2>&1
        Write-Host "[OK] $version" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[ERROR] Python not found. Install from https://python.org" -ForegroundColor Red
        return $false
    }
}

# Check Node.js
function Check-Node {
    try {
        $version = node --version 2>&1
        Write-Host "[OK] Node.js $version" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[WARN] Node.js not found. Frontend will not work." -ForegroundColor Yellow
        Write-Host "       Install from https://nodejs.org" -ForegroundColor Yellow
        return $false
    }
}

Write-Host "Checking dependencies..."
$pythonOk = Check-Python
$nodeOk = Check-Node

if (-not $pythonOk) {
    Write-Host "Please install Python 3.9+ and try again." -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host ""
Write-Host "Creating directories..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $BIN_DIR | Out-Null

# Copy files
Write-Host "Copying files..."
if (Test-Path ".git") {
    Copy-Item -Path ".\*" -Destination $INSTALL_DIR -Recurse -Force
}
else {
    Write-Host "Note: Please manually copy project files to $INSTALL_DIR" -ForegroundColor Yellow
}

Set-Location $INSTALL_DIR

# Create virtual environment
Write-Host ""
Write-Host "Creating Python virtual environment..."
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Python dependencies
Write-Host ""
Write-Host "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install fastapi uvicorn xgboost scikit-learn nfl-data-py duckdb

# Install frontend dependencies
if ($nodeOk) {
    Write-Host ""
    Write-Host "Installing frontend dependencies..."
    Set-Location frontend
    npm install
    Set-Location ..
}

# Create CLI batch file
Write-Host ""
Write-Host "Creating CLI command..."
$batchContent = @"
@echo off
call "$INSTALL_DIR\venv\Scripts\activate.bat"
python "$INSTALL_DIR\cli.py" %*
"@
Set-Content -Path "$BIN_DIR\nfl-betting.bat" -Value $batchContent

# Add to PATH
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$BIN_DIR*") {
    Write-Host ""
    Write-Host "Adding to PATH..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$BIN_DIR", "User")
    Write-Host "Note: Restart your terminal to use 'nfl-betting' command" -ForegroundColor Yellow
}

# Create Start Menu shortcut
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\NFL Betting Card.lnk")
$shortcut.TargetPath = "$BIN_DIR\nfl-betting.bat"
$shortcut.Arguments = "serve"
$shortcut.WorkingDirectory = $INSTALL_DIR
$shortcut.Description = "NFL Betting Predictions"
$shortcut.Save()

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Quick Start:" -ForegroundColor Cyan
Write-Host "  1. Open new PowerShell window (for PATH update)"
Write-Host ""
Write-Host "  2. Run the system:"
Write-Host "     nfl-betting run     # Full pipeline"
Write-Host "     nfl-betting serve   # Start API server"
Write-Host "     nfl-betting card    # Generate picks"
Write-Host ""
Write-Host "  3. Start frontend (in new terminal):"
Write-Host "     cd $INSTALL_DIR\frontend"
Write-Host "     npm run dev"
Write-Host ""
Write-Host "  4. Open browser:"
Write-Host "     http://localhost:3000"
Write-Host ""
Write-Host "For iOS/iPad PWA:" -ForegroundColor Cyan
Write-Host "  1. Open Safari on your device"
Write-Host "  2. Go to http://YOUR_PC_IP:3000"
Write-Host "  3. Tap Share -> Add to Home Screen"
Write-Host ""
