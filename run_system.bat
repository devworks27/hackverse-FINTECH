@echo off
echo ======================================================================
echo Launching FinIntel Autonomous Multi-Agent Financial Intelligence Platform
echo ======================================================================
cd /d "%~dp0"
echo Starting FastAPI Server with Real-Time WebSockets on http://localhost:8000 ...
start http://localhost:8000
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
