@ECHO off
SETLOCAL EnableExtensions EnableDelayedExpansion

FOR %%I IN ("%~dp0..") DO SET "REPO_ROOT=%%~fI"
SET "KIMI_HOME=%REPO_ROOT%\.kimi"
SET "KIMI_CONFIG=%KIMI_HOME%\config.toml"
SET "KIMI_AGENT=%KIMI_HOME%\aitp-agent.yaml"
SET "KIMI_SECRETS=%KIMI_HOME%\secrets"

IF NOT EXIST "%KIMI_HOME%" mkdir "%KIMI_HOME%" >NUL 2>NUL
IF NOT EXIST "%KIMI_SECRETS%" mkdir "%KIMI_SECRETS%" >NUL 2>NUL

REM --------------------------------------------------------------------------
REM Load secrets from .kimi/secrets/*.txt into environment variables.
REM These are available to Kimi and any subprocesses (including MCP servers).
REM --------------------------------------------------------------------------
CALL :LoadSecret KIMI_API_KEY       "%KIMI_SECRETS%\kimi_api_key.txt"
CALL :LoadSecret MOONSHOT_API_KEY   "%KIMI_SECRETS%\moonshot_api_key.txt"
CALL :LoadSecret GITHUB_TOKEN       "%KIMI_SECRETS%\github_token.txt"
CALL :LoadSecret OBSIDIAN_API_KEY   "%KIMI_SECRETS%\obsidian_api_key.txt"
CALL :LoadSecret EXA_API_KEY        "%KIMI_SECRETS%\exa_api_key.txt"
CALL :LoadSecret SESSDATA           "%KIMI_SECRETS%\bilibili_sessdata.txt"

REM Cross-alias the two common Kimi/Moonshot key names
IF NOT DEFINED KIMI_API_KEY IF DEFINED MOONSHOT_API_KEY (
  SET "KIMI_API_KEY=%MOONSHOT_API_KEY%"
)
IF NOT DEFINED MOONSHOT_API_KEY IF DEFINED KIMI_API_KEY (
  SET "MOONSHOT_API_KEY=%KIMI_API_KEY%"
)

REM --------------------------------------------------------------------------
REM Resolve Kimi binary
REM --------------------------------------------------------------------------
SET "KIMI_BIN=C:\Users\samur\.local\bin\kimi.exe"
IF NOT EXIST "%KIMI_BIN%" (
  FOR /F "delims=" %%A IN ('where kimi 2^>NUL') DO SET "KIMI_BIN=%%A"
)
IF NOT EXIST "%KIMI_BIN%" (
  ECHO [kimi] kimi.exe not found. Install Kimi Code CLI first:
  ECHO   uv tool install kimi-cli
  ECHO   or visit https://moonshotai.github.io/kimi-cli/
  EXIT /B 1
)

REM --------------------------------------------------------------------------
REM Launch with project-level config and AITP agent.
REM --config-file overrides ~/.kimi/config.toml completely.
REM --agent-file loads the AITP bootstrap agent (forces using-aitp read).
REM --------------------------------------------------------------------------
CALL "%KIMI_BIN%" --config-file "%KIMI_CONFIG%" --agent-file "%KIMI_AGENT%" %*
EXIT /B %ERRORLEVEL%

REM --------------------------------------------------------------------------
REM Subroutines
REM --------------------------------------------------------------------------
:LoadSecret
IF DEFINED %~1 GOTO :EOF
IF NOT EXIST "%~2" GOTO :EOF
FOR /F "usebackq delims=" %%A IN ("%~2") DO SET "%~1=%%A"
GOTO :EOF
