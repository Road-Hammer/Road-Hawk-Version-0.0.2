@echo off
setlocal

set "NODE_DIR="
if exist "C:\Program Files\nodejs\node.exe" set "NODE_DIR=C:\Program Files\nodejs"
if not defined NODE_DIR if exist "%LOCALAPPDATA%\road-hawk-node\node.exe" set "NODE_DIR=%LOCALAPPDATA%\road-hawk-node"

if not defined NODE_DIR (
  echo Node.js not found. Install from https://nodejs.org or restart your terminal after winget install.
  exit /b 1
)

set "PATH=%NODE_DIR%;%PATH%"
cd /d "%~dp0.."

if "%~1"=="" (
  echo Usage: run-with-node.cmd [dev^|build^|start]
  exit /b 1
)

"%NODE_DIR%\node.exe" "node_modules\next\dist\bin\next" %*
exit /b %ERRORLEVEL%