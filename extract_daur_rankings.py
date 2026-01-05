import json
import csv
import re
from html import unescape

INPUT_FILE = 'daur_page.html'
OUTPUT_FILE = 'daur_rankings_2024.csv'

def extract_rankings():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Regex to find the NEXT_DATA script tag
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content)
        if not match:
            print("Error: Could not find __NEXT_DATA__ script tag.")
            return

        json_str = match.group(1)
        data = json.loads(json_str)
        
        # Navigate to the rankings data
        # Based on inspection: props -> pageProps -> data -> list of schools
        try:
            rankings = data['props']['pageProps']['data']
        except KeyError as e:
            print(f"Error: Unexpected JSON structure. Key not found: {e}")
            # print(json.dumps(data, indent=2)) # Debug if needed
            return

        print(f"Found {len(rankings)} entries.")
        
        # Sort by rank just in case
        rankings.sort(key=lambda x: x.get('rank', 9999))

        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Rank', 'Name', 'Grade', 'Notation'])
            
            for school in rankings:
                rank = school.get('rank')
                name = school.get('school_name')
                # 'final_grade' seems to be a float like 0.95. Convert to score out of 100 if needed or keep as is.
                # The HTML table showed "95". So 0.95 * 100.
                final_grade_raw = school.get('final_grade')
                grade = round(final_grade_raw * 100, 2) if final_grade_raw is not None else ''
                notation = school.get('notation')
                
                writer.writerow([rank, name, grade, notation])
                
        print(f"Successfully wrote rankings to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    extract_rankings()
