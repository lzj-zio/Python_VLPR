# Python_VLPR Android APK Build Script
# Run as Administrator

param(
    [switch]$AutoRestart
)

$ErrorActionPreference = "Stop"

# APK output directory
$ApkOutputDir = "C:\Users\HUAWEI\Desktop\FinalDesign\apk"

function Write-Step($num, $total, $message) {
    Write-Host "[$num/$total] $message" -ForegroundColor Cyan
}

function Test-Administrator {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check admin rights
if (-not (Test-Administrator)) {
    Write-Host "ERROR: This script requires administrator privileges" -ForegroundColor Red
    Write-Host "Right-click this script and select 'Run as administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  License Plate Recognition - APK Build" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Create output directory if not exists
if (-not (Test-Path $ApkOutputDir)) {
    New-Item -ItemType Directory -Path $ApkOutputDir -Force | Out-Null
    Write-Host "Created output directory: $ApkOutputDir" -ForegroundColor Green
}

$projectDir = "C:\Users\HUAWEI\Desktop\FinalDesign\Python_VLPR-master"

# Step 1: Check WSL
Write-Step 1 6 "Checking WSL status..."

try {
    $null = wsl --status 2>&1
    $wslInstalled = $?
    if ($wslInstalled) {
        Write-Host "OK: WSL is installed" -ForegroundColor Green
    }
} catch {
    $wslInstalled = $false
}

if (-not $wslInstalled) {
    Write-Host "WSL not installed, installing..." -ForegroundColor Yellow
    
    Write-Step 2 6 "Enabling WSL feature..."
    $null = dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    
    Write-Step 3 6 "Enabling Virtual Machine Platform..."
    $null = dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  Computer restart required to complete WSL installation" -ForegroundColor Yellow
    Write-Host "  Please run this script again after restart" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press Enter to restart now, or close to restart manually..." -ForegroundColor Gray
    
    $response = Read-Host
    if ($response -ne "n") {
        Restart-Computer -Force
    }
    exit 0
}

# Step 4: Check Ubuntu
Write-Step 4 6 "Checking Ubuntu status..."

$ubuntuInstalled = $false
try {
    $wslList = wsl -l --verbose 2>&1
    if ($wslList -like "*Ubuntu*") {
        $ubuntuInstalled = $true
        Write-Host "OK: Ubuntu is installed" -ForegroundColor Green
    }
} catch {
    $ubuntuInstalled = $false
}

if (-not $ubuntuInstalled) {
    Write-Host "Installing Ubuntu..." -ForegroundColor Yellow
    $null = wsl --install --distribution Ubuntu --no-default-application
    Start-Sleep -Seconds 5
}

# Set WSL2 as default
$null = wsl --set-default-version 2

# Step 5: Install dependencies in WSL
Write-Step 5 6 "Installing dependencies in WSL..."

$wslCommands = @"
set -e
export DEBIAN_FRONTEND=noninteractive

echo 'Updating system...'
sudo apt update -qq
sudo apt upgrade -y -qq

echo 'Installing required tools...'
sudo apt install -y git zip unzip openjdk-11-jdk python3 python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev python3-dev wget 2>/dev/null

echo 'Installing Python packages...'
pip3 install --upgrade pip -q
pip3 install buildozer cython==0.29.19 -q

echo 'Done!'
"@

Write-Host "Installing... (this may take a few minutes)" -ForegroundColor Gray

try {
    $null = wsl -e bash -c $wslCommands 2>&1
    Write-Host "OK: Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Some dependencies may not have installed correctly" -ForegroundColor Yellow
}

# Step 6: Copy project and build APK
Write-Step 6 6 "Copying project and building APK..."

$buildCommands = @"
set -e

# Clean old project
rm -rf ~/Python_VLPR 2>/dev/null

# Copy project
echo 'Copying project to WSL...'
cp -r /mnt/c/Users/HUAWEI/Desktop/FinalDesign/Python_VLPR-master ~/Python_VLPR

cd ~/Python_VLPR

echo ''
echo '========================================'
echo '  Building APK'
echo '  First build takes 30-60 minutes'
echo '========================================'
echo ''

# Build APK
buildozer android debug

# Copy APK back to output directory
echo ''
echo 'Copying APK to output directory...'
mkdir -p /mnt/c/Users/HUAWEI/Desktop/FinalDesign/apk
cp bin/*.apk /mnt/c/Users/HUAWEI/Desktop/FinalDesign/apk/

echo ''
echo '========================================'
echo '  Build Complete!'
echo '========================================'
ls -la bin/*.apk
"@

Write-Host "Building APK..." -ForegroundColor Yellow
Write-Host "(First build downloads Android SDK, please wait)" -ForegroundColor Gray
Write-Host ""

try {
    $null = wsl -e bash -c $buildCommands 2>&1
    $buildSuccess = $true
} catch {
    $buildSuccess = $false
    Write-Host "Build error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
if ($buildSuccess) {
    Write-Host "  Build Complete!" -ForegroundColor Green
    Write-Host "  APK location: $ApkOutputDir" -ForegroundColor Green
    Write-Host "  Check the folder for your APK file" -ForegroundColor Green
} else {
    Write-Host "  Build may have failed" -ForegroundColor Yellow
    Write-Host "  Check logs above for details" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
