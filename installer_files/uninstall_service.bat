@echo off
setlocal enabledelayedexpansion

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script must be run as Administrator.
    echo Please right-click and select "Run as administrator".
    pause
    exit /b 1
)

set "INSTALL_DIR=%~1"
if "%INSTALL_DIR%"=="" set "INSTALL_DIR=%CD%"
echo Uninstalling Kapowarr Windows Service...
echo Installation directory: %INSTALL_DIR%

cd /d "%INSTALL_DIR%"

echo Stopping Kapowarr service...
"%INSTALL_DIR%\installer_files\nssm.exe" stop Kapowarr >nul 2>&1

echo Removing Kapowarr service...
"%INSTALL_DIR%\installer_files\nssm.exe" remove Kapowarr confirm >nul 2>&1

if %errorlevel% equ 0 (
    echo Kapowarr service uninstalled successfully!
) else (
    echo Error uninstalling service (service may not exist)
)

echo Service uninstallation complete!
