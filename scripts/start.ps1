# Vidya Copilot — start server
$ErrorActionPreference = "Stop"

$OllamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$OllamaDir = Split-Path $OllamaExe -Parent
$ProjectRoot = Split-Path $PSScriptRoot -Parent

# Add Ollama to PATH for this session
if (Test-Path $OllamaDir) {
    $env:PATH = "$OllamaDir;$env:PATH"
}

# Check Ollama is reachable
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3
    $models = $health.models | ForEach-Object { $_.name }
    if ($models.Count -eq 0) {
        Write-Host "WARNING: No models installed. Run: .\scripts\setup.ps1" -ForegroundColor Yellow
    } else {
        Write-Host "Ollama models: $($models -join ', ')" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Ollama not responding. Open the Ollama app first." -ForegroundColor Yellow
}

Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "Run setup first: .\scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

Write-Host "Starting Vidya Copilot at http://127.0.0.1:8000" -ForegroundColor Cyan
& $Python run.py
