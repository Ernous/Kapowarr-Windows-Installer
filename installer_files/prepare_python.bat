@echo off
setlocal enabledelayedexpansion

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script must be run as Administrator.
    pause
    exit /b 1
)

set "INSTALL_DIR=%~1"
if "%INSTALL_DIR%"=="" set "INSTALL_DIR=%CD%"
echo Preparing Python environment for Kapowarr...

if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"

set "LOG_FILE=%INSTALL_DIR%\logs\install_debug.log"
echo Starting Python environment preparation at %date% %time% >> "%LOG_FILE%"

set "PYTHON_DIR=%INSTALL_DIR%\python"

if not exist "%PYTHON_DIR%\python.exe" (
    echo Error: Portable Python not found at %PYTHON_DIR%. >> "%LOG_FILE%"
    exit /b 1
)

echo python311.zip > "%PYTHON_DIR%\python311._pth"
echo . >> "%PYTHON_DIR%\python311._pth"
echo .. >> "%PYTHON_DIR%\python311._pth"
echo site-packages >> "%PYTHON_DIR%\python311._pth"
echo import site >> "%PYTHON_DIR%\python311._pth"

set "PYTHON_CMD=%PYTHON_DIR%\python.exe"
"!PYTHON_CMD!" -c "import aiohttp; import cryptography; import _cffi_backend; print('All key libraries verified')" >> "%LOG_FILE%" 2>&1

if %errorlevel% neq 0 (
    echo Error: Python environment verification failed. >> "%LOG_FILE%"
    exit /b 1
)

exit /b 0
