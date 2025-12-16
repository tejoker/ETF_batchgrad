#!/usr/bin/env python3
"""
Example usage of the LinkedIn & GitHub scraper.
Demonstrates how to use the GitHubScraper class directly in your code.
"""

import os
from GitHubScraper import GitHubScraper
import json

def example_basic_github_scrape():
    """Example: Basic GitHub profile scraping"""
    print("=" * 60)
    print("Example 1: Basic GitHub Profile Scraping")
    print("=" * 60)

    # Scrape a GitHub profile (no driver needed for API data)
    scraper = GitHubScraper(
        username="torvalds",
        driver=None,  # Not needed for API-only scraping
        save=False,   # Don't save to file in this example
        api_token=None  # Can provide token to increase rate limits
    )

    # Access the data
    profile_data = json.loads(scraper.output)

    print(f"\nProfile: {profile_data['profile']['name']}")
    print(f"Username: {profile_data['profile']['username']}")
    print(f"Location: {profile_data['profile'].get('location', 'N/A')}")
    print(f"Company: {profile_data['profile'].get('company', 'N/A')}")
    print(f"Public Repos: {profile_data['profile']['publicRepos']}")
    print(f"Followers: {profile_data['profile']['followers']}")

    print(f"\nTop 3 Repositories:")
    for i, repo in enumerate(profile_data['repositories'][:3], 1):
        print(f"  {i}. {repo['name']}")
        print(f"     Stars: {repo['stars']}, Language: {repo.get('language', 'N/A')}")
        print(f"     {repo['description'][:60]}...")

    print("\n")

def example_with_token():
    """Example: Using GitHub API with authentication token"""
    print("=" * 60)
    print("Example 2: GitHub Scraping with API Token")
    print("=" * 60)

    # Get token from environment variable
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        print("\nNo GITHUB_TOKEN found in environment.")
        print("Set it to increase rate limits from 60 to 5000 requests/hour:")
        print("  export GITHUB_TOKEN='your_token_here'")
        print("\nContinuing without token...\n")

    scraper = GitHubScraper(
        username="gvanrossum",
        driver=None,
        save=False,
        api_token=github_token
    )

    profile_data = json.loads(scraper.output)

    print(f"\nProfile: {profile_data['profile']['name']}")
    print(f"Bio: {profile_data['profile'].get('bio', 'N/A')}")
    print(f"Twitter: @{profile_data['profile'].get('twitter', 'N/A')}")

    if profile_data.get('organizations'):
        print(f"\nOrganizations:")
        for org in profile_data['organizations']:
            print(f"  - {org['login']}")

    print("\n")

def example_multiple_users():
    """Example: Scraping multiple GitHub users"""
    print("=" * 60)
    print("Example 3: Scraping Multiple GitHub Profiles")
    print("=" * 60)

    usernames = ["torvalds", "gvanrossum", "mojombo"]

    results = {}

    for username in usernames:
        print(f"\nScraping {username}...")
        scraper = GitHubScraper(
            username=username,
            driver=None,
            save=False,
            api_token=os.getenv("GITHUB_TOKEN")
        )

        data = json.loads(scraper.output)
        results[username] = {
            "name": data['profile'].get('name', 'N/A'),
            "repos": data['profile']['publicRepos'],
            "followers": data['profile']['followers'],
            "top_language": data['repositories'][0].get('language', 'N/A') if data['repositories'] else 'N/A'
        }

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"{'Username':<15} {'Name':<25} {'Repos':<10} {'Followers':<12} {'Top Lang':<10}")
    print("-" * 60)

    for username, info in results.items():
        print(f"{username:<15} {info['name']:<25} {info['repos']:<10} {info['followers']:<12} {info['top_language']:<10}")

    print("\n")

def example_save_to_file():
    """Example: Saving scraper output to file"""
    print("=" * 60)
    print("Example 4: Saving to File")
    print("=" * 60)

    scraper = GitHubScraper(
        username="torvalds",
        driver=None,
        save=True,  # This will save to data/torvalds_github.json
        api_token=os.getenv("GITHUB_TOKEN")
    )

    scraper.save_output_in_file()
    print(f"\nOutput saved to: data/torvalds_github.json")
    print("\n")

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "    LinkedIn & GitHub Profile Scraper Examples".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    # Run examples
    try:
        example_basic_github_scrape()
        example_with_token()
        example_multiple_users()
        example_save_to_file()

        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print("\nFor LinkedIn scraping examples, see the main README.md")
        print("For detailed GitHub scraper docs, see GITHUB_SCRAPER_README.md")
        print("\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Installed all requirements: pip install -r requirements.txt")
        print("  2. Internet connection for GitHub API")
        print("  3. (Optional) Set GITHUB_TOKEN for higher rate limits")
        print("\n")
