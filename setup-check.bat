@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================
echo  SMCR Staff AI - Setup Check
echo ================================================
echo.

set MISSING=0

:: --- Git ---
where git >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('git --version 2^>nul') do set GIT_VER=%%i
    echo [OK]      Git: !GIT_VER!
) else (
    echo [MISSING] Git not found.
    echo.
    echo           Install options:
    echo             winget install Git.Git
    echo             https://git-scm.com/downloads
    echo.
    set MISSING=1
)

:: --- Python ---
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version 2^>nul') do set PY_VER=%%i
    echo [OK]      Python: !PY_VER!  ^(3.12 or newer required^)
) else (
    echo [MISSING] Python not found.
    echo.
    echo           Install options:
    echo             winget install Python.Python.3.12
    echo             https://www.python.org/downloads/
    echo.
    set MISSING=1
)

:: --- uv ---
where uv >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('uv --version 2^>nul') do set UV_VER=%%i
    echo [OK]      uv: !UV_VER!
) else (
    echo [MISSING] uv not found.
    echo.
    echo           Install options:
    echo             powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo             pip install uv
    echo.
    set MISSING=1
)

echo.

if %MISSING% equ 1 (
    echo ------------------------------------------------
    echo  Install the missing items above, then re-run
    echo  this script  OR  just run: start.bat
    echo.
    echo  TIP: Open Claude, Copilot, or another AI
    echo  assistant in this folder and say:
    echo.
    echo    "Help me install the prerequisites for
    echo     smcr-staff-ai - see QUICKSTART.md"
    echo.
    echo  It can walk you through each step.
    echo ------------------------------------------------
) else (
    echo  All prerequisites found.
    echo.
    set /p LAUNCH="  Launch the server now? [Y/n]: "
    if /i "!LAUNCH!" == "n" goto done
    call start.bat
)

:done
echo.
pause
endlocal
