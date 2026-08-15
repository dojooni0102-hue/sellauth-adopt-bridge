@echo off
title SellAuth Dropship Bridge
echo ==============================================
echo   SellAuth Adopt Me Dropship Bridge Server
echo ==============================================
echo.
echo [1/2] Installing required packages...
pip install fastapi uvicorn requests python-dotenv pydantic

echo.
echo [2/2] Starting Server...
python main.py
pause
