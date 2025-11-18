@echo off
REM Automated Data Processing Script - Windows Version
REM Checks for new data files and processes them automatically

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Directories
set "INPUTS_DIR=inputs"
set "ARCHIVE_DIR=inputs_already_read"
set "DB_PATH=output\outages.db"
set "LOG_FILE=logs\auto-process.log"

REM Create directories if they don't exist
if not exist "%INPUTS_DIR%" mkdir "%INPUTS_DIR%"
if not exist "%ARCHIVE_DIR%" mkdir "%ARCHIVE_DIR%"
if not exist "logs" mkdir "logs"

REM Logging function
set "TIMESTAMP="
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    for /f "tokens=1-2 delims=: " %%e in ('time /t') do (
        set "TIMESTAMP=%%c-%%a-%%b %%e:%%f"
    )
)

echo [%TIMESTAMP%] ======================================== >> "%LOG_FILE%"
echo [%TIMESTAMP%] Automated Data Processing - Starting >> "%LOG_FILE%"
echo [%TIMESTAMP%] ======================================== >> "%LOG_FILE%"

echo ========================================
echo Automated Data Processing - Starting
echo ========================================
echo.

REM Find connectivity file (most recent if multiple)
set "WAN_FILE="
for /f "delims=" %%f in ('dir /b /o-d "%INPUTS_DIR%\networks_outage-*.csv" 2^>nul') do (
    if not defined WAN_FILE set "WAN_FILE=%INPUTS_DIR%\%%f"
)

REM Find Eero discovery file (most recent if multiple)
set "EERO_FILE="
for /f "delims=" %%f in ('dir /b /o-d "%INPUTS_DIR%\Eero Discovery Details*.csv" 2^>nul') do (
    if not defined EERO_FILE set "EERO_FILE=%INPUTS_DIR%\%%f"
)

REM Check if both files were found
if not defined WAN_FILE (
    echo [%TIMESTAMP%] No new files to process >> "%LOG_FILE%"
    echo [%TIMESTAMP%] Missing: networks_outage-*.csv >> "%LOG_FILE%"
    echo No new files to process
    echo   Missing: networks_outage-*.csv
    goto :END
)

if not defined EERO_FILE (
    echo [%TIMESTAMP%] No new files to process >> "%LOG_FILE%"
    echo [%TIMESTAMP%] Missing: Eero Discovery Details*.csv >> "%LOG_FILE%"
    echo No new files to process
    echo   Missing: Eero Discovery Details*.csv
    goto :END
)

REM Extract basenames for checking archive
for %%f in ("%WAN_FILE%") do set "WAN_BASENAME=%%~nxf"
for %%f in ("%EERO_FILE%") do set "EERO_BASENAME=%%~nxf"

echo [%TIMESTAMP%] Files found for processing: >> "%LOG_FILE%"
echo [%TIMESTAMP%]   WAN Connectivity: %WAN_BASENAME% >> "%LOG_FILE%"
echo [%TIMESTAMP%]   Eero Discovery: %EERO_BASENAME% >> "%LOG_FILE%"

echo Files found for processing:
echo   WAN Connectivity: %WAN_BASENAME%
echo   Eero Discovery: %EERO_BASENAME%
echo.

REM Check if files have already been processed
if exist "%ARCHIVE_DIR%\%WAN_BASENAME%" (
    if exist "%ARCHIVE_DIR%\%EERO_BASENAME%" (
        echo [%TIMESTAMP%] Files already processed (found in archive) >> "%LOG_FILE%"
        echo Files already processed (found in archive)
        goto :END
    )
)

REM Check for virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [%TIMESTAMP%] Error: Virtual environment not found >> "%LOG_FILE%"
    echo Error: Virtual environment not found
    echo Please run install.bat first
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo [%TIMESTAMP%] Virtual environment activated >> "%LOG_FILE%"
echo Virtual environment activated
echo.

REM Process the data
echo [%TIMESTAMP%] Processing data files... >> "%LOG_FILE%"
echo Processing data files...
echo.

python process_property_outages_db.py --connectivity-file "%WAN_FILE%" --discovery-file "%EERO_FILE%" --database "%DB_PATH%" --mode append --retain-days 7 >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [%TIMESTAMP%] Data processing completed successfully >> "%LOG_FILE%"
    echo Data processing completed successfully
    echo.

    REM Create timestamped archive subdirectory
    for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
        for /f "tokens=1-2 delims=: " %%e in ('time /t') do (
            set "ARCHIVE_SUBDIR=%ARCHIVE_DIR%\%%c-%%a-%%b_%%e%%f"
        )
    )

    REM Remove spaces from timestamp
    set "ARCHIVE_SUBDIR=!ARCHIVE_SUBDIR: =!"

    mkdir "!ARCHIVE_SUBDIR!"

    echo [%TIMESTAMP%] Moving files to archive... >> "%LOG_FILE%"
    echo Moving files to archive...

    move "%WAN_FILE%" "!ARCHIVE_SUBDIR!\" >> "%LOG_FILE%"
    move "%EERO_FILE%" "!ARCHIVE_SUBDIR!\" >> "%LOG_FILE%"

    echo [%TIMESTAMP%] Files archived to: !ARCHIVE_SUBDIR! >> "%LOG_FILE%"
    echo Files archived to: !ARCHIVE_SUBDIR!
    echo.

    echo [%TIMESTAMP%] ======================================== >> "%LOG_FILE%"
    echo [%TIMESTAMP%] Processing Complete! >> "%LOG_FILE%"
    echo [%TIMESTAMP%] Database updated: %DB_PATH% >> "%LOG_FILE%"
    echo [%TIMESTAMP%] ======================================== >> "%LOG_FILE%"

    echo ========================================
    echo Processing Complete!
    echo Database updated: %DB_PATH%
    echo ========================================
) else (
    echo [%TIMESTAMP%] Error during data processing >> "%LOG_FILE%"
    echo Error during data processing
    echo Files NOT moved to archive (will retry on next run)
    exit /b 1
)

:END
endlocal
