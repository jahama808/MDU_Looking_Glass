@echo off
REM Property Outage Analysis - Installation Script for Windows
REM This script sets up a Python virtual environment and installs dependencies

echo ============================================================
echo Property Outage Analysis - Setup
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.6 or higher and try again.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Warning: Virtual environment already exists. Removing old venv...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)
echo Virtual environment created in .\venv
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo pip upgraded
echo.

REM Install requirements
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies installed
echo.

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo To use the script:
echo   1. Activate the virtual environment:
echo      venv\Scripts\activate
echo.
echo   2. Run the script:
echo      python process_property_outages.py ^
echo        --connectivity-file wan_connectivity.csv ^
echo        --discovery-file eero_discovery.csv
echo.
echo   3. When done, deactivate the virtual environment:
echo      deactivate
echo.
echo For more information, see README.md
echo.
pause
