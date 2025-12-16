import requests
import logging
import json
import time
from typing import Dict, List, Optional
from bs4 import BeautifulSoup as bs
from datetime import datetime
from base64 import b64decode
from ollama_wrapper import OllamaClient


class GitHubScraper:
    """
    GitHub profile scraper using hybrid API + web scraping approach.

    Primary: GitHub REST API v3 (no authentication required for public data)
    Fallback: Selenium scraping for contribution graphs and activity timeline
    """

    def __init__(self, username: str, driver: object = None, save: bool = False, api_token: Optional[str] = None, use_ollama: bool = True):
        """
        Initialize GitHub scraper.

        Args:
            username: GitHub username to scrape
            driver: Selenium WebDriver instance (optional, for scraping fallback)
            save: Whether to save output to file
            api_token: GitHub personal access token (optional, increases rate limits)
            use_ollama: Whether to use Ollama LLM to review repositories
        """
        self.username = username
        self.driver = driver
        self.save = save
        self.api_token = api_token
        self.use_ollama = use_ollama
        self.ollama_client = OllamaClient() if use_ollama else None
        self.base_api_url = "https://api.github.com"
        self.profile_url = f"https://github.com/{username}"

        # Setup API headers
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Profile-Scraper"
        }
        if api_token:
            self.headers["Authorization"] = f"token {api_token}"

        # Fetch data
        self.user_data = self.get_user_profile()
        self.repositories = self.get_repositories()
        self.organizations = self.get_organizations()
        self.starred_repos = self.get_starred_repositories()
        self.contribution_stats = self.get_contribution_stats()

        # Generate output
        self.output = self.get_json_output()

    def _make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a request to GitHub API with error handling and rate limit checking.

        Args:
            endpoint: API endpoint (e.g., '/users/username')
            params: Query parameters

        Returns:
            JSON response or None if request fails
        """
        url = f"{self.base_api_url}{endpoint}"

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)

            # Check rate limit
            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining:
                logging.debug(f"API rate limit remaining: {remaining}")
                if int(remaining) < 10:
                    logging.warning(f"Low API rate limit: {remaining} requests remaining")

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logging.error(f"Resource not found: {endpoint}")
                return None
            elif response.status_code == 403:
                logging.error("API rate limit exceeded or forbidden")
                return None
            else:
                logging.error(f"API request failed: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logging.exception(e)
            logging.error(f"Failed to fetch {endpoint}")
            return None

    def get_user_profile(self) -> Dict:
        """
        Fetch user profile information from GitHub API.

        Returns:
            Dictionary with user profile data
        """
        user_data = self._make_api_request(f"/users/{self.username}")

        if not user_data:
            logging.error(f"Failed to fetch profile for {self.username}")
            return {}

        # Extract and clean relevant fields
        profile = {
            "username": user_data.get("login"),
            "name": user_data.get("name"),
            "bio": user_data.get("bio"),
            "company": user_data.get("company"),
            "location": user_data.get("location"),
            "email": user_data.get("email"),
            "blog": user_data.get("blog"),
            "twitter": user_data.get("twitter_username"),
            "avatarUrl": user_data.get("avatar_url"),
            "profileUrl": user_data.get("html_url"),
            "hireable": user_data.get("hireable"),
            "publicRepos": user_data.get("public_repos"),
            "publicGists": user_data.get("public_gists"),
            "followers": user_data.get("followers"),
            "following": user_data.get("following"),
            "createdAt": user_data.get("created_at"),
            "updatedAt": user_data.get("updated_at"),
        }

        # Remove null values
        profile = {k: v for k, v in profile.items() if v is not None}

        logging.info(f"Successfully fetched profile for {self.username}")
        return profile

    def get_repositories(self, max_repos: int = 100) -> List[Dict]:
        """
        Fetch user's public repositories.

        Args:
            max_repos: Maximum number of repositories to fetch

        Returns:
            List of repository dictionaries
        """
        repos = []
        page = 1
        per_page = 100  # GitHub API max per page

        while len(repos) < max_repos:
            params = {
                "per_page": per_page,
                "page": page,
                "sort": "updated",
                "direction": "desc"
            }

            repo_data = self._make_api_request(f"/users/{self.username}/repos", params)

            if not repo_data or len(repo_data) == 0:
                break

            for repo in repo_data:
                if len(repos) >= max_repos:
                    break

                repo_info = {
                    "name": repo.get("name"),
                    "fullName": repo.get("full_name"),
                    "description": repo.get("description"),
                    "url": repo.get("html_url"),
                    "homepage": repo.get("homepage"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count"),
                    "forks": repo.get("forks_count"),
                    "watchers": repo.get("watchers_count"),
                    "openIssues": repo.get("open_issues_count"),
                    "topics": repo.get("topics", []),
                    "isPrivate": repo.get("private"),
                    "isFork": repo.get("fork"),
                    "isArchived": repo.get("archived"),
                    "createdAt": repo.get("created_at"),
                    "updatedAt": repo.get("updated_at"),
                    "pushedAt": repo.get("pushed_at"),
                    "size": repo.get("size"),
                    "defaultBranch": repo.get("default_branch"),
                    "license": repo.get("license", {}).get("name") if repo.get("license") else None,
                }

                # Remove null values
                repo_info = {k: v for k, v in repo_info.items() if v is not None and v != [] and v != {}}
                
                # Fetch README and Review with Ollama
                if self.use_ollama:
                    logging.info(f"Analyzing repository: {repo_info['name']}")
                    readme_content = self.get_readme_content(repo_info['name'])
                    if readme_content:
                        review = self.review_repository(repo_info['name'], readme_content)
                        repo_info['llm_review'] = review
                    else:
                        repo_info['llm_review'] = "No README found."

                repos.append(repo_info)

            page += 1

            # Prevent infinite loop
            if len(repo_data) < per_page:
                break

        logging.info(f"Fetched {len(repos)} repositories")
        return repos

    def get_readme_content(self, repo_name: str) -> Optional[str]:
        """
        Fetch README.md content for a repository.
        """
        try:
            url = f"/repos/{self.username}/{repo_name}/readme"
            data = self._make_api_request(url)
            if data and data.get("content"):
                return b64decode(data["content"]).decode('utf-8')
        except Exception as e:
            logging.error(f"Failed to fetch README for {repo_name}: {e}")
        return None

    def review_repository(self, repo_name: str, readme_content: str) -> str:
        """
        Use Ollama to review the repository based on its README.
        """
        try:
            # Truncate README if too long to save context window
            if len(readme_content) > 10000:
                readme_content = readme_content[:10000] + "...(truncated)"
            
            prompt = f"Analyze the following README for the GitHub repository '{repo_name}' and provide a concise review of what the project does, its key features, and the tech stack used."
            
            review = self.ollama_client.process_profile(
                {"readme": readme_content}, 
                custom_prompt=prompt
            )
            return review
        except Exception as e:
            logging.error(f"Failed to review repository {repo_name}: {e}")
            return "Analysis failed."

    def get_organizations(self) -> List[Dict]:
        """
        Fetch user's public organizations.

        Returns:
            List of organization dictionaries
        """
        orgs_data = self._make_api_request(f"/users/{self.username}/orgs")

        if not orgs_data:
            logging.debug("No organizations found")
            return []

        organizations = []
        for org in orgs_data:
            org_info = {
                "login": org.get("login"),
                "name": org.get("login"),  # Full name requires additional API call
                "url": org.get("html_url"),
                "avatarUrl": org.get("avatar_url"),
                "description": org.get("description"),
            }

            # Remove null values
            org_info = {k: v for k, v in org_info.items() if v is not None}
            organizations.append(org_info)

        logging.info(f"Fetched {len(organizations)} organizations")
        return organizations

    def get_starred_repositories(self, max_stars: int = 50) -> List[Dict]:
        """
        Fetch repositories starred by the user.

        Args:
            max_stars: Maximum number of starred repos to fetch

        Returns:
            List of starred repository dictionaries
        """
        starred = []
        page = 1
        per_page = 50

        while len(starred) < max_stars:
            params = {
                "per_page": per_page,
                "page": page
            }

            starred_data = self._make_api_request(f"/users/{self.username}/starred", params)

            if not starred_data or len(starred_data) == 0:
                break

            for repo in starred_data:
                if len(starred) >= max_stars:
                    break

                repo_info = {
                    "name": repo.get("name"),
                    "fullName": repo.get("full_name"),
                    "description": repo.get("description"),
                    "url": repo.get("html_url"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count"),
                }

                # Remove null values
                repo_info = {k: v for k, v in repo_info.items() if v is not None}
                starred.append(repo_info)

            page += 1

            if len(starred_data) < per_page:
                break

        logging.info(f"Fetched {len(starred)} starred repositories")
        return starred

    def get_contribution_stats(self) -> Dict:
        """
        Get contribution statistics via web scraping (GitHub doesn't provide this via API).
        Falls back to basic stats if scraping is unavailable.

        Returns:
            Dictionary with contribution statistics
        """
        if not self.driver:
            logging.debug("No driver provided, skipping contribution graph scraping")
            return {
                "scrapingAvailable": False,
                "message": "Selenium driver required for contribution statistics"
            }

        try:
            self.driver.get(self.profile_url)
            time.sleep(2)

            page_source = self.driver.page_source
            soup = bs(page_source, "lxml")

            # Try to find contribution count
            contributions = {}

            # Look for contribution summary (e.g., "1,234 contributions in the last year")
            contrib_text = soup.find("h2", class_="f4 text-normal mb-2")
            if contrib_text:
                text = contrib_text.get_text(strip=True)
                # Parse number from text
                import re
                match = re.search(r'([\d,]+)\s+contributions?', text)
                if match:
                    contrib_count = match.group(1).replace(',', '')
                    contributions["totalContributions"] = int(contrib_count)

            # Get longest streak
            streak_elem = soup.find("span", class_="f4 text-normal text-bold")
            if streak_elem:
                streak_text = streak_elem.get_text(strip=True)
                match = re.search(r'(\d+)', streak_text)
                if match:
                    contributions["longestStreak"] = int(match.group(1))

            # Get current streak
            current_streak = soup.find_all("span", class_="f4 text-normal text-bold")
            if len(current_streak) > 1:
                streak_text = current_streak[1].get_text(strip=True)
                match = re.search(r'(\d+)', streak_text)
                if match:
                    contributions["currentStreak"] = int(match.group(1))

            contributions["scrapingAvailable"] = True
            logging.info("Successfully scraped contribution statistics")
            return contributions

        except Exception as e:
            logging.exception(e)
            logging.error("Failed to scrape contribution statistics")
            return {
                "scrapingAvailable": False,
                "error": str(e)
            }

    def get_json_output(self) -> str:
        """
        Generate JSON output with all extracted data.

        Returns:
            JSON string with profile data
        """
        data = {
            "platform": "GitHub",
            "scrapedAt": datetime.utcnow().isoformat() + "Z",
            "profile": self.user_data,
            "repositories": self.repositories,
            "organizations": self.organizations,
            "starredRepositories": self.starred_repos,
            "contributionStats": self.contribution_stats,
        }

        # Remove empty/null sections
        data = {k: v for k, v in data.items() if v not in [None, [], {}]}

        output = json.dumps(data, indent=4, ensure_ascii=False)
        return output

    def save_output_in_file(self) -> None:
        """Save scraped data to a JSON file."""
        if self.save:
            filename = self.username
            try:
                import os

                if not os.path.exists("./data"):
                    os.makedirs("data")

                filepath = f"./data/{filename}_github.json"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(self.output)

                logging.info(f"File saved as {filepath}")
                print(f"✅ GitHub profile saved: {filepath}")

            except Exception as e:
                logging.exception(e)
                logging.error("Error saving the file")
        else:
            return None
