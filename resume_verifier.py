import argparse
import json
import os
import sys
from verifier.parser import ResumeParser
from verifier.engine import VerificationEngine
from GitHubScraper import GitHubScraper

def main():
    parser = argparse.ArgumentParser(description="Resume HR Verifier - Cross-reference Resume with GitHub")
    parser.add_argument("--resume", required=True, help="Path to the Resume PDF file")
    parser.add_argument("--github", required=False, help="GitHub username (optional if link is in resume)")
    parser.add_argument("--output", default="verification_report.json", help="Output file for the report")
    
    args = parser.parse_args()

    # 1. Parse Resume PDF (Moved first to get links)
    print(f"📄 Parsing Resume: {args.resume}...")
    if not os.path.exists(args.resume):
        print(f"❌ Resume file not found: {args.resume}")
        return
        
    try:
        pdf_parser = ResumeParser(args.resume)
        resume_data = pdf_parser.parse()
        print("✅ Resume parsed successfully.")
    except Exception as e:
        print(f"❌ Error parsing resume: {e}")
        return

    # 2. Determine GitHub Username
    github_username = args.github
    if not github_username:
        print("🔍 specific username not provided, checking resume links...")
        extracted_gh = resume_data.get("links", {}).get("github")
        if extracted_gh:
            github_username = extracted_gh
            print(f"✅ Found GitHub profile in resume: {github_username}")
        else:
            print("❌ No GitHub username provided and no link found in resume.")
            print("   Please add a link to your resume or use --github argument.")
            return

    # 3. Report LinkedIn (Informational)
    linkedin_id = resume_data.get("links", {}).get("linkedin")
    if linkedin_id:
        print(f"ℹ️  Found LinkedIn profile: {linkedin_id} (Note: Verification requires manual login)")

    # 4. Scrape GitHub Data
    print(f"🔍 Fetching GitHub data for user: {github_username}...")
    try:
        scraper = GitHubScraper(username=github_username, save=False)
        # We access the internal methods to get the raw data structure 
        # normally scraper.get_json_output() returns a string, but we want the dict
        # So we'll trigger the scraping and reconstruct the dict similarly to the scraper
        profile = scraper.get_user_profile()
        if not profile:
             print(f"❌ User '{github_username}' not found on GitHub.")
             return

        repos = scraper.get_repositories()
        
        github_data = {
            "profile": profile,
            "repositories": repos
        }
        print("✅ GitHub data fetched successfully.")
    except Exception as e:
        print(f"❌ Error fetching GitHub data: {e}")
        return

    # 3. Verify
    print("⚖️  Running verification...")
    engine = VerificationEngine(resume_data, github_data)
    report = engine.verify()

    # 4. Output Results
    print("\n" + "="*60)
    print(f"RESUME VERIFICATION REPORT: {args.github}")
    print("="*60)
    print(f"TRUST SCORE: {report['score']}/100")
    print(f"SUMMARY: {report['summary']}")
    print("-" * 60)
    
    for check in report["checks"]:
        status_icon = "✅" if check["status"] == "PASS" else "⚠️ " if check["status"] == "WARN" else "❌"
        print(f"{status_icon} [{check['category']}] {check['item']}")
        print(f"   Resume: {check['resume_value']}")
        print(f"   GitHub: {check['github_value']}")
        print(f"   Score:  {check['match_score']}%")
        if "details" in check:
            print(f"   Details: {check['details']}")
        print("")
    
    # Save Report
    with open(args.output, "w") as f:
        json.dump(report, f, indent=4)
    print(f"💾 Detailed report saved to {args.output}")

if __name__ == "__main__":
    main()
