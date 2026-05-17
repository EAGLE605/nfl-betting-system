# Building Windows MSI Installer

This guide explains how to create a Windows MSI installer for the NFL Betting System.

## Prerequisites

1. Windows 10/11 or Windows Server
2. Python 3.11+ installed
3. WiX Toolset v4 or later (https://wixtoolset.org/)
4. Node.js 18+ installed

## Option 1: Using PyInstaller + WiX

### Step 1: Install PyInstaller
```powershell
pip install pyinstaller
```

### Step 2: Create Executable
```powershell
cd nfl-betting-system
pyinstaller --name "NFLBetting" --onefile --windowed cli.py
```

### Step 3: Create WiX Project
Create `installer.wxs`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <Package Name="NFL Betting System"
           Manufacturer="EAGLE605"
           Version="1.0.0"
           UpgradeCode="YOUR-GUID-HERE">
    
    <MajorUpgrade DowngradeErrorMessage="A newer version is already installed." />
    
    <Feature Id="Main">
      <ComponentGroupRef Id="ProductComponents" />
    </Feature>
    
    <StandardDirectory Id="ProgramFilesFolder">
      <Directory Id="INSTALLFOLDER" Name="NFL Betting System">
        <Component Id="MainExecutable">
          <File Source="dist\NFLBetting.exe" />
        </Component>
      </Directory>
    </StandardDirectory>
    
  </Package>
</Wix>
```

### Step 4: Build MSI
```powershell
wix build installer.wxs -o NFLBetting-1.0.0.msi
```

## Option 2: Using NSIS (Simpler)

### Step 1: Install NSIS
Download from https://nsis.sourceforge.io/

### Step 2: Create Installer Script
Create `installer.nsi`:
```nsis
!define PRODUCT_NAME "NFL Betting System"
!define PRODUCT_VERSION "1.0.0"

OutFile "NFLBetting-Setup.exe"
InstallDir "$PROGRAMFILES\NFL Betting System"

Section "Install"
  SetOutPath $INSTDIR
  File /r "dist\*.*"
  File /r "frontend\dist\*.*"
  File /r "data\*.*"
  
  CreateShortCut "$DESKTOP\NFL Betting.lnk" "$INSTDIR\NFLBetting.exe"
  CreateShortCut "$SMPROGRAMS\NFL Betting System\NFL Betting.lnk" "$INSTDIR\NFLBetting.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\*.*"
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\NFL Betting.lnk"
  Delete "$SMPROGRAMS\NFL Betting System\NFL Betting.lnk"
SectionEnd
```

### Step 3: Build Installer
```powershell
makensis installer.nsi
```

## Option 3: Portable ZIP (Simplest)

For users who don't need an installer:

```powershell
# Create portable distribution
mkdir NFLBetting-Portable
xcopy /E /I dist NFLBetting-Portable\
xcopy /E /I frontend\dist NFLBetting-Portable\web
xcopy /E /I models NFLBetting-Portable\models

# Create start script
echo "@echo off" > NFLBetting-Portable\start.bat
echo "start python -m http.server 3000 --directory web &" >> NFLBetting-Portable\start.bat
echo "NFLBetting.exe serve --port 8000" >> NFLBetting-Portable\start.bat

# Zip it
Compress-Archive -Path NFLBetting-Portable -DestinationPath NFLBetting-1.0.0-Portable.zip
```

## Notes

- The MSI installer requires administrative privileges
- For PWA on iOS/iPad, users add to homescreen from Safari
- The portable version works without installation
- All versions require Python dependencies to be bundled
