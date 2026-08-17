$env:Path += ";C:\Program Files\GitHub CLI"
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   GitHub Auto Uploader" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[1/2] GitHub Login..." -ForegroundColor Yellow
& "C:\Program Files\GitHub CLI\gh.exe" auth login -h github.com -p https -w

Write-Host ""
Write-Host "[2/2] Creating repo and pushing..." -ForegroundColor Yellow
& "C:\Program Files\GitHub CLI\gh.exe" repo create sellauth-adopt-bridge --public --source=. --remote=origin --push

Write-Host ""
Write-Host "SUCCESS! Uploaded to GitHub." -ForegroundColor Green
Read-Host -Prompt "Press Enter to exit"
