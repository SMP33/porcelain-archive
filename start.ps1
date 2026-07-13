# Сборка frontend (frontend/dist - для доступа напрямую через backend), затем
# запуск backend (porcelain_archive, порт 8000) и frontend
# dev-сервера (npm run dev, порт 5173) в фоне, вывод - в лог-файлы.
# Если что-то из них уже запущено (порт занят) - перезапускает.

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$RunDir = Join-Path $PSScriptRoot ".run"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Build-Frontend {
    # Нужна для варианта доступа напрямую через backend (порт 8000, frontend/dist),
    # dev-сервер (порт 5173) собранный dist не использует и работает поверх исходников.
    Write-Host "Сборка frontend..."
    $frontendDir = Join-Path $PSScriptRoot "frontend"
    & npm.cmd --prefix $frontendDir install
    & npm.cmd --prefix $frontendDir run build
}

function Get-PortOwnerPids([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
}

function Start-Backend {
    $port = 8000
    $logFile = Join-Path $RunDir "server.log"
    $errFile = Join-Path $RunDir "server.err.log"

    $existing = Get-PortOwnerPids $port
    if ($existing) {
        Write-Host "Backend уже запущен (PID: $($existing -join ', ')), перезапускаю..."
        foreach ($procId in $existing) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 1
    }

    Write-Host "Запуск backend..."
    $pythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    Start-Process -FilePath $pythonExe -ArgumentList "-m", "porcelain_archive" `
        -WorkingDirectory $PSScriptRoot `
        -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
        -WindowStyle Hidden | Out-Null

    Start-Sleep -Seconds 2
    $running = Get-PortOwnerPids $port
    if ($running) {
        Write-Host "Backend запущен, PID: $($running -join ', '). Лог: $logFile"
    } else {
        Write-Error "Не удалось запустить backend (см. $logFile и $errFile)."
        exit 1
    }
}

function Start-Frontend {
    $port = 5173
    $frontendDir = Join-Path $PSScriptRoot "frontend"
    $logFile = Join-Path $RunDir "frontend.log"
    $errFile = Join-Path $RunDir "frontend.err.log"

    $existing = Get-PortOwnerPids $port
    if ($existing) {
        Write-Host "Frontend dev-сервер уже запущен (PID: $($existing -join ', ')), перезапускаю..."
        foreach ($procId in $existing) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 1
    }

    Write-Host "Запуск frontend dev-сервера..."
    # npm run dev запускает vite в дочернем node-процессе - именно он слушает
    # порт, поэтому и старт, и остановка ориентируются на порт, а не на PID npm.
    Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" `
        -WorkingDirectory $frontendDir `
        -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
        -WindowStyle Hidden | Out-Null

    Start-Sleep -Seconds 3
    $running = Get-PortOwnerPids $port
    if ($running) {
        Write-Host "Frontend dev-сервер запущен, PID: $($running -join ', '). Лог: $logFile"
    } else {
        Write-Error "Не удалось запустить frontend dev-сервер (см. $logFile и $errFile)."
        exit 1
    }
}

Build-Frontend
Start-Backend
Start-Frontend
