import re
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class WebsiteScraper:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def scrape(self, url: str) -> Dict:
        """
        Scrape a personal/company website and extract name and company/project mentions.
        Returns:
            {
                "name": str|None,
                "companies": [str],
                "raw_text": str,
                "error": str|None
            }
        """
        if not url or not url.startswith("http"):
            return {"name": None, "companies": [], "raw_text": "", "error": "invalid URL"}

        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Strip scripts/styles for clean text
            for tag in soup(["script", "style", "noscript", "nav", "footer"]):
                tag.decompose()

            raw_text = soup.get_text(separator=" ", strip=True)
            raw_text = re.sub(r'\s+', ' ', raw_text).strip()

            name = self._extract_name(soup)
            companies = self._extract_companies(raw_text)

            return {
                "name": name,
                "companies": companies,
                "raw_text": raw_text[:3000],
                "error": None
            }

        except requests.exceptions.Timeout:
            return {"name": None, "companies": [], "raw_text": "", "error": "timeout"}
        except requests.exceptions.ConnectionError:
            return {"name": None, "companies": [], "raw_text": "", "error": "connection error"}
        except requests.exceptions.HTTPError as e:
            return {"name": None, "companies": [], "raw_text": "", "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"name": None, "companies": [], "raw_text": "", "error": str(e)}

    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Try to extract the person/site owner name from common HTML signals."""
        # 1. Open Graph author/title meta
        for attr in ["og:title", "author", "twitter:title"]:
            tag = soup.find("meta", property=attr) or soup.find("meta", attrs={"name": attr})
            if tag and tag.get("content"):
                candidate = tag["content"].strip()
                if candidate and len(candidate) < 60:
                    return candidate

        # 2. <h1> tag — most personal sites use this for their name
        h1 = soup.find("h1")
        if h1:
            candidate = h1.get_text(strip=True)
            if candidate and len(candidate) < 60:
                return candidate

        # 3. <title> tag (strip common suffixes)
        title = soup.find("title")
        if title:
            candidate = title.get_text(strip=True)
            # Remove common trailing patterns like " | Portfolio", " - Home"
            candidate = re.sub(r'[\|\-–—].*$', '', candidate).strip()
            if candidate and len(candidate) < 60:
                return candidate

        return None

    def _extract_companies(self, text: str) -> List[str]:
        """Extract capitalized multi-word phrases that could be company/project names."""
        # Pattern: 2-4 consecutive capitalized words
        pattern = re.compile(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})\b')
        candidates = pattern.findall(text)

        # Deduplicate while preserving order, filter common false positives
        seen = set()
        stop = {
            "The", "This", "These", "Those", "What", "Where", "When", "How",
            "About", "Contact", "Home", "Blog", "Work", "My", "Our", "We",
            "You", "He", "She", "They", "It", "Its", "And", "For", "With",
            "From", "Into", "Over", "Under", "Through", "Between", "During"
        }
        results = []
        for c in candidates:
            words = c.split()
            if all(w in stop for w in words):
                continue
            if c not in seen:
                seen.add(c)
                results.append(c)

        return results[:20]
