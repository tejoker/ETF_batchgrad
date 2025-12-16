import csv
import re
import statistics

# Configuration
INPUT_ARWU = 'all_years_combined.csv'
INPUT_QS = 'qs-world-rankings-2025.csv'
INPUT_THE = 'rankings/THE_2024.csv'
OUTPUT_FILE = 'average_ranking.csv'

def normalize_name(name):
    """
    Normalizes university names for matching.
    """
    if not name:
        return ""
    name = name.lower()
    # Remove text in parentheses (often acronyms or locations)
    name = re.sub(r'\(.*?\)', '', name)
    # Replace non-alphanumeric with spaces
    name = re.sub(r'[^a-z0-9]', ' ', name)
    # Collapse multiple spaces
    name = ' '.join(name.split())
    return name.strip()

def clean_rank(rank_str):
    """
    Cleans rank strings and extracts the first integer found.
    """
    if not rank_str:
        return None
    rank_str = str(rank_str).strip()
    if not rank_str:
        return None
    match = re.search(r'(\d+)', rank_str)
    if match:
        return int(match.group(1))
    return None

def load_arwu(filepath):
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('name')
            rank = row.get('rank')
            if name and rank:
                norm = normalize_name(name)
                clean = clean_rank(rank)
                if clean:
                    data[norm] = {'name': name, 'rank': clean}
    return data

def load_qs(filepath):
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Institution Name')
            rank = row.get('2025 Rank')
            
            # Helper to handle BOM or slight header variations
            if not rank and reader.fieldnames:
                 for key in reader.fieldnames:
                     if '2025 Rank' in key:
                         rank = row.get(key)
                         break

            if name and rank:
                norm = normalize_name(name)
                clean = clean_rank(rank)
                if clean:
                    data[norm] = {'name': name, 'rank': clean}
    return data

def load_the(filepath):
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('name')
            rank = row.get('rank')
            if name and rank:
                norm = normalize_name(name)
                clean = clean_rank(rank)
                if clean:
                    data[norm] = {'name': name, 'rank': clean}
    return data

def main():
    print("Loading datasets...")
    arwu_data = load_arwu(INPUT_ARWU)
    qs_data = load_qs(INPUT_QS)
    the_data = load_the(INPUT_THE)

    print(f"Loaded {len(arwu_data)} ARWU entries")
    print(f"Loaded {len(qs_data)} QS entries")
    print(f"Loaded {len(the_data)} THE entries")

    all_keys = set(arwu_data.keys()) | set(qs_data.keys()) | set(the_data.keys())
    
    merged_list = []

    for key in all_keys:
        # Prefer names in order: QS (often clean), THE, ARWU
        display_name = ""
        if key in qs_data: display_name = qs_data[key]['name']
        elif key in the_data: display_name = the_data[key]['name']
        elif key in arwu_data: display_name = arwu_data[key]['name']

        ranks = []
        arwu_r = arwu_data.get(key, {}).get('rank')
        qs_r = qs_data.get(key, {}).get('rank')
        the_r = the_data.get(key, {}).get('rank')

        if arwu_r: ranks.append(arwu_r)
        if qs_r: ranks.append(qs_r)
        if the_r: ranks.append(the_r)

        if not ranks:
            continue

        mean_val = statistics.mean(ranks)
        median_val = statistics.median(ranks)

        merged_list.append({
            'University Name': display_name,
            'QS Rank': qs_r if qs_r else '',
            'THE Rank': the_r if the_r else '',
            'ARWU Rank': arwu_r if arwu_r else '',
            'Mean Rank': round(mean_val, 2),
            'Median Rank': median_val,
            'Source Count': len(ranks)
        })

    merged_list.sort(key=lambda x: x['Mean Rank'])

    print(f"Writing {len(merged_list)} entries to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['University Name', 'QS Rank', 'THE Rank', 'ARWU Rank', 'Mean Rank', 'Median Rank', 'Source Count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_list)

    print("Done.")

if __name__ == "__main__":
    main()
