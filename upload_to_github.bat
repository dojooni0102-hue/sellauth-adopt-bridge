@echo off
set "PATH=%PATH%;C:\Program Files\GitHub CLI"
title GitHub Auto Uploader
echo ===================================================
echo   GitHub Auto Repository Creator and Uploader
echo ===================================================
echo.
echo [1/3] Logging in to GitHub...
echo Press Enter to open browser and enter the one-time code shown below.
echo.
"C:\Program Files\GitHub CLI\gh.exe" auth login -h github.com -p https -w

echo.
echo [2/3] Creating repository 'sellauth-adopt-bridge' on GitHub and pushing code...
"C:\Program Files\GitHub CLI\gh.exe" repo create sellauth-adopt-bridge --public --source=. --remote=origin --push

echo.
echo ===================================================
echo [3/3] SUCCESS! Uploaded to GitHub!
echo ===================================================
pause
