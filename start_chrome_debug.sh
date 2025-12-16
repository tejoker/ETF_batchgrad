#!/bin/bash
# Starts Google Chrome in remote debugging mode
# Adjust the executable name if necessary (google-chrome, google-chrome-stable, chromium-browser)

CHROME_BIN="google-chrome"

if ! command -v $CHROME_BIN &> /dev/null; then
    CHROME_BIN="google-chrome-stable"
fi

if ! command -v $CHROME_BIN &> /dev/null; then
    CHROME_BIN="chromium-browser"
fi

echo "Starting Chrome with remote debugging on port 9222..."
"$CHROME_BIN" --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-debug-profile" &
