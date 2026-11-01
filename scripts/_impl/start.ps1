[CmdletBinding()]
param(
    [switch]$NoPause,
    [int]$DjangoPort = 8000,
    [int]$FastApiPort = 8001
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root
$Host.UI.RawUI.WindowTitle = 'Solar-World - Start'

try {
    $null = chcp 65001
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}
catch { }

function Write-Header {
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host '  Solar-World - запуск' -ForegroundColor Cyan
    Write-Host "  Папка проекта: $Root" -ForegroundColor DarkGray
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host ''
}

function Write-Step { param([string]$Number, [string]$Text) Write-Host "[$Number] $Text" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Text) Write-Host "      $Text" -ForegroundColor Green }
function Write-Warn { param([string]$Text) Write-Host "      $Text" -ForegroundColor Yellow }
function Write-Err  { param([string]$Text) Write-Host "      $Text" -ForegroundColor Red }

function Wait-AnyKey {
    if ($NoPause) { return }
    Write-Host ''
    Write-Host 'Нажмите любую клавишу для выхода...' -ForegroundColor DarkGray
    try {
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    }
    catch {
        Read-Host | Out-Null
    }
}

function Test-PythonExe {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    & $Path -c "import sys" 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Find-ProjectPython {
    $candidates = @(
        (Join-Path $Root 'venv\Scripts\python.exe'),
        (Join-Path $Root 'env\Scripts\python.exe')
    )
    foreach ($candidate in $candidates) {
        if (Test-PythonExe $candidate) { return $candidate }
    }
    return $null
}

function Test-Port {
    param([int]$Port)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        $ready = $async.AsyncWaitHandle.WaitOne(400)
        if (-not $ready) { $client.Close(); return $false }
        $client.EndConnect($async)
        $client.Close()
        return $true
    }
    catch {
        return $false
    }
}

function Test-Redis {
    param([string]$PythonPath)
    & $PythonPath -c "import redis; redis.Redis(socket_connect_timeout=0.5, socket_timeout=0.5).ping()" 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Stop-ProcessTree {
    param($Process)
    if ($null -eq $Process) { return }
    try {
        if (-not $Process.HasExited) {
            & taskkill /PID $Process.Id /T /F 2>$null | Out-Null
        }
    }
    catch { }
}

Write-Header

$python = Find-ProjectPython
if (-not $python) {
    Write-Err 'Не найдено рабочее виртуальное окружение проекта.'
    Write-Err 'Сначала запустите scripts\setup.bat'
    Write-Host ''
    Wait-AnyKey
    exit 1
}

if (-not (Test-Path (Join-Path $Root '.env'))) {
    Write-Err 'Не найден файл .env.'
    Write-Err 'Сначала запустите scripts\setup.bat'
    Write-Host ''
    Wait-AnyKey
    exit 1
}

if (Test-Port $DjangoPort) {
    Write-Err "Порт $DjangoPort уже занят. Возможно, сайт уже запущен."
    Write-Err 'Закройте старое окно сервера и повторите запуск.'
    Write-Host ''
    Wait-AnyKey
    exit 1
}

if (Test-Port $FastApiPort) {
    Write-Err "Порт $FastApiPort уже занят (FastAPI). Освободите порт и повторите запуск."
    Write-Host ''
    Wait-AnyKey
    exit 1
}

# --- Шаг 1. Миграции ---------------------------------------------------------
Write-Step '1/4' 'Применение миграций...'
& $python (Join-Path $Root 'manage.py') migrate --noinput 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warn 'Миграции не применились, пробуем запустить как есть.'
}
else {
    Write-Ok 'База данных готова.'
}
Write-Host ''

# --- Шаг 2. Redis ------------------------------------------------------------
Write-Step '2/4' 'Проверка Redis (кэш)...'
$redisReady = Test-Redis $python

if (-not $redisReady) {
    $memurai = Get-Service -Name 'Memurai*' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($memurai -and $memurai.Status -ne 'Running') {
        Write-Warn "Служба $($memurai.Name) остановлена, пробуем запустить..."
        try {
            Start-Service -Name $memurai.Name -ErrorAction Stop
            Start-Sleep -Seconds 2
            $redisReady = Test-Redis $python
        }
        catch {
            Write-Warn 'Не удалось запустить службу (нужны права администратора).'
        }
    }
}

