[CmdletBinding()]
param(
    [switch]$NoPause
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root
$Host.UI.RawUI.WindowTitle = 'Solar-World - Setup'

try {
    $null = chcp 65001
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}
catch { }

function Write-Header {
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host '  Solar-World - установка проекта' -ForegroundColor Cyan
    Write-Host "  Папка проекта: $Root" -ForegroundColor DarkGray
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host ''
}

function Write-Step {
    param([string]$Number, [string]$Text)
    Write-Host "[$Number] $Text" -ForegroundColor Cyan
}

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

function Find-SystemPython {
    foreach ($name in @('python', 'py')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        if ($name -eq 'py') {
            & py -3 -c "import sys" 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { return @{ Exe = 'py'; Args = @('-3') } }
        }
        else {
            & python -c "import sys" 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { return @{ Exe = 'python'; Args = @() } }
        }
    }
    return $null
}

function Exit-WithError {
    param([string]$Message)
    Write-Host ''
    Write-Err $Message
    Write-Host ''
    Wait-AnyKey
    exit 1
}

Write-Header

# --- Шаг 1. Виртуальное окружение -------------------------------------------
Write-Step '1/6' 'Подготовка виртуального окружения...'

$python = Find-ProjectPython
if ($python) {
    Write-Ok "Используем окружение: $python"
}
else {
    Write-Warn 'Рабочее виртуальное окружение не найдено, создаём venv...'
    $base = Find-SystemPython
    if (-not $base) {
        Exit-WithError 'Python 3 не найден. Установите Python 3.10+ с python.org и добавьте его в PATH.'
    }

    $venvPath = Join-Path $Root 'venv'
    $baseArgs = @($base.Args) + @('-m', 'venv', $venvPath)
    & $base.Exe @baseArgs
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError 'Не удалось создать виртуальное окружение venv.'
    }

    $python = Join-Path $Root 'venv\Scripts\python.exe'
    if (-not (Test-PythonExe $python)) {
        Exit-WithError 'Виртуальное окружение создано, но python.exe в нём не запускается.'
    }
    Write-Ok "Создано окружение: $python"
}
Write-Host ''

# --- Шаг 2. pip --------------------------------------------------------------
Write-Step '2/6' 'Обновление pip...'
& $python -m pip install --upgrade pip --disable-pip-version-check
if ($LASTEXITCODE -ne 0) {
    Write-Warn 'Не удалось обновить pip, продолжаем с текущей версией.'
}
Write-Host ''

# --- Шаг 3. Зависимости ------------------------------------------------------
Write-Step '3/6' 'Установка зависимостей из requirements.txt...'
$requirements = Join-Path $Root 'requirements.txt'
if (-not (Test-Path $requirements)) {
    Exit-WithError "Файл requirements.txt не найден: $requirements"
}
& $python -m pip install -r $requirements --disable-pip-version-check
if ($LASTEXITCODE -ne 0) {
    Exit-WithError 'Не удалось установить зависимости. Проверьте подключение к интернету и повторите запуск.'
}
Write-Host ''

# --- Шаг 4. .env -------------------------------------------------------------
Write-Step '4/6' 'Проверка файла .env...'
$envPath = Join-Path $Root '.env'
if (-not (Test-Path $envPath)) {
    $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    $chars = for ($i = 0; $i -lt 64; $i++) { $alphabet[(Get-Random -Maximum $alphabet.Length)] }
    $secret = -join $chars
    $content = "SECRET_KEY=$secret`r`nDEBUG=True`r`nENVIRONMENT=local`r`n"
    [System.IO.File]::WriteAllText($envPath, $content, (New-Object System.Text.UTF8Encoding($false)))
    Write-Ok '.env создан, сгенерирован новый SECRET_KEY.'
}
else {
    Write-Ok '.env уже существует, оставляем без изменений.'
}
Write-Host ''

# --- Шаг 5. Миграции ---------------------------------------------------------
Write-Step '5/6' 'Применение миграций базы данных...'
& $python (Join-Path $Root 'manage.py') migrate --noinput
if ($LASTEXITCODE -ne 0) {
    Exit-WithError 'Миграции не применились. Смотрите текст ошибки выше.'
}
Write-Host ''

# --- Шаг 6. Демо-данные + проверка ------------------------------------------
Write-Step '6/6' 'Загрузка демонстрационных данных...'
& $python (Join-Path $Root 'manage.py') shell -c "from planets.models import Planet; raise SystemExit(0 if Planet.objects.exists() else 1)" 2>$null | Out-Null
$dbEmpty = ($LASTEXITCODE -ne 0)

if ($dbEmpty) {
    $fixture = Join-Path $Root 'data.json'
    if (Test-Path $fixture) {
        & $python (Join-Path $Root 'manage.py') loaddata $fixture
        if ($LASTEXITCODE -ne 0) {
            Write-Warn 'Не удалось загрузить data.json. База осталась без демо-данных.'
        }
        else {
            Write-Ok 'Демо-данные загружены.'
        }
    }
    else {
        Write-Warn 'Файл data.json не найден, демо-данные не загружены.'
    }
}
else {
    Write-Ok 'База уже содержит данные, загрузка пропущена.'
}
Write-Host ''

Write-Host 'Проверка конфигурации Django...' -ForegroundColor Cyan
& $python (Join-Path $Root 'manage.py') check
if ($LASTEXITCODE -ne 0) {
    Exit-WithError 'Проверка Django завершилась с ошибкой. Смотрите текст выше.'
}
Write-Host ''

Write-Host '============================================================' -ForegroundColor Green
Write-Host '  Установка завершена успешно.' -ForegroundColor Green
Write-Host ''
Write-Host '  Дальше:' -ForegroundColor White
Write-Host '    scripts\start.bat        - запустить сайт' -ForegroundColor White
Write-Host '    scripts\start_tests.bat  - запустить тесты' -ForegroundColor White
Write-Host '============================================================' -ForegroundColor Green

Wait-AnyKey
exit 0
