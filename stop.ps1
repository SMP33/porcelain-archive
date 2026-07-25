# Остановка backend (порт 8000) и frontend dev-сервера (порт 5173),
# запущенных через start.ps1.

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Get-PortOwnerPids([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
}

function Stop-TaskManagers {
    # task_manager - дочерний процесс backend (subprocess.Popen в lifespan), порт
    # не слушает, поэтому Stop-ByPort его не находит. Ищем по командной строке -
    # так же убиваются и осиротевшие процессы прошлых нештатных остановок.
    $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*porcelain_archive.task_manager*' }
    if (-not $procs) {
        Write-Host "task_manager не запущен."
        return
    }

    Write-Host "Останавливаю task_manager (PID: $($procs.ProcessId -join ', '))..."
    foreach ($proc in $procs) {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Stop-ByPort([int]$Port, [string]$Label) {
    $procIds = Get-PortOwnerPids $Port
    if (-not $procIds) {
        Write-Host "$Label не запущен."
        return
    }

    Write-Host "Останавливаю $Label (PID: $($procIds -join ', '))..."
    foreach ($procId in $procIds) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep -Milliseconds 500
    if (Get-PortOwnerPids $Port) {
        Write-Warning "Не удалось остановить $Label."
    } else {
        Write-Host "$Label остановлен."
    }
}

Stop-ByPort -Port 8000 -Label "backend"
Stop-ByPort -Port 5173 -Label "frontend dev-сервер"
Stop-TaskManagers
