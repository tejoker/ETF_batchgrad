import re
from typing import Dict, List, Any, Optional
from pypdf import PdfReader


class ResumeParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.sections = {
            "skills": [],
            "experience": [],
            "education": []
        }

    def extract_text(self) -> str:
        """Extract text from the PDF file. Tries pdfplumber first (layout-aware), falls back to pypdf."""
        # Primary: pdfplumber (handles two-column layouts, tables)
        try:
            import pdfplumber
            with pdfplumber.open(self.pdf_path) as pdf:
                pages = []
                for page in pdf.pages:
                    text = page.extract_text(layout=True)
                    if text:
                        pages.append(text)
                result = "\n".join(pages)
                if result.strip():
                    self.text = result
                    return self.text
        except Exception as e:
            print(f"[Parser] pdfplumber failed: {e}, falling back to pypdf")

        # Fallback: pypdf
        try:
            reader = PdfReader(self.pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            self.text = text
            return text
        except Exception as e:
            print(f"[Parser] Error reading PDF: {e}")
            return ""

    def _extract_name_from_top(self, lines: List[str]) -> Optional[str]:
        """Scan first 10 lines for a name pattern (two+ capitalized words, no digits, under 50 chars)."""
        name_pattern = re.compile(
            r'^[A-Z\u00C0-\u017E][a-z\u00C0-\u017E\-]+'
            r'( [A-Z\u00C0-\u017E][a-z\u00C0-\u017E\-]+)+'
            r'$'
        )
        for line in lines[:10]:
            clean = line.strip()
            if not clean or len(clean) > 50:
                continue
            if re.search(r'\d', clean):
                continue
            if name_pattern.match(clean):
                return clean
        return None

    def parse(self) -> Dict[str, Any]:
        """Parse the extracted text into structured data."""
        if not self.text:
            self.extract_text()

        lines = self.text.split('\n')

        # 1. Extract Name
        name = self._extract_name_from_top(lines)
        if not name:
            # Fallback: first non-empty line
            for line in lines:
                if line.strip():
                    name = line.strip()
                    break
        name = name or ""

        # 2. Extract Skills
        self._extract_section("skills", [
            "skills", "technologies", "competencies",
            "compétences", "fähigkeiten", "habilidades",
            "technical skills", "core competencies", "tech stack",
            "outils", "langages", "langages de programmation"
        ])

        # 3. Extract Experience
        self._extract_section("experience", [
            "experience", "employment", "work history",
            "professional experience", "work experience",
            "expérience", "expérience professionnelle",
            "berufserfahrung", "experiencia", "parcours professionnel"
        ])

        # 4. Extract Education
        self._extract_section("education", [
            "education", "academic", "academic background",
            "formation", "études", "diplômes",
            "ausbildung", "educación", "degrees", "qualifications"
        ])

        return {
            "name": name,
            "skills": self.sections["skills"],
            "experience": self.sections["experience"],
            "education": self.sections["education"],
            "links": self.extract_links(),
            "raw_text": self.text
        }

    def extract_links(self) -> Dict[str, Optional[str]]:
        """Extract GitHub, LinkedIn, and personal website URLs."""
        links: Dict[str, Optional[str]] = {"github": None, "linkedin": None, "website": None}

        gh_match = re.search(r'github\.com/([a-zA-Z0-9_\-]+)', self.text, re.IGNORECASE)
        if gh_match:
            links["github"] = gh_match.group(1)

        li_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_\-]+)', self.text, re.IGNORECASE)
        if li_match:
            links["linkedin"] = li_match.group(1)

        # Personal website: any http(s) URL that is not github/linkedin/twitter/facebook/scholar
        web_match = re.search(
            r'https?://(?!(?:www\.)?(?:github|linkedin|twitter|facebook|scholar\.google|researchgate|orcid|doi|arxiv))'
            r'[a-zA-Z0-9\-\.]+\.[a-z]{2,}(?:/[^\s]*)?',
            self.text,
            re.IGNORECASE
        )
        if web_match:
            links["website"] = web_match.group(0).rstrip('.,;)')

        return links

    def _extract_section(self, section_name: str, keywords: List[str]):
        """Helper to extract a section based on keywords."""
        lines = self.text.split('\n')
        in_section = False
        captured_lines = []

        # All known section stop-words (expanded to include multilingual variants)
        stop_words = [
            "education", "experience", "skills", "projects", "languages",
            "volunteering", "certifications", "publications", "awards", "honors",
            "formation", "expérience", "compétences", "projets", "langues",
            "ausbildung", "berufserfahrung", "fähigkeiten", "projekte",
            "educación", "experiencia", "habilidades", "proyectos", "idiomas",
            "interests", "hobbies", "references", "summary", "objective",
            "profil", "résumé", "about"
        ]

        for line in lines:
            clean_line = line.strip().lower()

            is_header = any(keyword in clean_line for keyword in keywords) and len(clean_line) < 40

            if is_header:
                in_section = True
                continue

            if in_section and any(h in clean_line for h in stop_words if h not in keywords) and len(clean_line) < 40:
                in_section = False

            if in_section and line.strip():
                captured_lines.append(line.strip())

        self.sections[section_name] = captured_lines