if (-not $redisReady) {
    $redisServer = Get-Command redis-server -ErrorAction SilentlyContinue
    if ($redisServer) {
        Write-Warn 'Запускаем redis-server...'
        Start-Process -FilePath $redisServer.Source -WindowStyle Minimized | Out-Null
        Start-Sleep -Seconds 2
        $redisReady = Test-Redis $python
    }
}

if (-not $redisReady) {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($docker) {
        Write-Warn 'Пробуем поднять Redis в Docker...'
        & docker run -d --rm --name solar-world-redis -p 6379:6379 redis:7-alpine 2>$null | Out-Null
        Start-Sleep -Seconds 4
        $redisReady = Test-Redis $python
    }
}

if ($redisReady) {
    Write-Ok 'Redis доступен на 127.0.0.1:6379.'
}
else {
    Write-Warn 'Redis не найден на 127.0.0.1:6379.'
    Write-Warn 'Проект использует Redis для кэша: без него часть страниц'
    Write-Warn 'и API могут отвечать ошибкой 500.'
    Write-Warn ''
    Write-Warn 'Установите Memurai одной командой:'
    Write-Warn '  winget install -e --id Memurai.MemuraiDeveloper'
    Write-Warn 'Либо запустите Docker Desktop. Сайт будет запущен,'
    Write-Warn 'но с ограниченной работоспособностью.'
}
Write-Host ''

# --- Шаг 3. FastAPI ----------------------------------------------------------
Write-Step '3/4' "Запуск FastAPI (планета дня, порт $FastApiPort)..."
$fastapi = $null
try {
    $fastapi = Start-Process -FilePath $python `
        -ArgumentList @('-m', 'uvicorn', 'main:app', '--reload', '--port', "$FastApiPort") `
        -WorkingDirectory (Join-Path $Root 'fastapi_random_planets') `
        -PassThru
    Write-Ok "FastAPI PID: $($fastapi.Id)"
}
catch {
    Write-Warn 'Не удалось запустить FastAPI. Сайт продолжит работу без "планеты дня".'
}
Write-Host ''

# --- Шаг 4. Django -----------------------------------------------------------
Write-Step '4/4' "Запуск Django (сайт, порт $DjangoPort)..."
$django = $null
try {
    $django = Start-Process -FilePath $python `
        -ArgumentList @('manage.py', 'runserver', "127.0.0.1:$DjangoPort") `
        -WorkingDirectory $Root `
        -PassThru
    Write-Ok "Django PID: $($django.Id)"
}
catch {
    Write-Err 'Не удалось запустить Django.'
    Stop-ProcessTree $fastapi
    Write-Host ''
    Wait-AnyKey
    exit 1
}
Write-Host ''

Write-Host 'Ожидание запуска серверов...' -ForegroundColor DarkGray
$deadline = (Get-Date).AddSeconds(25)
do {
    $djangoUp = Test-Port $DjangoPort
    $fastapiUp = Test-Port $FastApiPort
    if ($djangoUp -and $fastapiUp) { break }
    Start-Sleep -Milliseconds 400
} while ((Get-Date) -lt $deadline)

Write-Host '============================================================' -ForegroundColor Green
if ($djangoUp) {
    Write-Host '  Solar-World запущен.' -ForegroundColor Green
}
else {
    Write-Host '  Django ещё запускается — проверьте его окно консоли.' -ForegroundColor Yellow
}
Write-Host ''
Write-Host "  Сайт:      http://127.0.0.1:$DjangoPort" -ForegroundColor White
Write-Host "  Каталог:   http://127.0.0.1:$DjangoPort/api/catalog/" -ForegroundColor White
Write-Host "  FastAPI:   http://127.0.0.1:$FastApiPort/docs" -ForegroundColor White
if (-not $fastapiUp) {
    Write-Host '  (FastAPI пока не отвечает — смотрите его окно)' -ForegroundColor Yellow
}
Write-Host ''
Write-Host '  Логи серверов открыты в отдельных окнах консоли.' -ForegroundColor DarkGray
Write-Host '============================================================' -ForegroundColor Green
Write-Host ''
Write-Host 'Нажмите любую клавишу, чтобы остановить серверы...' -ForegroundColor DarkGray
try {
    if (-not $NoPause) { $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown') }
}
catch {
    if (-not $NoPause) { Read-Host | Out-Null }
}

Stop-ProcessTree $django
Stop-ProcessTree $fastapi

Write-Host ''
Write-Host 'Серверы остановлены.' -ForegroundColor Green
Wait-AnyKey
exit 0
