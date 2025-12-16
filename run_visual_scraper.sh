#!/bin/bash
# Example usage of the visual scraper using the connected debug browser
# Usage: ./run_visual_scraper.sh <PROFILE_URL>

if [ -z "$1" ]; then
    echo "Usage: ./run_visual_scraper.sh <PROFILE_URL>"
    exit 1
fi

python3 visual_scraper.py --running --url "$1"
