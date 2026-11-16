@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
python src\depviz16\__main__.py %*
