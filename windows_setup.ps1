# ================================================
# Python Environment + FFmpeg Setup (PowerShell)
# ================================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "       Python Environment + FFmpeg Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------
# Step 1: Check if Python is installed
# ---------------------------------------------------
Write-Host "Checking Python installation..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "ERROR: Python is not installed or not added to PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ---------------------------------------------------
# Step 2: Create virtual environment (.venv)
# ---------------------------------------------------
if (Test-Path ".venv") {
    Write-Host "Virtual environment already exists: .venv" -ForegroundColor Yellow
    Write-Host "Skipping creation..." -ForegroundColor Yellow
    Write-Host ""
}
else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host "Virtual environment created: .venv" -ForegroundColor Green
    Write-Host ""
}

# ---------------------------------------------------
# Step 3: Activate venv and install requirements
# ---------------------------------------------------
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow

& ".venv\Scripts\Activate.ps1"
python -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Requirements installed successfully." -ForegroundColor Green
Write-Host ""

# ---------------------------------------------------
# Step 4: Check if FFmpeg is installed
# ---------------------------------------------------
Write-Host "Checking FFmpeg installation..." -ForegroundColor Yellow

try {
    $ffmpegVersion = ffmpeg -version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "FFmpeg is already installed." -ForegroundColor Green
        Write-Host ""
        Write-Host "================================================" -ForegroundColor Cyan
        Write-Host "Setup Complete!" -ForegroundColor Cyan
        Write-Host "================================================" -ForegroundColor Cyan
        Read-Host "Press Enter to exit"
        exit 0
    }
}
catch {
    # FFmpeg not found, continue with installation
}

Write-Host "FFmpeg NOT installed." -ForegroundColor Yellow
Write-Host ""

# ---------------------------------------------------
# Step 5: Install FFmpeg for current user
# ---------------------------------------------------
Write-Host "Installing FFmpeg for CURRENT USER..." -ForegroundColor Yellow
Write-Host ""

$userFfmpegDir = "$env:USERPROFILE\ffmpeg"
$ffmpegBinDir = "$userFfmpegDir\bin"

Write-Host "Installing FFmpeg into: $userFfmpegDir" -ForegroundColor Cyan

# Create folder if it doesn't exist
if (-not (Test-Path $userFfmpegDir)) {
    New-Item -ItemType Directory -Path $userFfmpegDir -Force | Out-Null
}

# Download FFmpeg (7z format - smaller and faster)
$sevenZipPath = "$env:TEMP\ffmpeg_user.7z"
Write-Host "Downloading FFmpeg (7z format for faster download)..." -ForegroundColor Yellow

try {
    Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z" -OutFile $sevenZipPath -UseBasicParsing
    Write-Host "Download complete." -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Failed to download FFmpeg." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Download standalone 7z extractor (7zr.exe - tiny ~500KB)
$sevenZrPath = "$env:TEMP\7zr.exe"
Write-Host "Downloading 7z extractor..." -ForegroundColor Yellow

try {
    Invoke-WebRequest -Uri "https://www.7-zip.org/a/7zr.exe" -OutFile $sevenZrPath -UseBasicParsing
    Write-Host "7z extractor downloaded." -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Failed to download 7z extractor." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Extract to temp location
$tempExtractPath = "$env:TEMP\ffmpeg_extract"
Write-Host "Extracting FFmpeg (this may take a moment)..." -ForegroundColor Yellow

if (Test-Path $tempExtractPath) {
    Remove-Item -Path $tempExtractPath -Recurse -Force
}

New-Item -ItemType Directory -Path $tempExtractPath -Force | Out-Null

try {
    # Use 7zr.exe to extract
    $extractProcess = Start-Process -FilePath $sevenZrPath -ArgumentList "x `"$sevenZipPath`" -o`"$tempExtractPath`" -y" -Wait -NoNewWindow -PassThru
    
    if ($extractProcess.ExitCode -ne 0) {
        throw "7z extraction failed with exit code: $($extractProcess.ExitCode)"
    }
    
    Write-Host "Extraction complete." -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Failed to extract FFmpeg." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Find the extracted folder (ffmpeg-*-essentials_build)
$extractedFolder = Get-ChildItem -Path $tempExtractPath -Directory | Where-Object { $_.Name -like "ffmpeg-*" } | Select-Object -First 1

if ($null -eq $extractedFolder) {
    Write-Host "ERROR: Could not find extracted FFmpeg folder." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Copy contents to user ffmpeg directory
Write-Host "Installing FFmpeg files..." -ForegroundColor Yellow
Copy-Item -Path "$($extractedFolder.FullName)\*" -Destination $userFfmpegDir -Recurse -Force

# Clean up temp files
Remove-Item -Path $sevenZipPath -Force -ErrorAction SilentlyContinue
Remove-Item -Path $sevenZrPath -Force -ErrorAction SilentlyContinue
Remove-Item -Path $tempExtractPath -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "FFmpeg files installed successfully." -ForegroundColor Green
Write-Host ""

# ---------------------------------------------------
# Step 6: Add to User PATH
# ---------------------------------------------------
Write-Host "Updating user PATH environment variable..." -ForegroundColor Yellow

# Get current user PATH from registry
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($null -eq $userPath) {
    $userPath = ""
}

# Check if FFmpeg bin directory is already in PATH
if ($userPath -notlike "*$ffmpegBinDir*") {
    # Add FFmpeg to user PATH
    if ($userPath -ne "") {
        $newPath = "$userPath;$ffmpegBinDir"
    }
    else {
        $newPath = $ffmpegBinDir
    }
    
    try {
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "Added $ffmpegBinDir to user PATH." -ForegroundColor Green
    }
    catch {
        Write-Host "WARNING: Failed to update user PATH." -ForegroundColor Yellow
        Write-Host "You may need to add $ffmpegBinDir to your PATH manually." -ForegroundColor Yellow
    }
}
else {
    Write-Host "$ffmpegBinDir already in user PATH." -ForegroundColor Green
}

# Add to current session PATH
$env:Path = "$env:Path;$ffmpegBinDir"
Write-Host "FFmpeg is now available in this terminal session." -ForegroundColor Green
Write-Host ""

# Verify installation
Write-Host "Verifying FFmpeg installation..." -ForegroundColor Yellow
try {
    $ffmpegTest = & "$ffmpegBinDir\ffmpeg.exe" -version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "FFmpeg installed and verified successfully!" -ForegroundColor Green
    }
}
catch {
    Write-Host "WARNING: FFmpeg installed but verification failed." -ForegroundColor Yellow
    Write-Host "Please restart your terminal and try running 'ffmpeg -version'" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Please restart your terminal for PATH changes to take effect." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
exit 0
