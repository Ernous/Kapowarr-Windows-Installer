@echo off
setlocal enabledelayedexpansion

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script must be run as Administrator.
    exit /b 1
)

set "INSTALL_DIR=%~1"
if "%INSTALL_DIR%"=="" (
    set "INSTALL_DIR=%~dp0"
    if "!INSTALL_DIR:~-16!"=="\installer_files\" set "INSTALL_DIR=!INSTALL_DIR:~0,-16!"
)

echo.
echo ====================================================
echo   Kapowarr Full Cleanup
echo ====================================================
echo.
echo Target Directory: %INSTALL_DIR%

if exist "%INSTALL_DIR%\installer_files\nssm.exe" (
    echo Stopping Kapowarr service...
    "%INSTALL_DIR%\installer_files\nssm.exe" stop Kapowarr >nul 2>&1
    echo Removing Kapowarr service...
    "%INSTALL_DIR%\installer_files\nssm.exe" remove Kapowarr confirm >nul 2>&1
)

echo Terminating any running Kapowarr processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Kapowarr*" >nul 2>&1
taskkill /F /IM kapowarr_tray.exe >nul 2>&1

echo Removing Python environment...
if exist "%INSTALL_DIR%\python" rmdir /s /q "%INSTALL_DIR%\python"

echo Removing application data (logs, database)...
if exist "%INSTALL_DIR%\logs" rmdir /s /q "%INSTALL_DIR%\logs"
if exist "%INSTALL_DIR%\db" rmdir /s /q "%INSTALL_DIR%\db"

echo Removing installer files...
if exist "%INSTALL_DIR%\installer_files" rmdir /s /q "%INSTALL_DIR%\installer_files"

echo Cleaning up root directory...
del /q "%INSTALL_DIR%\*.db" >nul 2>&1
del /q "%INSTALL_DIR%\*.sqlite" >nul 2>&1
del /q "%INSTALL_DIR%\config.json" >nul 2>&1
del /q "%INSTALL_DIR%\settings.json" >nul 2>&1

echo.
echo Cleanup complete!
exit /b 0
