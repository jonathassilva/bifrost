@echo off
setlocal EnableDelayedExpansion
rem download_all.bat
rem Usage: download_all.bat --source malware|android

rem Check arguments
if "%1"=="" (
    echo Usage: %0 --source ^<malware^|android^>
    exit /b 1
)

if "%1"=="--source" (
    set "SOURCE=%2"
) else (
    echo Invalid argument: %1
    echo Usage: %0 --source ^<malware^|android^>
    exit /b 1
)

if /I "%SOURCE%"=="malware" (
    set "DOWNLOADER=malwares_downloader.py"
) else if /I "%SOURCE%"=="android" (
    set "DOWNLOADER=android_downloader.py"
) else (
    echo Invalid source: %SOURCE%
    echo Valid values are malware or android
    exit /b 1
)

rem Determine script directory
set "SCRIPT_DIR=%~dp0"

set "DATES_FILE=%SCRIPT_DIR%dates.txt"
set "LOG_FILE=%SCRIPT_DIR%download-%SOURCE%.log"

if not exist "%DATES_FILE%" (
    echo Dates file not found: %DATES_FILE%
    exit /b 1
)

set /a TOTAL=0
set /a FAILED=0

rem FOR /F already skips empty lines; eol=# skips comment lines
for /F "usebackq eol=# tokens=* delims=" %%D in ("%DATES_FILE%") do (
    set /a TOTAL+=1
    echo ===== %SOURCE% :: %%D =====
    >> "%LOG_FILE%" echo [!DATE! !TIME!] ===== %SOURCE% :: %%D =====
    python "%~dp0..\downloaders\%DOWNLOADER%" --date "%%D" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        set /a FAILED+=1
        echo [warn] Downloader failed for %%D - see log
        >> "%LOG_FILE%" echo [warn] Downloader failed for %%D
    )
)

echo Download completed: %TOTAL% date(s), %FAILED% failure(s). Log saved to %LOG_FILE%
if %FAILED% GTR 0 exit /b 1