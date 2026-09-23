@echo off
title GL Anomaly Detection Dashboard Server
echo =======================================================
echo   GL Anomaly Detection Agent - Local Dashboard Server
echo   URL: http://localhost:8000
echo =======================================================
echo.
cd /d "c:\Users\arati\Downloads\uc14_agent 1"
uc14_agent\.venv\Scripts\python.exe run.py --ui
pause
