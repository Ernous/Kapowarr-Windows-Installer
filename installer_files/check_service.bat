@echo off
setlocal enabledelayedexpansion

set "INSTALL_DIR=%~1"
if "%INSTALL_DIR%"=="" set "INSTALL_DIR=%~dp0.."

echo Checking Kapowarr service status...
echo Installation directory: %INSTALL_DIR%
echo.

sc query Kapowarr >nul 2>&1
if %errorlevel% neq 0 (
    echo Kapowarr service is not installed
    echo.
    echo To install service, run:
    echo "%INSTALL_DIR%\installer_files\setup_service.bat" "%INSTALL_DIR%"
    goto :end
)

echo Service Status:
sc query Kapowarr
echo.

for /f "tokens=3" %%i in ('sc query Kapowarr ^| findstr "STATE"') do (
    set "SERVICE_STATE=%%i"
)

if "!SERVICE_STATE!"=="RUNNING" (
    echo ✓ Kapowarr service is running
    echo.
    echo Checking if port 5656 is accessible...
    netstat -an | findstr ":5656" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✓ Port 5656 is listening
        echo You can access Kapowarr at http://localhost:5656
    ) else (
        echo ⚠ Port 5656 is not listening yet
        echo Service may still be starting up
    )
) else (
    echo ⚠ Kapowarr service is not running
    echo Current state: !SERVICE_STATE!
    echo.
    echo To start the service, run:
    echo sc start Kapowarr
    echo.
    echo Or use NSSM:
    echo "%INSTALL_DIR%\installer_files\nssm.exe" start Kapowarr
)

echo.
echo Log files:
if exist "%INSTALL_DIR%\logs\service.log" (
    echo - Service log: %INSTALL_DIR%\logs\service.log
) else (
    echo - Service log: Not found
)

if exist "%INSTALL_DIR%\logs\service_error.log" (
    echo - Error log: %INSTALL_DIR%\logs\service_error.log
) else (
    echo - Error log: Not found
)

if exist "%INSTALL_DIR%\logs\install_debug.log" (
    echo - Installation log: %INSTALL_DIR%\logs\install_debug.log
) else (
    echo - Installation log: Not found
)

echo.
echo Recent service log entries (last 10 lines):
if exist "%INSTALL_DIR%\logs\service.log" (
    powershell "Get-Content '%INSTALL_DIR%\logs\service.log' | Select-Object -Last 10"
) else (
    echo Service log file not found
)

:end
pause
