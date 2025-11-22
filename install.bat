@echo off
REM MDU Performance Dashboard - Installation Script (Windows)
REM This script sets up the entire application environment

echo ========================================
echo MDU Performance Dashboard - Installer
echo ========================================
echo.

REM Check for Python
echo Checking for Python 3...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3 is not installed
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Found Python %PYTHON_VERSION%

REM Check for Node.js
echo Checking for Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed
    echo Please install Node.js 16 or higher and try again.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo ✓ Found Node.js %NODE_VERSION%

REM Check for npm
echo Checking for npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo Error: npm is not installed
    echo Please install npm and try again.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('npm --version 2^>^&1') do set NPM_VERSION=%%i
echo ✓ Found npm %NPM_VERSION%
echo.

REM Create Python virtual environment
echo ========================================
echo Setting up Python environment...
echo ========================================

if exist venv (
    echo Virtual environment already exists. Removing...
    rmdir /s /q venv
)

python -m venv venv
echo ✓ Virtual environment created

REM Activate virtual environment
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo ✓ pip upgraded

REM Install Python dependencies
echo Installing Python dependencies...
pip install flask flask-cors pandas >nul 2>&1
echo ✓ Python dependencies installed
echo.

REM Install frontend dependencies
echo ========================================
echo Setting up Frontend environment...
echo ========================================

cd frontend

if exist node_modules (
    echo node_modules already exists. Removing...
    rmdir /s /q node_modules
)

echo Installing Node.js dependencies (this may take a few minutes)...
call npm install >nul 2>&1
echo ✓ Frontend dependencies installed

cd ..
echo.

REM Create output directory
echo ========================================
echo Creating directories...
echo ========================================

if not exist output mkdir output
echo ✓ Output directory created
echo.

REM Create start scripts
echo ========================================
echo Creating start scripts...
echo ========================================

REM Create start-backend.bat
echo @echo off > start-backend.bat
echo call venv\Scripts\activate.bat >> start-backend.bat
echo python api_server.py >> start-backend.bat
echo ✓ Created start-backend.bat

REM Create start-frontend.bat
echo @echo off > start-frontend.bat
echo cd frontend >> start-frontend.bat
echo npm run dev >> start-frontend.bat
echo ✓ Created start-frontend.bat

REM Create start-all.bat
echo @echo off > start-all.bat
echo echo Starting MDU Performance Dashboard... >> start-all.bat
echo echo. >> start-all.bat
echo echo Starting API server on port 5000... >> start-all.bat
echo start "API Server" cmd /k "call venv\Scripts\activate.bat && python api_server.py" >> start-all.bat
echo timeout /t 2 /nobreak ^>nul >> start-all.bat
echo echo Starting frontend dev server on port 5173... >> start-all.bat
echo start "Frontend Dev Server" cmd /k "cd frontend && npm run dev" >> start-all.bat
echo echo. >> start-all.bat
echo echo ======================================== >> start-all.bat
echo echo MDU Performance Dashboard is starting! >> start-all.bat
echo echo ======================================== >> start-all.bat
echo echo. >> start-all.bat
echo echo Frontend: http://localhost:5173 >> start-all.bat
echo echo API:      http://localhost:5000 >> start-all.bat
echo echo. >> start-all.bat
echo echo Two windows will open for the services. >> start-all.bat
echo echo Close those windows to stop the services. >> start-all.bat
echo echo. >> start-all.bat
echo pause >> start-all.bat
echo ✓ Created start-all.bat

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo ✓ Everything is set up and ready to go!
echo.
echo To start the application:
echo   start-all.bat          - Start both backend and frontend
echo   start-backend.bat      - Start only the API server
echo   start-frontend.bat     - Start only the frontend
echo.
echo To process data:
echo   call venv\Scripts\activate.bat
echo   python process_property_outages_db.py --connectivity-file ^<file^> --discovery-file ^<file^>
echo.
echo Access the application at: http://localhost:5173
echo.
pause
