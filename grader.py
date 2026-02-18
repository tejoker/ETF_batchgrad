
import pandas as pd
from fuzzywuzzy import fuzz
from ollama_wrapper import OllamaClient
from GitHubScraper import GitHubScraper
from verifier.parser import ResumeParser
from verifier.cross_verifier import CrossVerifier
from website_scraper import WebsiteScraper
from LinkedInScraper import LinkedinScraper
from scraper import get_selenium_drivers
import statistics
import re
import math
import json
import os

class Grader:
    def __init__(self, use_scraping=True):
        self.daur_df = pd.read_csv('daur_rankings_2024.csv')
        self.world_df = pd.read_csv('average_ranking_with_region.csv')
        self.ollama = OllamaClient(model="llama3.2:3b")
        self.use_scraping = use_scraping
        self.ollama = OllamaClient(model="llama3.2:3b")
        self.use_scraping = use_scraping
        self.scraped_data_cache = {}
        self.driver = None
        if self.use_scraping:
             try:
                 # Try to connect to existing debug chrome or start headless
                 # Using port 9222 as default
                 self.driver = get_selenium_drivers(running=True, portnumber=9222)
             except:
                 print("   [Grader] Could not connect to running Chrome, trying to start new instance...")
                 try:
                    self.driver = get_selenium_drivers(running=False, headless=True)
                 except Exception as e:
                     print(f"   [Grader] Failed to initialize Selenium: {e}")


    def _fuzzy_match_school(self, school_name, df, name_col):
        """Find best match for school name in dataframe."""
        if not isinstance(school_name, str):
            school_name = str(school_name)
            if school_name == "nan":
                 return None, 0
            
        best_match = None
        best_score = 0
        
        # Simple exact match check first
        if school_name in df[name_col].values:
            return school_name, 100
            
        # Optimization: Only check first letter match to speed up?
        # Or just run full scan, dataset is small enough (<200 lines for DAUR, <1000 for World)
        
        for name in df[name_col].dropna():
            score = fuzz.token_sort_ratio(school_name.lower(), name.lower())
            if score > best_score:
                best_score = score
                best_match = name
        
        return best_match, best_score

    def grade_education(self, row):
        """
        Grade education based on France DAUR or World Rankings.
        DAUR: AAA=95, AA=85, A=75. Poly/ENS Ulm=100.
        World: Top 10=100. Decay using DAUR anchors.
        """
        school_name = row.get('education.degreeFields1') or row.get('education.pleaseSpecify') # Adjust based on actual CSV columns for school name
        
        if pd.isna(school_name) or school_name == "":
             school_name = row.get('education.degreeFields', "")

        country = row.get('countryOfOrigin', "")
        
        # Heuristic: Check if France
        is_france = False
        if isinstance(country, str) and "france" in country.lower():
            is_france = True
        
        grade = 0
        matched_name = ""
        
        if is_france:
            matched_name, score = self._fuzzy_match_school(school_name, self.daur_df, 'Name')
            if score > 80:
                # Get notation
                try:
                    notation = self.daur_df[self.daur_df['Name'] == matched_name]['Notation'].iloc[0]
                except:
                    notation = "B" # Default fallback
                
                # Special cases - Case insensitive check
                m_lower = matched_name.lower()
                if "polytechnique" in m_lower and "milano" not in m_lower: # Avoid Polimi
                     return 100
                if "ens ulm" in m_lower or ("normale supérieure" in m_lower and "paris" in m_lower): 
                    return 100

                if notation == 'AAA':
                    grade = 95
                elif notation == 'AA':
                    grade = 85
                elif notation == 'A':
                    grade = 75
                elif notation == 'BBB':
                    grade = 65
                elif notation == 'BB':
                    grade = 55
                elif notation == 'B':
                    grade = 45
                elif notation == 'CCC':
                    grade = 35
                elif notation == 'CC':
                    grade = 25
                elif notation == 'C':
                    grade = 15
                else:
                    grade = 10
                    
                return grade
        
        # If not France or no match in DAUR, check World
        matched_name, score = self._fuzzy_match_school(school_name, self.world_df, 'University Name')
        
        if score > 80:
            rank = self.world_df[self.world_df['University Name'] == matched_name]['Mean Rank'].iloc[0]
            
            # Top 10 -> 100
            if rank <= 10:
                return 100
                
            # Mapping:
            # Rank 50 ~ 95 (AAA)
            # Rank 150 ~ 85 (AA)
            # Rank 300 ~ 75 (A)
            
            if rank <= 50:
                grade = 100 + (rank - 10) * -0.125
            elif rank <= 150:
                grade = 95 + (rank - 50) * -0.1
            elif rank <= 300:
                grade = 85 + (rank - 150) * (-10/150)
            else:
                grade = 75 + (rank - 300) * (-0.08)
            
            return max(0, min(100, grade))
            
        return 50 # Default if no match found

    def _scrape_github(self, github_url):
        if not self.use_scraping or not isinstance(github_url, str) or "github.com" not in github_url:
            return {}
        
        # Extract username
        try:
            username = github_url.rstrip('/').split('/')[-1]
        except:
            return {}
            
        if f"gh_{username}" in self.scraped_data_cache:
            return self.scraped_data_cache[f"gh_{username}"]
            
        print(f"   [Scraper] Fetching GitHub data for {username}...")
        try:
            # Initialize scraper without driver for speed (API only)
            # Ensure Ollama is used for repo analysis
            scraper = GitHubScraper(username=username, driver=None, save=False, use_ollama=False)
            
            # Get structured data
            profile = scraper.get_user_profile()
            repos = scraper.get_repositories(max_repos=3) # Limit to top 3 for speed
            
            data = {
                "profile": profile,
                "repos": repos,
                "bio": profile.get('bio', ''),
                "blog": profile.get('blog', '')
            }
            self.scraped_data_cache[f"gh_{username}"] = data
            return data
        except Exception as e:
            print(f"   [Scraper] GitHub Error: {e}")
            return {}

    def _scrape_linkedin(self, linkedin_url):
        if not self.use_scraping or not self.driver or not isinstance(linkedin_url, str) or "linkedin.com" not in linkedin_url:
            return {}
            
        if linkedin_url in self.scraped_data_cache:
            return self.scraped_data_cache[linkedin_url]
            
        print(f"   [Scraper] Fetching LinkedIn data for {linkedin_url}...")
        try:
            driver = self.driver
            driver.get(linkedin_url)
            # Basic wait for load
            import time
            time.sleep(3)
            
            page_source = driver.page_source
            scraper = LinkedinScraper(page_source, driver, save=False)
            
            # Construct simple data dictionary from scraper attributes
            data = {
                "education": scraper.education,
                "experience": scraper.experience,
                "projects": scraper.projects,
                "skills": scraper.skills
            }
            
            self.scraped_data_cache[linkedin_url] = data
            return data
        except Exception as e:
            print(f"   [Scraper] LinkedIn Error: {e}")
            return {}

    def _parse_resume(self, resume_path):
        """Parse resume PDF if path exists."""
        if not resume_path or not isinstance(resume_path, str):
            return ""
        
        # Handle potential web URLs by skipping or separate logic (currently only local)
        if resume_path.startswith("http"):
             # TODO: Download logic could be added here
             return ""
             
        if not os.path.exists(resume_path):
            return ""

        print(f"   [Resume] Parsing {resume_path}...")
        try:
            parser = ResumeParser(resume_path)
            data = parser.parse()
            
            # Construct summary
            summary = ""
            if data.get('skills'):
                summary += f"Skills: {', '.join(data['skills'][:20])}\n" # Limit
            
            if data.get('experience'):
                summary += "Experience:\n"
                for exp in data['experience'][:5]: # Limit
                    summary += f"- {exp}\n"
            
            # Use raw text (truncated) if structured fails or as supplement?
            # Structured is likely safer for context window
            # Return both summary and raw structure/text for verification
            return {
                "summary": summary,
                "raw_text": data.get("raw_text", ""),
                "education": data.get("education", []),
                "skills": data.get("skills", [])
            }
        except Exception as e:
            print(f"   [Resume] Error: {e}")
            return {}

    def _get_ollama_grade(self, criteria, prompt_context):
        """Run Ollama 5 times, take average of best 3."""
        scores = []
        
        system_prompt = """
        You are an expert venture capital evaluator. 
        You evaluate applicants based on specific criteria for a deeptech/elite program.
        Output ONLY a single integer score from 0 to 100.
        0 is terrible, 100 is world-class/exceptional.
        Do not explain. Just the number.
        """
        
        full_prompt = f"""
        Evaluate the following applicant for the criteria: {criteria}.
        
        Context:
        {prompt_context}
        
        Specific Instructions:
        {self._get_criteria_instructions(criteria)}
        
        Grade (0-100):
        """
        
        regex = r'\b([0-9]{1,3})\b'
        
        for _ in range(5):
            response = self.ollama.generate_completion(full_prompt, system_prompt=system_prompt)
            if response:
                matches = re.findall(regex, response)
                if matches:
                    try:
                        val = int(matches[-1])
                        if 0 <= val <= 100:
                            scores.append(val)
                    except:
                        pass
        
        if not scores:
            return 0
            
        scores.sort(reverse=True)
        # Avg of best 3
        best_3 = scores[:3]
        if len(best_3) > 0:
            return sum(best_3) / len(best_3)
        return 0

    def _get_criteria_instructions(self, criteria):
        if criteria == 'Community':
            return """
            Look for roles in associations, involvement in EuroTech, connections to fellows.
            Keywords: 'association', 'president', 'founder', 'fellow', 'community', 'family'.
            High grade for leadership roles and strong community spirit.
            """
        elif criteria == 'Hack/Personal Project':
            return """
            Look for won hackathons, GitHub repos, personal projects.
            Verify if they are technical/deeptech enough.
            Evidence like 'won', '1st place', 'github.com', 'built'.
            Look for technical details in the GitHub analysis if available.
            High grade for winning major hacks or complex technical projects.
            """
        elif criteria == 'Research':
            return """
            Look for publications, Arxiv, deeptech research ambition.
            Links to papers are a plus.
            Must be DEEPTECH research, not just fine-tuning LLMs.
            High grade for published papers or serious research involvement.
            """
        elif criteria == 'Startup':
            return """
            Looking for website, money raised, VC backing.
            Standard Rule: High grade for raised funds + deeptech focus + live product.
            OVERRIDE RULE: If the applicant mentions raising 1 million or more (e.g. "raised 2.1 million", "1M", "1000k", "$1M", "€1M"), the grade MUST be 100. IGNORE all other criteria like tech vs non-tech. raising > 1M = 100.
            
            """
        return ""

    def grade_applicant(self, row):
        grades = {}
        
        # Education
        grades['Education'] = self.grade_education(row)
        
        # Scrape Data if available
        github_url = row.get('githubUrl')
        scraped_gh_data = self._scrape_github(github_url)
        
        gh_context = ""
        if scraped_gh_data:
            gh_context += f"GitHub Bio: {scraped_gh_data.get('bio')}\n"
            gh_context += f"Top Repositories:\n"
            for repo in scraped_gh_data.get('repos', [])[:5]:
                gh_context += f"- {repo['name']}: {repo.get('description', '')} (Stars: {repo.get('stars')})\n  Analysis: {repo.get('llm_review', 'N/A')}\n"

        # Scrape personal website
        website_url = (
            (scraped_gh_data.get('blog', '') if scraped_gh_data else '')
            or row.get('personalWebsite', '')
        )
        website_data = {}
        if website_url and isinstance(website_url, str) and website_url.startswith("http"):
            print(f"   [Website] Scraping {website_url}...")
            website_data = WebsiteScraper().scrape(website_url)
            if website_data.get("error"):
                print(f"   [Website] {website_data['error']}")

        # Parse Resume
        resume_path = row.get('uploadResume')
        resume_data = self._parse_resume(resume_path)  # Returns dict now
        resume_summary = resume_data.get("summary", "") if isinstance(resume_data, dict) else ""

        # If website URL not found from GitHub bio, try resume links
        if not website_url and isinstance(resume_data, dict):
            resume_website = resume_data.get("links", {}).get("website", "")
            if resume_website and resume_website.startswith("http"):
                print(f"   [Website] Scraping {resume_website} (from resume)...")
                website_data = WebsiteScraper().scrape(resume_website)
                if website_data.get("error"):
                    print(f"   [Website] {website_data['error']}")

        # Scrape LinkedIn
        linkedin_url = row.get('linkedinUrl')
        scraped_li_data = self._scrape_linkedin(linkedin_url)
        
        # Cross Verification
        form_data_for_verifier = {
            "education_school": row.get('education.degreeFields1') or row.get('education.pleaseSpecify'),
            "current_role": row.get('editGrid.whatIsYourRoleInTheCompany'),
            "startup_name": row.get('editGrid.whatIsTheNameOfTheCompany'),
            "projects": row.get('listTheThingsYouveBuiltAppsToolsWebsitesOpenSourceProjectsAddUrLsIfPossibleIfSeveralSeparateWithSemicolons', '')
        }
        
        verifier = CrossVerifier(form_data_for_verifier, scraped_li_data, resume_data if isinstance(resume_data, dict) else {})
        verification_report = verifier.verify()
        grades['Verification'] = verification_report
        
        # Community
        comm_context = f"""
        Role/Association: {row.get('whichEntrepreneurshipProgramsAcceleratorsClubsHaveYouBeenPartOf', '')}
        Experience: {row.get('tellYouALittleBitMoreAboutYouThen200Words', '')}
        Contributions: {row.get('whyWouldYouLikeToJoinEuroTechFederationAsAFellowWhatCouldYouContributeToTheCommunity', '')}
        GitHub Bio: {scraped_gh_data.get('bio', '') if scraped_gh_data else ''}
        Resume: {resume_summary}
        """
        grades['Community'] = self._get_ollama_grade('Community', comm_context)
        
        # Hack/Project
        hack_context = f"""
        Achievements: {row.get('whatIsTheMostImpressiveThingYouveAchievedMax150Words', '')}
        Projects: {row.get('listTheThingsYouveBuiltAppsToolsWebsitesOpenSourceProjectsAddUrLsIfPossibleIfSeveralSeparateWithSemicolons', '')}
        Github URL: {row.get('githubUrl', '')}
        
        SCRAPED GITHUB DATA:
        {gh_context}
        
        RESUME:
        {resume_summary}
        """
        grades['Hack/Project'] = self._get_ollama_grade('Hack/Personal Project', hack_context)
        
        # Research
        res_context = f"""
        Projects/Papers: {row.get('listTheThingsYouveBuiltAppsToolsWebsitesOpenSourceProjectsAddUrLsIfPossibleIfSeveralSeparateWithSemicolons', '')}
        About: {row.get('tellYouALittleBitMoreAboutYouThen200Words', '')}
        SCRAPED GITHUB DATA (May contain research code):
        {gh_context}
        RESUME:
        {resume_summary}
        """
        grades['Research'] = self._get_ollama_grade('Research', res_context)
        
        # Startup
        
        # Helper signal for funding
        extra_info = str(row.get('tellYouALittleBitMoreAboutYouThen200Words', ''))
        funding_signal = ""
        if "raised" in extra_info.lower() and ("million" in extra_info.lower() or "1m" in extra_info.lower() or "2.1" in extra_info.lower()):
             funding_signal = "IMPORTANT: APPLICANT HAS STATED THEY RAISED > 1 MILLION."

        start_context = f"""
        Startup Name: {row.get('editGrid.whatIsTheNameOfTheCompany', '')}
        Role: {row.get('editGrid.whatIsYourRoleInTheCompany', '')}
        Desc: {row.get('editGrid.describeYourStartupIn23Sentences', '')}
        Extra Info: {extra_info}
        Website URL: {scraped_gh_data.get('blog', '') if scraped_gh_data else ''}
        Website Content: {website_data.get('raw_text', '')[:400] if website_data else ''}
        {funding_signal}
        TRUST SCORE: {verification_report['trust_score']}
        DISCREPANCIES: {verification_report['discrepancies']}
        """
        grades['Startup'] = self._get_ollama_grade('Startup', start_context)
        
        return grades

    def __del__(self):
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    # Test on one row
    grader = Grader()
    df = pd.read_csv('input.csv')
    if not df.empty:
        sample = df.iloc[0]
        print("Grading sample:", sample['firstName'], sample['lastName'])
        results = grader.grade_applicant(sample)
        print("Results:", results)
