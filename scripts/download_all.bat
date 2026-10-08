@echo off
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

for /F "usebackq delims=" %%D in ("%DATES_FILE%") do (
    python "%~dp0..\downloaders\%DOWNLOADER%" --date "%%D"
)

echo Download completed. Log saved to %LOG_FILE%