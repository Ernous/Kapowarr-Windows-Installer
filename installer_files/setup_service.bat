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
echo Setting up Kapowarr as Windows Service...

if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"

set "LOG_FILE=%INSTALL_DIR%\logs\install_debug.log"
echo Starting Kapowarr service installation at %date% %time% >> "%LOG_FILE%"

set "PYTHON_DIR=%INSTALL_DIR%\python"
set "PYTHON_CMD=%PYTHON_DIR%\python.exe"

cd /d "%INSTALL_DIR%"

if not exist "%PYTHON_CMD%" (
    echo Error: Python not found at %PYTHON_CMD% >> "%LOG_FILE%"
    exit /b 1
)

if not exist "%INSTALL_DIR%\Kapowarr.py" (
    echo Error: Kapowarr.py not found in %INSTALL_DIR% >> "%LOG_FILE%"
    exit /b 1
)

echo Testing Python environment... >> "%LOG_FILE%"
set "OLD_PYTHONPATH=%PYTHONPATH%"
set "PYTHONPATH=%INSTALL_DIR%"
"!PYTHON_CMD!" -c "import sys; sys.path.insert(0, r'%INSTALL_DIR%'); import backend; print('Backend loaded successfully')" >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo Error: Python environment test failed. Check %LOG_FILE% >> "%LOG_FILE%"
    set "PYTHONPATH=%OLD_PYTHONPATH%"
    exit /b 1
)
set "PYTHONPATH=%OLD_PYTHONPATH%"

set "NSSM_PATH=%INSTALL_DIR%\installer_files\nssm.exe"
if not exist "%NSSM_PATH%" (
    echo Error: NSSM not found at %NSSM_PATH%. >> "%LOG_FILE%"
    exit /b 1
)

"%NSSM_PATH%" stop Kapowarr >> "%LOG_FILE%" 2>&1
"%NSSM_PATH%" remove Kapowarr confirm >> "%LOG_FILE%" 2>&1

"%NSSM_PATH%" install Kapowarr "%PYTHON_CMD%" >> "%LOG_FILE%" 2>&1
"%NSSM_PATH%" set Kapowarr AppParameters "-u Kapowarr.py" >> "%LOG_FILE%" 2>&1
"%NSSM_PATH%" set Kapowarr AppDirectory "%INSTALL_DIR%" >> "%LOG_FILE%" 2>&1

if %errorlevel% neq 0 (
    echo Error installing service >> "%LOG_FILE%"
    exit /b 1
)

"%NSSM_PATH%" set Kapowarr DisplayName "Kapowarr" >> "%LOG_FILE%" 2>&1
"%NSSM_PATH%" set Kapowarr Description "Kapowarr - Comic and manga server" >> "%LOG_FILE%" 2>&1
"%NSSM_PATH%" set Kapowarr Start SERVICE_AUTO_START >> "%LOG_FILE%" 2>&1
"%NSSM_PATH%" set Kapowarr AppStdout "%INSTALL_DIR%\logs\service.log" >> "%LOG_FILE%" 2>&1
"%NSSM_PATH%" set Kapowarr AppStderr "%INSTALL_DIR%\logs\service_error.log" >> "%LOG_FILE%" 2>&1
"%NSSM_PATH%" set Kapowarr AppRotateFiles 1 >> "%LOG_FILE%" 2>&1
"%NSSM_PATH%" set Kapowarr AppRotateOnline 1 >> "%LOG_FILE%" 2>&1

"%NSSM_PATH%" start Kapowarr >> "%LOG_FILE%" 2>&1

timeout /t 5 /nobreak >nul
"%NSSM_PATH%" status Kapowarr > "%INSTALL_DIR%\logs\status.tmp" 2>&1
set /p SERVICE_STATUS= < "%INSTALL_DIR%\logs\status.tmp"
del "%INSTALL_DIR%\logs\status.tmp"

if "%SERVICE_STATUS%"=="SERVICE_RUNNING" (
    echo Kapowarr service installed and started successfully!
) else (
    echo Error starting service. Check logs.
    exit /b 1
)

exit /b 0
