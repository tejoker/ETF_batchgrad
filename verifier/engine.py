from typing import Dict, Any, List, Optional
from fuzzywuzzy import fuzz


class VerificationEngine:
    def __init__(
        self,
        resume_data: Dict[str, Any],
        github_data: Dict[str, Any],
        website_data: Optional[Dict[str, Any]] = None
    ):
        self.resume = resume_data
        self.github = github_data
        self.website = website_data or {}
        self.report = {
            "score": 0,
            "checks": [],
            "summary": ""
        }

    def verify(self) -> Dict[str, Any]:
        """Run all verification checks."""
        self._verify_identity()
        self._verify_company()
        self._verify_skills()
        self._verify_website()
        self._calculate_score()
        return self.report

    def _verify_identity(self):
        """Check if names match."""
        resume_name = self.resume.get("name", "")
        github_name = self.github.get("profile", {}).get("name", "")

        match_score = fuzz.token_sort_ratio(resume_name, github_name)
        status = "PASS" if match_score > 80 else "WARN" if match_score > 50 else "FAIL"

        self.report["checks"].append({
            "category": "Identity",
            "item": "Name Match",
            "resume_value": resume_name,
            "github_value": github_name,
            "match_score": match_score,
            "status": status
        })

    def _verify_company(self):
        """Check if current company matches."""
        github_company = self.github.get("profile", {}).get("company", "")
        if not github_company:
            return

        clean_gh_company = github_company.replace("@", "").strip()
        experience_text = " ".join(self.resume.get("experience", []))

        match_score = fuzz.partial_ratio(clean_gh_company.lower(), experience_text.lower())
        status = "PASS" if match_score > 80 else "WARN"

        self.report["checks"].append({
            "category": "Professional",
            "item": "Company Match",
            "resume_value": "See Experience Section",
            "github_value": github_company,
            "match_score": match_score,
            "status": status,
            "details": f"Checked for '{clean_gh_company}' in resume experience."
        })

    def _verify_skills(self):
        """Verify claimed skills against GitHub languages and topics."""
        resume_skills = self.resume.get("skills", [])
        flat_resume_skills = []
        for line in resume_skills:
            parts = [s.strip() for s in line.split(',')]
            flat_resume_skills.extend(parts)

        github_skills = set()
        for repo in self.github.get("repositories", []):
            if repo.get("language"):
                github_skills.add(repo.get("language").lower())

        matched_skills = []
        unverified_skills = []

        for skill in flat_resume_skills:
            if not skill:
                continue
            skill_lower = skill.lower()
            found = False
            for gh_skill in github_skills:
                if fuzz.ratio(skill_lower, gh_skill) > 85:
                    matched_skills.append(skill)
                    found = True
                    break
            if not found:
                unverified_skills.append(skill)

        if flat_resume_skills:
            verification_rate = len(matched_skills) / len(flat_resume_skills) * 100
            status = "PASS" if verification_rate > 50 else "WARN"
        else:
            verification_rate = 0
            status = "INFO"

        self.report["checks"].append({
            "category": "Skills",
            "item": "Skill Verification",
            "resume_value": f"{len(flat_resume_skills)} skills listed",
            "github_value": f"{len(github_skills)} languages found",
            "match_score": int(verification_rate),
            "status": status,
            "details": f"Verified: {', '.join(matched_skills[:5])}..."
        })

    def _verify_website(self):
        """Cross-check personal website against resume name and GitHub company."""
        if not self.website or self.website.get("error"):
            return

        resume_name = self.resume.get("name", "")
        website_name = self.website.get("name") or ""

        # Name check
        if resume_name and website_name:
            match_score = fuzz.token_sort_ratio(resume_name.lower(), website_name.lower())
            status = "PASS" if match_score > 75 else "WARN"
            self.report["checks"].append({
                "category": "Website",
                "item": "Name Match",
                "resume_value": resume_name,
                "website_value": website_name,
                "match_score": match_score,
                "status": status
            })

        # Company mention check
        github_company = self.github.get("profile", {}).get("company", "")
        if github_company:
            clean_company = github_company.replace("@", "").strip()
            companies_text = " ".join(self.website.get("companies", []))
            match_score = fuzz.partial_ratio(clean_company.lower(), companies_text.lower())
            self.report["checks"].append({
                "category": "Website",
                "item": "Company Mention",
                "github_value": github_company,
                "website_value": companies_text[:80],
                "match_score": match_score,
                "status": "PASS" if match_score > 70 else "INFO"
            })

    def _calculate_score(self):
        """Calculate overall trust score."""
        total_score = 0
        count = 0
        for check in self.report["checks"]:
            if check["category"] == "Identity":
                total_score += check["match_score"] * 2
                count += 2
            elif check["category"] == "Website":
                # Website checks are supplementary — half weight
                total_score += check["match_score"] * 0.5
                count += 0.5
            else:
                total_score += check["match_score"]
                count += 1

        self.report["score"] = int(total_score / count) if count > 0 else 0

        if self.report["score"] > 80:
            self.report["summary"] = "High Trust: Resume aligns well with public GitHub profile."
        elif self.report["score"] > 50:
            self.report["summary"] = "Medium Trust: Some discrepancies found, worth manual review."
        else:
            self.report["summary"] = "Low Trust: Significant mismatch between Resume and GitHub."
