@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%aitp-local.py" %*
exit /b %errorlevel%
