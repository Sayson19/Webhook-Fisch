@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python screen_monitor.py
pause
