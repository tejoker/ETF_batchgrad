#!/bin/bash

# LinkedIn Scraper - Easy Launch Script
# This script helps you run the scraper with the correct settings

echo "🚀 LinkedIn Scraper - Quick Start"
echo "================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env from .env.example and add your credentials."
    exit 1
fi

echo "✅ .env file found"
echo ""

# Check if Chrome is installed
if ! command -v google-chrome &> /dev/null; then
    echo "❌ Error: Google Chrome not installed!"
    echo "Run: sudo apt-get install -y google-chrome-stable"
    exit 1
fi

echo "✅ Chrome installed: $(google-chrome --version)"
echo ""

# Menu
echo "Choose an option:"
echo "1) Use remote debugging (Chrome on Windows) - RECOMMENDED for WSL"
echo "2) Use Chrome in WSL (headless mode)"
echo "3) Use Chrome in WSL (with browser window)"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "📋 INSTRUCTIONS FOR REMOTE DEBUGGING:"
        echo "====================================="
        echo ""
        echo "1. On Windows PowerShell, run:"
        echo '   & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0 --user-data-dir="C:\temp\chrome-debug"'
        echo ""
        echo "2. Login to LinkedIn in that Chrome window"
        echo ""
        echo "3. Keep Chrome open and press Enter here to continue..."
        read
        
        # Get Windows IP
        WINDOWS_IP=$(ip route show | grep -i default | awk '{ print $3}')
        echo "Windows IP detected: $WINDOWS_IP"
        echo ""
        
        # Test connection
        echo "Testing connection to Chrome..."
        if curl -s --max-time 3 http://$WINDOWS_IP:9222/json/version > /dev/null; then
            echo "✅ Connected to Chrome!"
            echo ""
            read -p "Enter LinkedIn profile URL: " URL
            echo ""
            echo "🔍 Scraping profile..."
            python3 scraper.py --running True --port 9222 --host $WINDOWS_IP --url "$URL" --save True
        else
            echo "❌ Cannot connect to Chrome at $WINDOWS_IP:9222"
            echo ""
            echo "Troubleshooting:"
            echo "- Make sure Chrome is running with --remote-debugging-port=9222"
            echo "- Add firewall rule: New-NetFirewallRule -DisplayName 'Chrome Debug' -Direction Inbound -LocalPort 9222 -Protocol TCP -Action Allow"
            echo "- Try manually: python3 scraper.py --running True --port 9222 --host $WINDOWS_IP --url YOUR_URL --save True"
            exit 1
        fi
        ;;
    2)
        echo ""
        read -p "Enter LinkedIn profile URL: " URL
        echo ""
        echo "🔍 Scraping profile in headless mode..."
        python3 scraper.py --url "$URL" --save True --headless True
        ;;
    3)
        echo ""
        read -p "Enter LinkedIn profile URL: " URL
        echo ""
        echo "🔍 Scraping profile with browser window..."
        python3 scraper.py --url "$URL" --save True --headless False
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
if [ $? -eq 0 ]; then
    echo "✅ Scraping completed!"
    echo ""
    echo "📁 Output saved in: data/"
    ls -lh data/*.json 2>/dev/null | tail -3
else
    echo "❌ Scraping failed! Check app.log for details:"
    tail -20 app.log
fi
