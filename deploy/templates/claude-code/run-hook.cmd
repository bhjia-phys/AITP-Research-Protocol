: << 'CMDBLOCK'
@echo off
if "%~1"=="" (
    echo run-hook.cmd: missing script name >&2
    exit /b 1
)

set "HOOK_DIR=%~dp0"
set "AITP_REPO_ROOT={{REPO_ROOT}}"
set "PYTHONPATH={{REPO_ROOT}};%PYTHONPATH%"
set "PYTHON_HOOK=%HOOK_DIR%%~1.py"

if exist "%PYTHON_HOOK%" (
    if defined AITP_PYTHON (
        "%AITP_PYTHON%" "%PYTHON_HOOK%" %2 %3 %4 %5 %6 %7 %8 %9
        exit /b %ERRORLEVEL%
    )

    where python >NUL 2>NUL
    if %ERRORLEVEL% equ 0 (
        python "%PYTHON_HOOK%" %2 %3 %4 %5 %6 %7 %8 %9
        exit /b %ERRORLEVEL%
    )

    where py >NUL 2>NUL
    if %ERRORLEVEL% equ 0 (
        py -3 "%PYTHON_HOOK%" %2 %3 %4 %5 %6 %7 %8 %9
        exit /b %ERRORLEVEL%
    )
)

if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" "%HOOK_DIR%%~1" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)
if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
    "C:\Program Files (x86)\Git\bin\bash.exe" "%HOOK_DIR%%~1" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

where bash >nul 2>nul
if %ERRORLEVEL% equ 0 (
    bash "%HOOK_DIR%%~1" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

echo WARNING: AITP session initialization could not run because bash is not available 1>&2
exit /b 0
CMDBLOCK

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"
shift
exec bash "${SCRIPT_DIR}/${SCRIPT_NAME}" "$@"
