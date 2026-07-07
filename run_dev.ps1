Set-Location -Path $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

try {
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
}
finally {
    Read-Host "Нажмите Enter, чтобы закрыть окно"
}
