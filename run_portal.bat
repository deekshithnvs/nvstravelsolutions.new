@echo off
echo Starting NVS Vendor Portal...
cd /d "c:\code\Vendor management portal\backend-services"
python -m uvicorn main:app --port 8000 --host 0.0.0.0 --reload
pause
