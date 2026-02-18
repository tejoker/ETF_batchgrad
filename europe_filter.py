from typing import Dict, List, Tuple
import pandas as pd
from fuzzywuzzy import fuzz


class EuropeFilter:
    # Copied from add_region_column.py
    EUROPEAN_COUNTRIES = {
        "Albania", "Andorra", "Armenia", "Austria", "Azerbaijan", "Belarus",
        "Belgium", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus",
        "Czech Republic", "Czechia", "Denmark", "Estonia", "Finland", "France",
        "Georgia", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
        "Kazakhstan", "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg",
        "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands", "North Macedonia",
        "Norway", "Poland", "Portugal", "Romania", "Russia", "San Marino", "Serbia",
        "Slovakia", "Slovak Republic", "Slovenia", "Spain", "Sweden", "Switzerland",
        "Turkey", "Ukraine", "United Kingdom", "UK", "Vatican City"
    }

    # Common European cities mapped to country — expands location string matching
    CITY_TO_COUNTRY = {
        "paris": "France", "lyon": "France", "marseille": "France", "toulouse": "France",
        "bordeaux": "France", "lille": "France", "nice": "France", "nantes": "France",
        "strasbourg": "France", "rennes": "France", "grenoble": "France", "montpellier": "France",
        "london": "United Kingdom", "manchester": "United Kingdom", "birmingham": "United Kingdom",
        "edinburgh": "United Kingdom", "glasgow": "United Kingdom", "bristol": "United Kingdom",
        "cambridge": "United Kingdom", "oxford": "United Kingdom", "leeds": "United Kingdom",
        "berlin": "Germany", "munich": "Germany", "hamburg": "Germany", "frankfurt": "Germany",
        "cologne": "Germany", "düsseldorf": "Germany", "dusseldorf": "Germany",
        "stuttgart": "Germany", "dresden": "Germany", "leipzig": "Germany",
        "amsterdam": "Netherlands", "rotterdam": "Netherlands", "hague": "Netherlands",
        "madrid": "Spain", "barcelona": "Spain", "valencia": "Spain", "seville": "Spain",
        "bilbao": "Spain", "zaragoza": "Spain",
        "rome": "Italy", "milan": "Italy", "naples": "Italy", "turin": "Italy",
        "florence": "Italy", "bologna": "Italy", "venice": "Italy",
        "zurich": "Switzerland", "geneva": "Switzerland", "bern": "Switzerland",
        "lausanne": "Switzerland", "basel": "Switzerland",
        "stockholm": "Sweden", "gothenburg": "Sweden", "malmo": "Sweden",
        "oslo": "Norway", "bergen": "Norway",
        "copenhagen": "Denmark", "aarhus": "Denmark",
        "helsinki": "Finland", "tampere": "Finland",
        "brussels": "Belgium", "antwerp": "Belgium", "ghent": "Belgium",
        "vienna": "Austria", "graz": "Austria", "salzburg": "Austria",
        "warsaw": "Poland", "krakow": "Poland", "wroclaw": "Poland",
        "prague": "Czech Republic", "brno": "Czech Republic",
        "budapest": "Hungary",
        "bucharest": "Romania", "cluj": "Romania",
        "athens": "Greece", "thessaloniki": "Greece",
        "lisbon": "Portugal", "porto": "Portugal",
        "dublin": "Ireland", "cork": "Ireland",
        "kiev": "Ukraine", "kyiv": "Ukraine",
        "moscow": "Russia", "saint petersburg": "Russia",
        "istanbul": "Turkey", "ankara": "Turkey",
        "reykjavik": "Iceland",
        "luxembourg": "Luxembourg",
        "valletta": "Malta",
        "nicosia": "Cyprus",
        "tallinn": "Estonia", "riga": "Latvia", "vilnius": "Lithuania",
        "bratislava": "Slovakia", "ljubljana": "Slovenia", "zagreb": "Croatia",
        "belgrade": "Serbia", "sarajevo": "Bosnia and Herzegovina",
        "sofia": "Bulgaria", "skopje": "North Macedonia", "tirana": "Albania",
        "chisinau": "Moldova", "minsk": "Belarus", "tbilisi": "Georgia",
        "yerevan": "Armenia", "baku": "Azerbaijan"
    }

    def __init__(self, world_df: pd.DataFrame):
        self.world_df = world_df

    def _normalize(self, s: str) -> str:
        return s.strip().lower()

    def check_location(self, location_str: str) -> bool:
        """
        Return True if location_str indicates a European location.
        Splits by comma, checks each token against EUROPEAN_COUNTRIES and CITY_TO_COUNTRY.
        """
        if not location_str or not isinstance(location_str, str):
            return False

        parts = [p.strip() for p in location_str.replace(";", ",").split(",")]
        for part in parts:
            part_lower = self._normalize(part)
            # Direct country match (case-insensitive)
            if any(part_lower == c.lower() for c in self.EUROPEAN_COUNTRIES):
                return True
            # City match
            if part_lower in self.CITY_TO_COUNTRY:
                return True
            # Check if any European country name is a substring of the part
            for country in self.EUROPEAN_COUNTRIES:
                if country.lower() in part_lower:
                    return True
        return False

    def check_university(self, school_name: str) -> bool:
        """
        Return True if the university is in Europe according to the world rankings CSV.
        Uses fuzzy matching (same logic as Grader._fuzzy_match_school).
        """
        if not school_name or not isinstance(school_name, str) or school_name.strip() == "":
            return False

        best_match = None
        best_score = 0

        for name in self.world_df["University Name"].dropna():
            score = fuzz.token_sort_ratio(school_name.lower(), name.lower())
            if score > best_score:
                best_score = score
                best_match = name

        if best_score > 80 and best_match is not None:
            try:
                region = self.world_df[
                    self.world_df["University Name"] == best_match
                ]["Region"].iloc[0]
                return region == "Europe"
            except (IndexError, KeyError):
                return False

        return False

    def check_employer(self, linkedin_data: Dict) -> bool:
        """
        Return True if any LinkedIn experience entry has a European location.
        """
        for exp in linkedin_data.get("experience", []):
            loc = exp.get("location", "")
            if loc and self.check_location(loc):
                return True
        return False

    def is_eligible(self, row: "pd.Series", linkedin_data: Dict) -> Tuple[bool, str]:
        """
        Check all three criteria (OR logic). Returns (eligible, reason_string).

        reason_string examples:
          "passed: current_location (Paris, France)"
          "passed: university (Ecole Polytechnique)"
          "passed: employer_location (London, UK)"
          "rejected: all criteria non-European"
        """
        # 1. Current location from form data or LinkedIn profile location
        current_location = row.get("currentLocation", "") or row.get("city", "") or ""
        if not current_location:
            # Try to get location from LinkedIn data if available
            current_location = linkedin_data.get("location", "") or ""

        if current_location and self.check_location(str(current_location)):
            return True, f"passed: current_location ({current_location})"

        # 2. University location
        school = (
            row.get("education.degreeFields1")
            or row.get("education.pleaseSpecify")
            or row.get("education.degreeFields", "")
        )
        if school and self.check_university(str(school)):
            return True, f"passed: university ({school})"

        # 3. Employer location (from LinkedIn experience entries)
        if self.check_employer(linkedin_data):
            # Find the matching location for the reason string
            for exp in linkedin_data.get("experience", []):
                loc = exp.get("location", "")
                if loc and self.check_location(loc):
                    return True, f"passed: employer_location ({loc})"
            return True, "passed: employer_location"

        return False, "rejected: all criteria non-European"
