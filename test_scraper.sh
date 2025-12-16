#!/bin/bash
# LinkedIn Scraper Test Script
# This script tests the improved LinkedIn scraper

echo "==================================="
echo "LinkedIn Scraper Test"
echo "==================================="
echo ""

# Check if Chrome is running in debug mode
if ! pgrep -f "google-chrome.*9222" > /dev/null; then
    echo "❌ Chrome is not running in debug mode on port 9222"
    echo ""
    echo "Please run this command first in a separate terminal:"
    echo "  google-chrome --remote-debugging-port=9222 --user-data-dir=\"~/.config/google-chrome\""
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Chrome is running in debug mode"
echo ""

# Test profile URL
TEST_URL="https://www.linkedin.com/in/louise-scarlette-maunoir/"

echo "Testing with profile: $TEST_URL"
echo ""
echo "Running scraper..."
echo ""

# Run the scraper
python3 scraper.py --running True --port 9222 --url "$TEST_URL" --save True --debug True

# Check results
if [ $? -eq 0 ]; then
    echo ""
    echo "==================================="
    echo "✅ Scraper completed successfully!"
    echo "==================================="
    echo ""
    echo "Checking results..."
    echo ""
    
    # Extract filename from URL
    FILENAME=$(echo "$TEST_URL" | sed 's/.*\/in\///' | sed 's/\///' | sed 's/$/\.json/')
    
    if [ -f "data/$FILENAME" ]; then
        echo "Output file: data/$FILENAME"
        echo ""
        echo "--- Preview ---"
        cat "data/$FILENAME" | head -30
        echo ""
        echo "--- Summary ---"
        echo "Name: $(cat data/$FILENAME | jq -r '.name // "null"')"
        echo "Headline: $(cat data/$FILENAME | jq -r '.headline // "null"')"
        echo "Location: $(cat data/$FILENAME | jq -r '.location // "null"')"
        echo "Experience entries: $(cat data/$FILENAME | jq '.experience | length')"
        echo "Education entries: $(cat data/$FILENAME | jq '.education | length')"
        echo "Skills entries: $(cat data/$FILENAME | jq '.skills | length')"
    else
        echo "⚠️  Output file not found: data/$FILENAME"
    fi
else
    echo ""
    echo "==================================="
    echo "❌ Scraper failed!"
    echo "==================================="
    echo ""
    echo "Check app.log for errors:"
    echo "  cat app.log | tail -50"
fi
