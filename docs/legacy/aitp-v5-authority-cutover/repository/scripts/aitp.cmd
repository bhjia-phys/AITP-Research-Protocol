@echo off
:: AITP CLI — routes to PM (install/update/...) or research CLI (topic/state/...)
set "REPO_ROOT=%~dp0.."
set "PM_PATH=%~dp0aitp-pm.py"

:: Determine Python
if defined AITP_PYTHON (
    set "PY=%AITP_PYTHON%"
) else (
    where python >NUL 2>NUL
    if %ERRORLEVEL% equ 0 (
        set "PY=python"
    ) else (
        where python3 >NUL 2>NUL
        if %ERRORLEVEL% equ 0 (
            set "PY=python3"
        ) else (
            where py >NUL 2>NUL
            if %ERRORLEVEL% equ 0 (
                set "PY=py -3"
            ) else (
                echo AITP: Could not find Python. Install Python 3.10+ or set AITP_PYTHON env var. 1>&2
                exit /b 1
            )
        )
    )
)

:: No args — show help via the aitp script
if "%~1"=="" (
    %PY% "%~dp0aitp" %*
    exit /b %ERRORLEVEL%
)

:: PM subcommands
if "%~1"=="install"   goto :pm
if "%~1"=="uninstall" goto :pm
if "%~1"=="update"    goto :pm
if "%~1"=="upgrade"   goto :pm
if "%~1"=="status"    goto :pm
if "%~1"=="doctor"    goto :pm
if "%~1"=="pm"        goto :pm

:: Everything else → research CLI
:cli
%PY% -m brain.cli %*
exit /b %ERRORLEVEL%

:pm
%PY% "%PM_PATH%" %*
exit /b %ERRORLEVEL%
