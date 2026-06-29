# Vidya Copilot — one-time setup script
$ErrorActionPreference = "Stop"

$OllamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "=== Vidya Copilot Setup ===" -ForegroundColor Cyan

# 1. Check Ollama app
if (-not (Test-Path $OllamaExe)) {
    Write-Host "ERROR: Ollama not found. Install from https://ollama.com" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Ollama found at $OllamaExe" -ForegroundColor Green

# 2. Add Ollama to PATH for this session
$OllamaDir = Split-Path $OllamaExe -Parent
if ($env:PATH -notlike "*$OllamaDir*") {
    $env:PATH = "$OllamaDir;$env:PATH"
    Write-Host "[OK] Added Ollama to PATH for this session" -ForegroundColor Green
}

# 3. Create .env if missing
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvExample = Join-Path $ProjectRoot ".env.example"
if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "[OK] Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host "[OK] .env already exists" -ForegroundColor Green
}

# 4. Python venv
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv (Join-Path $ProjectRoot ".venv")
}
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt") -q

# 5. Pull Ollama models
$Model = "qwen3:8b"
$EmbedModel = "nomic-embed-text"

Write-Host "Pulling AI model: $Model (this may take 10-20 min, ~5GB)..." -ForegroundColor Yellow
& $OllamaExe pull $Model

Write-Host "Pulling embedding model: $EmbedModel..." -ForegroundColor Yellow
& $OllamaExe pull $EmbedModel

# 6. Verify
Write-Host "`nInstalled models:" -ForegroundColor Cyan
& $OllamaExe list

Write-Host "`n=== Setup complete! ===" -ForegroundColor Green
Write-Host "Start Vidya Copilot with:" -ForegroundColor Cyan
Write-Host "  cd $ProjectRoot"
Write-Host "  .\scripts\start.ps1"
