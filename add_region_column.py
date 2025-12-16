import csv
import sys
import os

def get_region(country):
    europe_countries = [
        "Albania", "Andorra", "Armenia", "Austria", "Azerbaijan", "Belarus", "Belgium", "Bosnia and Herzegovina",
        "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Estonia", "Finland", "France", "Georgia",
        "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Kazakhstan", "Kosovo", "Latvia", "Liechtenstein",
        "Lithuania", "Luxembourg", "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands", "North Macedonia", "Norway",
        "Poland", "Portugal", "Romania", "Russia", "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain", "Sweden",
        "Switzerland", "Turkey", "Ukraine", "United Kingdom", "Vatican City", "UK", "Czechia", "Slovak Republic"
    ]
    
    if not country:
        return "Unknown"
    
    # Normalize country name slightly if needed (e.g. UK vs United Kingdom)
    if country == "UK":
        country = "United Kingdom"
    if country == "USA" or country == "US":
        return "Outside Europe"
        
    if country in europe_countries:
        return "Europe"
    else:
        return "Outside Europe"


def load_csv_to_dict(filename, key_col, val_col, skip_header=True):
    mapping = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader) if skip_header else None
            
            if header:
                try:
                    key_idx = header.index(key_col)
                    val_idx = header.index(val_col)
                except ValueError:
                    print(f"Warning: Columns {key_col} or {val_col} not found in {filename} header: {header}")
                    return {}
            else:
                return {} 
                
            for row in reader:
                if len(row) > max(key_idx, val_idx):
                    # Strip the key to ensure better matching
                    key = row[key_idx].strip()
                    mapping[key] = row[val_idx]
    except FileNotFoundError:
        print(f"Warning: {filename} not found.")
    return mapping

def main():
    # Load QS Data
    print("Loading qs-world-rankings-2025.csv...")
    qs_mapping = load_csv_to_dict('qs-world-rankings-2025.csv', 'Institution Name', 'Location Full')

    # Load CWUR Data
    print("Loading cwurData.csv...")
    cwur_mapping = load_csv_to_dict('cwurData.csv', 'institution', 'country')

    # Manual matches for known tricky ones
    manual_mapping = {
        "ETH Zurich": "Switzerland",
        "Swiss Federal Institute of Technology Lausanne": "Switzerland",
        "Paris-Saclay University": "France",
        "PSL University": "France",
        "Sorbonne University": "France",
        "Institut Polytechnique de Paris": "France",
        "Université Paris-Saclay": "France",
        "Université PSL": "France",
        "Paris Sciences et Lettres – PSL Research University Paris": "France",
        "LMU Munich": "Germany",
        "University of Munich": "Germany",
        "Technical University of Munich": "Germany",
        "Heidelberg University": "Germany",
        "Humboldt University of Berlin": "Germany",
        "Charité - Universitätsmedizin Berlin": "Germany",
        "Free University of Berlin": "Germany",
        "Freie Universitaet Berlin": "Germany",
        "KIT, Karlsruhe Institute of Technology": "Germany",
        "Technische Universität Berlin (TU Berlin)": "Germany",
        "Technische Universität Dresden": "Germany",
        "RWTH Aachen University": "Germany",
        "University of Tübingen": "Germany",
        "University of Freiburg": "Germany",
        "University of Bonn": "Germany",
        "University of Goettingen": "Germany",
        "University of Hamburg": "Germany",
        "University of Muenster": "Germany",
        "University of Cologne": "Germany",
        "University of Mannheim": "Germany",
        "University of Würzburg": "Germany",
        "University of Erlangen-Nuremberg": "Germany",
        "University of Kiel": "Germany",
        "University of Mainz": "Germany",
        "University of Leipzig": "Germany",
        "University of Bremen": "Germany",
        "University of Ulm": "Germany",
        "University of Stuttgart": "Germany",
        "University of Regensburg": "Germany",
        "University of Konstanz": "Germany",
        "University of Bayreuth": "Germany",
        "University of Jena": "Germany",
        "University of Rostock": "Germany",
        "University of Marburg": "Germany",
        "University of Giessen": "Germany", 
        "University of Potsdam": "Germany",
        "University of Dusseldorf": "Germany",
        "University of Duisburg-Essen": "Germany",
        "University of Bochum": "Germany",
        "Imperial College London": "United Kingdom",
        "UCL": "United Kingdom",
        "London School of Economics and Political Science": "United Kingdom",
        "King's College London": "United Kingdom",
        "The University of Edinburgh": "United Kingdom",
        "The University of Manchester": "United Kingdom",
        "The University of Warwick": "United Kingdom",
        "The University of Bristol": "United Kingdom",
        "The University of Glasgow": "United Kingdom",
        "The University of Sheffield": "United Kingdom",
        "The University of Birmingham": "United Kingdom",
        "The University of Leeds": "United Kingdom", 
        "The University of Nottingham": "United Kingdom",
        "The University of Southampton": "United Kingdom",
        "London School of Hygiene & Tropical Medicine": "United Kingdom"
    }

    # Load Main Data
    print("Loading average_ranking.csv...")
    input_file = 'average_ranking.csv'
    output_file = 'average_ranking_with_region.csv'
    
    try:
        with open(input_file, 'r', encoding='utf-8') as fin, \
             open(output_file, 'w', encoding='utf-8', newline='') as fout:
            
            reader = csv.DictReader(fin)
            # Ensure unique fieldnames if we run multiple times, but here we just construct fresh
            fieldnames = reader.fieldnames + ['Country', 'Region']
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()
            
            found_count = 0
            missing_count = 0
            
            region_counts = {"Europe": 0, "Outside Europe": 0, "Unknown": 0}

            for row in reader:
                uni_name = row['University Name']
                country = None
                
                uni_name_clean = uni_name.strip()
                
                # Priority 1: Manual Mapping
                if uni_name_clean in manual_mapping:
                    country = manual_mapping[uni_name_clean]
                
                # Priority 2: Direct Match
                if not country and uni_name_clean in qs_mapping:
                    country = qs_mapping[uni_name_clean]
                if not country and uni_name_clean in cwur_mapping:
                    country = cwur_mapping[uni_name_clean]
                
                # Priority 3: Try removing "The " prefix
                if not country:
                    if uni_name_clean.startswith("The "):
                        no_the = uni_name_clean[4:]
                        if no_the in qs_mapping:
                            country = qs_mapping[no_the]
                        elif no_the in cwur_mapping:
                            country = cwur_mapping[no_the]
                            
                # Priority 4: Try removing quotes
                if not country:
                    cleaner_name = uni_name_clean.replace('"', '')
                    if cleaner_name in qs_mapping:
                        country = qs_mapping[cleaner_name]
                    elif cleaner_name in cwur_mapping:
                        country = cwur_mapping[cleaner_name]
                
                # Priority 5: Partial match / Contains (Risky, use carefully or skip)
                # Let's skip risking false positives for now, unless we want to search in keys
                
                if country:
                    found_count += 1
                else:
                    missing_count += 1
                
                region = get_region(country)
                region_counts[region] += 1
                
                row['Country'] = country if country else ""
                row['Region'] = region
                writer.writerow(row)

            print(f"Processed universities.")
            print(f"Found country for {found_count} universities.")
            print(f"Missing country for {missing_count} universities.")
            print(f"Results saved to {output_file}")
            print("\nRegion Distribution:")
            print(region_counts)

    except FileNotFoundError:
        print(f"Error: {input_file} not found.")

if __name__ == "__main__":
    main()
