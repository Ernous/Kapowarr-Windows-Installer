@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%I in ("%SCRIPT_DIR%") do set "BASE_DIR=%%~dpI"
if "%BASE_DIR:~-1%"=="\" set "BASE_DIR=%BASE_DIR:~0,-1%"

cd /d "%BASE_DIR%"
set "PYTHONPATH=%BASE_DIR%;%PYTHONPATH%"

if not exist "%BASE_DIR%\python\python.exe" exit /b 1
if not exist "%BASE_DIR%\Kapowarr.py" exit /b 1

"%BASE_DIR%\python\python.exe" -u "%BASE_DIR%\Kapowarr.py" >> "%BASE_DIR%\logs\service_output.log" 2>&1
