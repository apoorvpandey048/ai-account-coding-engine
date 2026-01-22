# Start Backend API Server
# This script starts the FastAPI server in a new terminal window

$workingDir = $PSScriptRoot
$title = "AI Account Coding - Backend API"

Write-Host "Starting backend API server in new window..." -ForegroundColor Cyan
Write-Host "Working directory: $workingDir" -ForegroundColor Gray
Write-Host ""

# Start in new PowerShell window
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "cd '$workingDir'; `
     Write-Host '=============================================='-ForegroundColor Cyan; `
     Write-Host ' AI Account Coding Backend API' -ForegroundColor Green; `
     Write-Host '==============================================' -ForegroundColor Cyan; `
     Write-Host ''; `
     Write-Host 'Starting server on http://127.0.0.1:8005...' -ForegroundColor Yellow; `
     Write-Host 'API Key: dev-key-001' -ForegroundColor Yellow; `
     Write-Host ''; `
     Write-Host 'Press Ctrl+C to stop the server' -ForegroundColor Gray; `
     Write-Host ''; `
     python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8005 --reload"

Write-Host "Backend server started in new terminal window!" -ForegroundColor Green
Write-Host "Server URL: http://127.0.0.1:8005" -ForegroundColor Cyan
Write-Host "API Key: dev-key-001" -ForegroundColor Cyan
Write-Host ""
Write-Host "To expose via ngrok, run in another terminal:" -ForegroundColor Yellow
Write-Host "  & `"`$env:USERPROFILE\ngrok\ngrok.exe`" http 8005" -ForegroundColor Gray
