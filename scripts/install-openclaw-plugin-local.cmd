@ECHO OFF
SETLOCAL

FOR %%I IN ("%~dp0..") DO SET "AITP_REPO_ROOT=%%~fI"
SET "PLUGIN_SCRIPT=%AITP_REPO_ROOT%\research\adapters\openclaw\scripts\install_openclaw_plugin.py"

IF NOT EXIST "%PLUGIN_SCRIPT%" (
  ECHO Missing plugin installer: %PLUGIN_SCRIPT%>&2
  EXIT /B 1
)

IF DEFINED AITP_PYTHON (
  "%AITP_PYTHON%" "%PLUGIN_SCRIPT%" %*
  EXIT /B %ERRORLEVEL%
)

where python >NUL 2>NUL
IF %ERRORLEVEL% EQU 0 (
  python "%PLUGIN_SCRIPT%" %*
  EXIT /B %ERRORLEVEL%
)

where py >NUL 2>NUL
IF %ERRORLEVEL% EQU 0 (
  py -3 "%PLUGIN_SCRIPT%" %*
  EXIT /B %ERRORLEVEL%
)

ECHO Python 3 launcher not found on PATH.>&2
EXIT /B 127
