# LinkedIn Scraper - Chrome Debug Mode Launcher
# Run this in PowerShell on Windows

Write-Host "🚀 Starting Chrome in Debug Mode for LinkedIn Scraper..." -ForegroundColor Green
Write-Host ""

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$debugPort = 9222
$userDataDir = "C:\temp\chrome-debug"

# Check if Chrome exists
if (-Not (Test-Path $chromePath)) {
    Write-Host "❌ Chrome not found at: $chromePath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Google Chrome or update the path in this script." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Found Chrome at: $chromePath" -ForegroundColor Green
Write-Host "📡 Debug Port: $debugPort" -ForegroundColor Cyan
Write-Host "📁 User Data: $userDataDir" -ForegroundColor Cyan
Write-Host ""

# Create user data directory if it doesn't exist
if (-Not (Test-Path $userDataDir)) {
    New-Item -ItemType Directory -Path $userDataDir -Force | Out-Null
    Write-Host "📁 Created user data directory" -ForegroundColor Green
}

Write-Host "🌐 Starting Chrome..." -ForegroundColor Green
Write-Host ""
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host "INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host "1. Chrome will open in a new window" -ForegroundColor White
Write-Host "2. Go to https://www.linkedin.com/" -ForegroundColor White
Write-Host "3. Login with your THROWAWAY account" -ForegroundColor White
Write-Host "4. Keep this window OPEN" -ForegroundColor White
Write-Host "5. Run the scraper in WSL:" -ForegroundColor White
Write-Host ""
Write-Host "   python3 scraper.py --running True --port $debugPort \\" -ForegroundColor Cyan
Write-Host "     --url https://www.linkedin.com/in/PROFILE_NAME/ \\" -ForegroundColor Cyan
Write-Host "     --save True" -ForegroundColor Cyan
Write-Host ""
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  DO NOT CLOSE THIS WINDOW OR CHROME!" -ForegroundColor Red
Write-Host ""

# Start Chrome with debugging
& $chromePath --remote-debugging-port=$debugPort --user-data-dir=$userDataDir

Write-Host ""
Write-Host "Chrome closed. Exiting..." -ForegroundColor Yellow
