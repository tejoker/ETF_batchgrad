# LinkedIn & GitHub Profile Scraper

A powerful tool designed to extract profile information from both LinkedIn and GitHub. It provides an automated way to gather comprehensive data from professional profiles.

## Features

### LinkedIn Scraper
Automatically extracts information like name, location, experience, education, skills, certifications, projects, publications, languages, honors, and volunteering from LinkedIn profiles.

### GitHub Scraper (AI Enhanced)
Uses GitHub's REST API + **Ollama LLM** to extract:
- User profile (bio, location, company, social links)
- All public repositories (with stars, forks, language, topics)
- **AI Project Reviews**: Fetches `README.md` for each repo and generates a concise summary/review using local LLM.
- Organizations
- Starred repositories
- Contribution statistics (optional, with browser)

**Advantages of GitHub scraper:**
- Fast (API-based)
- **Insightful**: AI reviews help understand what code actually *does*.
- No authentication required for public data
- Returns structured JSON output containing both metadata and qualitative analysis.

### LinkedIn Visual Scraper (New)
A robust scraping pipeline that uses:
1. **Selenium + CDP**: For reliable rendering and screenshotting.
2. **Rolling OCR**: Captures profile content while scrolling to handle dynamic loading.
3. **Ollama Summarization**: Converts raw OCR text into a structured professional summary.

## Dependencies
- **Python3**: Ensure that you have Python 3 installed on your system. You can download and install Python 3 from the official Python website: https://www.python.org.
- **pip**: pip is the package installer for Python. It is usually installed by default when you install Python. However, make sure you have pip installed and it is up to date. You can check the version of pip by running the following command:
  ```
  pip --version
  ```
- **Selenium**: You can install it using pip by running the following command
  ```
  pip install selenium
  ```
  OR 
  ```
  pip install -r requirements.txt
  ```
  After cloning the repository, to install all the requirements at once.
- **Chromium Drivers**: Make sure you have the appropriate Chromium drivers installed and configured. These drivers are required for Selenium to interact with the Chromium browser. Refer to the Selenium documentation for instructions on installing and setting up Chromium drivers based on your operating system.


## Installation

To install and use the scraper, follow the steps given below:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/{YOUR-USERNAME}/ETF_batchgrad
    cd ETF_batchgrad
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **(Optional) Install Chrome Drivers**:
    Ensure you have the appropriate Chromium drivers installed for Selenium interactions.

## How to use?

### Quick Start: GitHub Scraper

The easiest way to get started is with the GitHub scraper (no authentication required):

```bash
# Scrape a GitHub profile and save to JSON
python3 scraper.py --platform github --url torvalds --save True

# Output to console
python3 scraper.py --platform github --url gvanrossum --save False
```

See [GITHUB_SCRAPER_README.md](docs/GITHUB_SCRAPER_README.md) for detailed GitHub scraper documentation.

### LinkedIn Scraper Usage

To use LinkedIn Scraper, follow the steps given below:

**(Recommended)**

- Login to the LinkedIn account from the account you want to do scraping using Google Chrome and keep it signed in.
- **For ubuntu**, open the terminal and use the given command to start Google chrome in remote debugging mode
    ```
    google-chrome --remote-debugging-port=PORT_NUMBER --user-data-dir="~/.config/google-chrome
    ```
    Replace the ``PORT_NUMBER`` with a port number, you would like your chrome browser to run on.

- Now, you can run the scraper.py using the following command:
    ```
    python3 scraper.py --running True --portnumber PORT_NUMBER
    ```
    Replace ``PORT_NUMBER`` by the port number on which the google chrome is running

    This will use the signed in account to extract the data from the LinkedIn profiles

**Note:** This method has lower risks of failure.

**(Other)**
- Copy the ```example.config.ini``` file and name it as ``config.ini``.
- Open ``config.ini`` file in a text editor, and add you preferable LinkedIn account's login credentials.
- Run the scraper.py using the following command:
    ```
    python3 scraper.py
    ```

### Other Features
Some other helpful and cool features:
- **Path**: Path of the `.txt` file where the links of the url are saved in the format given in `example.url.txt` file
  ```
  python3 scraper.py --path "path/to/file.txt"
  ```
- **URL**: URL of the profile can be added easily in the command, that means no need to change any code :)
  ```
  python3 scraper.py --url URL_GOES_HERE
  ```
- **Save**: You get to decide that you want to save the output in a file or just output it in the terminal.
  ```
  python3 scrapper.py --save True
  ```
  Default is False, that means the output will be printed in the terminal.
  
  **NOTE:** It will create a new directory named **data** in the working directory, if --save True is chosen.
- **Debug**: Good news for programmers, it has a ``--debug`` option that you can turn on to get **DEBUG** level logging in log file named **app.log**. Default it gives **WARNING** level logging.
  ```
  python3 scraper.py --debug True
  ```
  **NOTE:** Logging for selenium webdriver is set to **CRITICAL**, if you are having problems with selenium, it can be easily turned to **WARNING** or **DEBUG** level.
## Contributions

Contributions are welcome! If you encounter any issues or have suggestions for improvements, please feel free to open an issue or submit a pull request on the GitHub repository.

## Author

- [Nicolas Bigeard](https://github.com/nicolasbigeard)

## Resume HR Verifier

A new tool is available to verify candidate resumes against their GitHub data.
See [VERIFIER_README.md](VERIFIER_README.md) for details.

**Quick Usage:**
```bash
python3 resume_verifier.py --resume candidate.pdf --github username

## University Ranking Aggregation

A new module designed to aggregate and analyze university rankings from multiple sources (QS, THE, ARWU, CWUR).

**Features:**
- **Aggregation**: Combines rankings from different years and sources into a unified average ranking.
- **Region Analysis**: Automatically determines if a university is located in Europe or outside, enabling regional comparisons.
- **Data Enrichment**: Maps university names across different datasets to provide enriched metadata.

**Key Files:**
- `aggregate_rankings.py`: Core logic for combining different ranking CSVs.
- `add_region_column.py`: Script to add "Region" (Europe/Outside Europe) based on university location.
- `average_ranking_with_region.csv`: The final output dataset with averaged rankings and regional data.

**Usage:**
```bash
# 1. Aggregate rankings (produces average_ranking.csv)
python3 aggregate_rankings.py

# 2. Add region information (produces average_ranking_with_region.csv)
python3 add_region_column.py
```
