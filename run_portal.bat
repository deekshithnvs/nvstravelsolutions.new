@echo off
echo Starting NVS Vendor Portal...
cd /d "%~dp0"
python -m uvicorn main:app --port 8000 --host 0.0.0.0 --reload
pause
