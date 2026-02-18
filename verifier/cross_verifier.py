import re
from typing import Dict, List, Any
from fuzzywuzzy import fuzz

class CrossVerifier:
    def __init__(self, form_data: Dict, linkedin_data: Dict, resume_data: Dict):
        self.form = form_data
        self.linkedin = linkedin_data
        self.resume = resume_data
        self.discrepancies = []
        self.matches = []
        self.trust_score = 100

    def verify(self) -> Dict[str, Any]:
        """Run all verification checks and return report."""
        self._check_education()
        self._check_experience()
        self._check_projects()
        
        # Calculate final score
        # Start at 100, deduct for discrepancies, add (internal) weight for matches
        # Limit to 0-100
        self.trust_score = max(0, min(100, self.trust_score))
        
        return {
            "trust_score": self.trust_score,
            "discrepancies": self.discrepancies,
            "matches": self.matches,
            "summary": self._generate_summary()
        }

    def _generate_summary(self) -> str:
        if self.trust_score >= 90:
            return "High data consistency across all sources."
        elif self.trust_score >= 70:
            return "Mostly consistent, with some minor missing details."
        else:
            return "Significant discrepancies found. Important claims not verified in external sources."

    def _fuzzy_match(self, str1: str, str2: str, threshold: int = 80) -> bool:
        if not str1 or not str2:
            return False
        return fuzz.token_sort_ratio(str1.lower(), str2.lower()) >= threshold

    def _check_education(self):
        """Verify education claims."""
        form_school = self.form.get("education_school")
        if not form_school:
            return

        # Check LinkedIn
        li_schools = [edu.get("school", "") for edu in self.linkedin.get("education", [])]
        li_match = any(self._fuzzy_match(form_school, s) for s in li_schools)

        # Check Resume
        res_text = self.resume.get("raw_text", "")
        # Heuristic: School name should appear in resume text
        res_match = form_school.lower() in res_text.lower() or \
                    any(self._fuzzy_match(form_school, s) for s in self.resume.get("education", []))

        if li_match and res_match:
            self.matches.append(f"Education '{form_school}' verified on LinkedIn and Resume.")
        elif li_match:
             self.matches.append(f"Education '{form_school}' verified on LinkedIn.")
        elif res_match:
             self.matches.append(f"Education '{form_school}' verified on Resume.")
        else:
            self.discrepancies.append(f"CRITICAL: Education '{form_school}' claimed in form but NOT found in LinkedIn or Resume.")
            self.trust_score -= 20

    def _check_experience(self):
        """Verify current role/startup."""
        current_role = self.form.get("current_role")
        startup_name = self.form.get("startup_name")
        
        if not startup_name:
            return

        # Check LinkedIn Experience
        li_experiences = self.linkedin.get("experience", [])
        
        # 1. Check if startup name exists in LI
        found_company = False
        for exp in li_experiences:
            company = exp.get("company", "")
            if self._fuzzy_match(startup_name, company):
                found_company = True
                # Check role if company found
                role = exp.get("title", "")
                if current_role and self._fuzzy_match(current_role, role):
                     self.matches.append(f"Role '{current_role}' at '{startup_name}' verified on LinkedIn.")
                elif current_role:
                     self.matches.append(f"Company '{startup_name}' verified on LinkedIn, but role '{current_role}' mismatch (Found: {role}).")
                     self.trust_score -= 5 # Minor deduction for title mismatch
                break
        
        if not found_company:
            # Check Resume
            res_text = self.resume.get("raw_text", "").lower()
            if startup_name.lower() in res_text:
                self.matches.append(f"Startup '{startup_name}' found in Resume (but not LinkedIn).")
            else:
                self.discrepancies.append(f"WARNING: Startup '{startup_name}' not found in LinkedIn experience OR Resume.")
                self.trust_score -= 15

    def get_employer_locations(self) -> list:
        """Return list of location strings from LinkedIn experience entries."""
        return [
            exp.get("location", "")
            for exp in self.linkedin.get("experience", [])
            if exp.get("location")
        ]

    def _check_projects(self):
        """Check if 'built' things appear in GitHub or Resume."""
        projects_text = self.form.get("projects", "")
        if len(projects_text) < 10: 
            return
        
        res_text = self.resume.get("raw_text", "").lower()
        
        # Fallback to simple trust deduction if major project claimed but Resume is empty/sparse
        if len(res_text) < 200 and len(projects_text) > 200:
             self.discrepancies.append("Detailed projects in form but Resume is very sparse.")
             self.trust_score -= 10
