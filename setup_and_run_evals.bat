@echo off
REM One-click setup for Windows: finds Python, installs everything, asks for your Gemini key once,
REM then runs the tests and the evals and saves the results to results_evals.txt.
setlocal EnableExtensions
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
echo.
echo ===== Shop Chatbot setup =====
echo.

REM ---- 1. Find a real Python 3.9+ (the plain "python" command can be a fake Microsoft Store shortcut) ----
set "PY="
call :try py -3
if not defined PY call :try python
if not defined PY call :tryfile "%USERPROFILE%\.venv\Scripts\python.exe"
if not defined PY for /d %%D in ("%USERPROFILE%\PycharmProjects\*") do if not defined PY call :tryfile "%%~D\.venv\Scripts\python.exe"
if not defined PY for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-3*") do if not defined PY call :tryfile "%%~D\python.exe"
if not defined PY for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if not defined PY call :tryfile "%%~D\python.exe"
if not defined PY for /d %%D in ("%ProgramFiles%\Python3*") do if not defined PY call :tryfile "%%~D\python.exe"
if not defined PY for /d %%D in ("%APPDATA%\uv\python\*") do if not defined PY call :tryfile "%%~D\python.exe"
if not defined PY call :diagnose
if not defined PY call :install
if not defined PY goto nopython
echo Found Python: %PY%

REM ---- 2. Create this project's own environment ----
set "VPY=.venv\Scripts\python.exe"
set "RETRIED="
:makevenv
REM Rebuild the environment if it's missing or broken (e.g. it points at a Python that was removed)
if exist "%VPY%" "%VPY%" -c "import sys" >nul 2>nul
if exist "%VPY%" if errorlevel 1 (
    echo Old environment is broken - rebuilding it...
    rmdir /s /q ".venv"
)
if exist ".venv" if not exist "%VPY%" rmdir /s /q ".venv"
if not exist "%VPY%" (
    echo [1/4] Creating a private Python environment...
    %PY% -m venv .venv
)
if not exist "%VPY%" goto nopython

echo [2/4] Installing packages (about a minute the first time)...
"%VPY%" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto pipfailed

REM ---- 3. API key ----
if not exist ".env" copy ".env.example" ".env" >nul
findstr /r /c:"^GEMINI_API_KEY=..*" ".env" >nul
if errorlevel 1 (
    echo.
    echo ---------------------------------------------------------------
    echo  Notepad is opening your .env file.
    echo  Paste your Gemini key straight after  GEMINI_API_KEY=
    echo  ^(no spaces, no quote marks^), press Ctrl+S, then close Notepad.
    echo ---------------------------------------------------------------
    notepad ".env"
)
findstr /r /c:"^GEMINI_API_KEY=..*" ".env" >nul
if errorlevel 1 (
    echo.
    echo No key found in .env - run this file again and paste the key.
    pause
    exit /b 1
)

REM ---- 4. Tests and evals ----
echo [3/4] Running the unit tests...
"%VPY%" -m pytest -q -p no:cacheprovider > results_tests.txt 2>&1
findstr /c:"passed" /c:"failed" /c:"error" results_tests.txt

echo [4/4] Running the 12 evals against the real AI (1-2 minutes, progress shows below)...
"%VPY%" -u evals\run_evals.py
echo.
echo ===== Done! Results saved in results_evals.txt =====
pause
exit /b 0

:try
%* -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=%*"
exit /b 0

:tryfile
if not exist "%~1" exit /b 0
"%~1" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if not errorlevel 1 set PY="%~1"
exit /b 0

:diagnose
> python_check.txt (
    echo where python / py:
    where python 2>&1
    where py 2>&1
    echo.
    echo PyCharm / home virtual environments:
    if exist "%USERPROFILE%\.venv\pyvenv.cfg" (echo --- home .venv & type "%USERPROFILE%\.venv\pyvenv.cfg")
    for /d %%D in ("%USERPROFILE%\PycharmProjects\*") do if exist "%%~D\.venv\pyvenv.cfg" (echo --- %%~nxD & type "%%~D\.venv\pyvenv.cfg")
)
exit /b 0

:install
echo.
echo No working Python found. Windows can install Python 3.12 for you (official, from Microsoft's winget).
where winget >nul 2>nul
if errorlevel 1 (
    echo winget isn't available, so opening the python.org download page instead.
    echo Install it ^(tick "Add python.exe to PATH"^), then run this file again.
    start "" https://www.python.org/downloads/
    exit /b 0
)
where pymanager >nul 2>nul
if not errorlevel 1 (
    echo The Python Install Manager is installed. Downloading Python itself - answer Y to any questions.
    pymanager install default
    call :try py
    if defined PY exit /b 0
    for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-3*") do if not defined PY call :tryfile "%%~D\python.exe"
    if defined PY exit /b 0
)
choice /c YN /m "Install Python 3.12 now"
if errorlevel 2 exit /b 0
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
call :tryfile "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-3*") do if not defined PY call :tryfile "%%~D\python.exe"
if not defined PY (
    echo.
    echo Python was installed, but Windows needs a fresh start to see it.
    echo Close this window and double-click setup_and_run_evals again.
)
exit /b 0

:nopython
echo.
echo Couldn't find Python 3.9 or newer on this computer.
echo Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), then run this again.
pause
exit /b 1

:pipfailed
REM Brand-new Python versions sometimes lack ready-made packages. Try once more with Python 3.13.
if defined RETRIED goto fail
set "RETRIED=1"
where pymanager >nul 2>nul
if errorlevel 1 goto fail
echo.
echo Some packages don't support this brand-new Python yet. Installing Python 3.13 alongside it - answer Y to any questions.
pymanager install 3.13
set PY="%LOCALAPPDATA%\Python\pythoncore-3.13-64\python.exe"
if not exist %PY% goto fail
rmdir /s /q ".venv"
goto makevenv

:fail
echo.
echo Something went wrong installing packages. Check the error message above (or take a screenshot of this window if you need help).
pause
exit /b 1
