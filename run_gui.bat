@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_PY=%SCRIPT_DIR%.venv\Scripts\python.exe"
set "VENV_PYW=%SCRIPT_DIR%.venv\Scripts\pythonw.exe"

if exist "%VENV_PYW%" (
    start "" "%VENV_PYW%" -m mcworldmgr.gui_main
) else if exist "%VENV_PY%" (
    start "" "%VENV_PY%" -m mcworldmgr.gui_main
) else (
    start "" pythonw -m mcworldmgr.gui_main
)

endlocal
