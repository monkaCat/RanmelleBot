@echo off
setlocal
cd /d "%~dp0"
title MeowMeowBot Dependency Installer

echo.
echo Installing MeowMeowBot Python dependencies...
echo.

set "PY_CMD="

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py -3"
)

if "%PY_CMD%"=="" (
    where python >nul 2>nul
    if %errorlevel%==0 (
        python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
        if not errorlevel 1 set "PY_CMD=python"
    )
)

if "%PY_CMD%"=="" goto install_python

:install_python_packages
%PY_CMD% -m pip install --upgrade pip
if errorlevel 1 goto install_failed
%PY_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto install_failed
goto done

:install_python
echo Python 3.11+ was not found.
echo.
where winget >nul 2>nul
if not %errorlevel%==0 goto python_manual

echo Installing Python 3.11 via winget...
winget install --id Python.Python.3.11 -e --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto python_failed

echo.
echo Python installation finished. Checking again...
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py -3"
)

if "%PY_CMD%"=="" (
    where python >nul 2>nul
    if %errorlevel%==0 (
        python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
        if not errorlevel 1 set "PY_CMD=python"
    )
)

if "%PY_CMD%"=="" (
    echo Python was installed, but this terminal cannot see it yet.
    echo Close this window and run Install_MeowMeowBot_Dependencies.bat again.
    pause
    exit /b 1
)

goto install_python_packages

:python_manual
echo.
echo Python 3.11+ was not found, and winget is not available.
echo Install Python manually from:
echo https://www.python.org/downloads/
echo Enable "Add Python to PATH" during install.
echo Then run this installer again.
pause
exit /b 1

:python_failed
echo.
echo Python could not be installed automatically.
echo Install Python 3.11+ manually from:
echo https://www.python.org/downloads/
echo Enable "Add Python to PATH" during install.
echo Then run this installer again.
pause
exit /b 1

:install_failed
echo.
echo Installation failed. Please keep this window open and send a screenshot of the red error above.
echo.
pause
exit /b 1

:done
echo.
echo Done. You can now start MeowMeowBot.vbs or MeowMeowBot.lnk.
echo Note: on first start, EasyOCR will download its text recognition model (~100 MB). This requires an internet connection once.
echo
pause
