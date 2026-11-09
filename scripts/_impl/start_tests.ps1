[CmdletBinding()]
param(
    [switch]$NoPause
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root
$Host.UI.RawUI.WindowTitle = 'Solar-World - Tests'

try {
    $null = chcp 65001
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}
catch { }

function Write-Header {
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host '  Solar-World - запуск тестов' -ForegroundColor Cyan
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

Write-Header

$python = Find-ProjectPython
if (-not $python) {
    Write-Err 'Не найдено рабочее виртуальное окружение проекта.'
    Write-Err 'Сначала запустите scripts\setup.bat'
    Write-Host ''
    Wait-AnyKey
    exit 1
}

Write-Step '1/2' 'Проверка конфигурации Django...'
& $python (Join-Path $Root 'manage.py') check
if ($LASTEXITCODE -ne 0) {
    Write-Warn 'Проверка Django завершилась с замечаниями, запускаем тесты.'
}
else {
    Write-Ok 'Конфигурация в порядке.'
}
Write-Host ''

Write-Step '2/2' 'Запуск pytest...'
& $python -m pytest -v
$testCode = $LASTEXITCODE
Write-Host ''

if ($testCode -eq 0) {
    Write-Host '============================================================' -ForegroundColor Green
    Write-Host '  Все тесты пройдены успешно.' -ForegroundColor Green
    Write-Host '============================================================' -ForegroundColor Green
}
else {
    Write-Host '============================================================' -ForegroundColor Red
    Write-Host "  Тесты завершились с ошибками. Код выхода: $testCode" -ForegroundColor Red
    Write-Host '============================================================' -ForegroundColor Red
}

Wait-AnyKey
exit $testCode
