$ErrorActionPreference = "Stop"

$body = @{
  email = "admin@autojob.local"
  password = "ChangeMe123!"
} | ConvertTo-Json

$login = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body $body -ContentType "application/json"
$headers = @{ Authorization = "Bearer $($login.access_token)" }

Invoke-RestMethod -Uri "http://localhost:8000/api/dashboard/summary" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/profiles/jobs" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/profiles/candidates" -Headers $headers

Write-Host "Smoke test completed."

