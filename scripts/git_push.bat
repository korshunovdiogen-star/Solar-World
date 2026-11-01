@echo off
setlocal
where powershell >nul 2>&1
if errorlevel 1 (
    echo PowerShell not found. Windows 10/11 is required.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_impl\git_push.ps1" %*
exit /b %errorlevel%
