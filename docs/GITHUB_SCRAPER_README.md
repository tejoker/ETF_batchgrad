# GitHub Scraper Documentation

The scraper now supports both LinkedIn and GitHub profiles using a hybrid API + scraping approach.

## Features

### GitHub Scraper Capabilities

The GitHub scraper uses the GitHub REST API v3 as its primary data source, with optional web scraping for contribution graphs.

**Data Collected:**
- User profile (name, bio, location, company, email, website, Twitter)
- All public repositories (with metadata: stars, forks, language, topics, license)
- Organizations
- Starred repositories
- Contribution statistics (requires Selenium driver)

**Advantages:**
- No authentication required for public data
- Fast and reliable (API is more stable than scraping)
- Higher rate limits with GitHub token (5000 req/hour vs 60 req/hour)
- Works without browser/Selenium for most data

## Usage

### Basic Usage (API Only - No Browser Required)

```bash
# Scrape a GitHub profile and save to JSON
python3 scraper.py --platform github --url torvalds --save True

# Output to console instead of file
python3 scraper.py --platform github --url gvanrossum --save False

# You can use username or full URL
python3 scraper.py --platform github --url https://github.com/torvalds --save True
```

### With GitHub Token (Recommended)

Increase API rate limits from 60 to 5000 requests per hour:

```bash
# Set token in environment
export GITHUB_TOKEN="your_github_personal_access_token"

# Or add to .env file
echo "GITHUB_TOKEN=your_token" >> .env

# Then run normally
python3 scraper.py --platform github --url torvalds --save True
```

To create a GitHub token:
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate new token (classic)
3. No scopes needed for public data (leave all unchecked)
4. Copy and save the token

### With Contribution Graph Scraping

To scrape the contribution heatmap/statistics:

```bash
# Start Chrome in debug mode (Windows PowerShell)
start_chrome_debug.ps1

# Navigate to github.com in that browser
# Then run with --running True
python3 scraper.py --platform github --url torvalds --save True --running True --port 9222 --host 172.24.128.1
```

### Batch Processing

Create a file with GitHub usernames (one per line):

```bash
# github_users.txt
torvalds
gvanrossum
mojombo
defunkt
```

```bash
python3 scraper.py --platform github --path github_users.txt --save True
```

## Output Format

The scraper generates JSON files in the `data/` directory with the following structure:

```json
{
    "platform": "GitHub",
    "scrapedAt": "2025-10-24T07:26:50.053765Z",
    "profile": {
        "username": "torvalds",
        "name": "Linus Torvalds",
        "company": "Linux Foundation",
        "location": "Portland, OR",
        "followers": 253225,
        "following": 0,
        "publicRepos": 9,
        "publicGists": 1,
        "createdAt": "2011-09-03T15:26:22Z"
    },
    "repositories": [
        {
            "name": "linux",
            "description": "Linux kernel source tree",
            "language": "C",
            "stars": 205568,
            "forks": 57988,
            "topics": [],
            "license": "Other"
        }
    ],
    "organizations": [
        {
            "login": "DROPCitizenShip",
            "url": "https://github.com/DROPCitizenShip"
        }
    ],
    "starredRepositories": [
        {
            "name": "linux",
            "fullName": "torvalds/linux",
            "stars": 205568
        }
    ],
    "contributionStats": {
        "scrapingAvailable": false,
        "message": "Selenium driver required for contribution statistics"
    }
}
```

## Command Line Options

```
--platform          Platform to scrape (linkedin or github) [default: linkedin]
--url              Username or full URL to scrape
--path             Path to file with multiple usernames/URLs
--save             Save output to JSON file [default: False]
--running          Use remote debugging mode [default: False]
--port             Chrome debug port [default: 9222]
--host             Chrome debug host [default: localhost]
--debug            Enable debug logging [default: False]
```

## Architecture

### Hybrid API + Scraping Approach

```
GitHubScraper:
├── Primary: GitHub REST API v3 (requests library)
│   ├── User profile
│   ├── Repositories
│   ├── Organizations
│   └── Starred repos
│
└── Fallback: Selenium web scraping
    └── Contribution graph/statistics
```

### Benefits of This Approach

1. **Reliability**: GitHub API is more stable than scraping
2. **Speed**: API requests are much faster than browser automation
3. **No Auth Required**: Public data accessible without login
4. **Rate Limits**: 60 req/hour without token, 5000/hour with token
5. **Fallback Option**: Can still scrape data not available via API

## API Rate Limits

- **Without token**: 60 requests/hour
- **With token**: 5000 requests/hour
- Rate limit info is logged in debug mode

To check your current rate limit:
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
```

## Examples

### Simple Scrape
```bash
python3 scraper.py --platform github --url torvalds --save True
```

### Multiple Users
```bash
# Create users.txt
echo "torvalds
gvanrossum
mojombo" > github_users.txt

python3 scraper.py --platform github --path github_users.txt --save True
```

### With Custom Settings
```bash
export GITHUB_TOKEN="ghp_yourtoken"
python3 scraper.py --platform github --url torvalds --save True --debug True
```

## Comparison: LinkedIn vs GitHub Scraping

| Feature | LinkedIn | GitHub |
|---------|----------|--------|
| **Primary Method** | Web scraping (Selenium) | REST API |
| **Auth Required** | Yes (login) | No (for public data) |
| **Speed** | Slow (browser automation) | Fast (API calls) |
| **Reliability** | Medium (DOM changes) | High (stable API) |
| **Browser Needed** | Always | Optional (only for contributions) |
| **Rate Limits** | None (but may get blocked) | 60/hr (5000/hr with token) |

## Troubleshooting

### "API rate limit exceeded"
- Solution: Set GITHUB_TOKEN environment variable
- Or wait 1 hour for rate limit reset

### "Resource not found"
- The username doesn't exist or profile is private
- Check the username spelling

### Dependencies warning
- Warning about urllib3 version mismatch is harmless
- Can be ignored or fixed by updating: `pip install -U urllib3`

## Future Enhancements

Potential additions:
- GraphQL API for contribution graphs (avoids scraping)
- Repository language statistics
- Commit frequency analysis
- Pull request/issue statistics
- Follower/following details
- Gist content scraping
