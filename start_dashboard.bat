@echo off
title SAP Vendor Intelligence & AP Risk Agent (VIRA)
echo =======================================================
echo   SAP Vendor Intelligence & AP Risk Agent (VIRA)
echo   URL: http://localhost:8000
echo =======================================================
echo.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe run.py --ui
) else (
    python run.py --ui
)
pause
