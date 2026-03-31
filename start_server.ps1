# Start Meta AI API server with cookies
$storageState = Get-Content -Path "storage_state.json" -Raw
$env:STORAGE_STATE = $storageState

Write-Host "✅ Loaded cookies from storage_state.json" -ForegroundColor Green
Write-Host "🚀 Starting Meta AI API server on http://localhost:8000" -ForegroundColor Cyan
Write-Host ""

py -m uvicorn main:app --host 0.0.0.0 --port 8000
