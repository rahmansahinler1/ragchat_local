@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main.py
call deactivate