$ErrorActionPreference = "Stop"

Write-Host "Starting backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\..\backend'; python -m venv .venv; .\.venv\Scripts\activate; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8000"

Write-Host "Starting worker..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\..\worker'; python -m venv .venv; .\.venv\Scripts\activate; pip install -r requirements.txt; python -m app.runner"

Write-Host "Starting frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\..\frontend'; cmd /c npm install; if ($LASTEXITCODE -eq 0) { cmd /c npm run dev }"
