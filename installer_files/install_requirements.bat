@echo off
setlocal enabledelayedexpansion

set "INSTALL_DIR=%~1"
echo Installing Python requirements for Kapowarr...
echo Installation directory: %INSTALL_DIR%

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :found_python
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :found_python
)

echo Error: Python not found in PATH
exit /b 1

:found_python
echo Using Python command: !PYTHON_CMD!
echo Installing requirements...

cd /d "%INSTALL_DIR%"
!PYTHON_CMD! -m pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo Requirements installed successfully!
) else (
    echo Error installing requirements
    exit /b 1
)

echo Installation complete!
