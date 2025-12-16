import re
from typing import Dict, List, Any
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
        """Extract text from the PDF file."""
        try:
            reader = PdfReader(self.pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            self.text = text
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    def parse(self) -> Dict[str, Any]:
        """Parse the extracted text into structured data."""
        if not self.text:
            self.extract_text()
        
        # Basic parsing logic (heuristic based)
        lines = self.text.split('\n')
        
        # 1. Extract Name (Heuristic: First line usually, or capitalized words at top)
        # For simplicity, we'll assume the first non-empty line is the name
        name = ""
        for line in lines:
            clean_line = line.strip()
            if clean_line:
                name = clean_line
                break
        
        # 2. Extract Skills (Look for 'Skills' keyword and following lines)
        self._extract_section("skills", ["skills", "technologies", "competencies"])
        
        # 3. Extract Experience (Look for 'Experience' keyword)
        self._extract_section("experience", ["experience", "employment", "work history"])
        
        # 4. Extract Education
        self._extract_section("education", ["education", "academic"])

        return {
            "name": name,
            "skills": self.sections["skills"],
            "experience": self.sections["experience"],
            "education": self.sections["education"],
            "links": self.extract_links(),
            "raw_text": self.text
        }

    def extract_links(self) -> Dict[str, str]:
        """Extract GitHub and LinkedIn profiles."""
        links = {"github": None, "linkedin": None}
        
        # Regex for GitHub username (simple match)
        # Matches github.com/username (ignoring trailing slash)
        gh_match = re.search(r'github\.com/([a-zA-Z0-9-]+)', self.text, re.IGNORECASE)
        if gh_match:
            links["github"] = gh_match.group(1)
            
        # Regex for LinkedIn
        # Matches linkedin.com/in/username
        li_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', self.text, re.IGNORECASE)
        if li_match:
            links["linkedin"] = li_match.group(1)
            
        return links

    def _extract_section(self, section_name: str, keywords: List[str]):
        """Helper to extract a section based on keywords."""
        lines = self.text.split('\n')
        in_section = False
        captured_lines = []
        
        for line in lines:
            clean_line = line.strip().lower()
            
            # Check if line is a section header
            is_header = any(keyword in clean_line for keyword in keywords) and len(clean_line) < 30
            
            if is_header:
                in_section = True
                continue
            
            # If we hit another likely header, stop (simplistic heuristic)
            possible_other_headers = ["education", "experience", "skills", "projects", "languages", "volunteering", "certifications"]
            if in_section and any(h in clean_line for h in possible_other_headers if h not in keywords) and len(clean_line) < 30:
                in_section = False
            
            if in_section and line.strip():
                captured_lines.append(line.strip())
        
        self.sections[section_name] = captured_lines
