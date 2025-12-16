# Imports
from bs4 import BeautifulSoup as bs

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import time
from configparser import ConfigParser
import argparse
import os
from dotenv import load_dotenv

import logging
from typing import List, Any

from LinkedInScraper import LinkedinScraper
from GitHubScraper import GitHubScraper

# Load environment variables from .env file
load_dotenv()


# Functions and Classes


def quit_driver(driver):
    logging.critical("Quitting...")
    driver.quit()


def get_selenium_drivers(running: bool, **kwargs) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    
    # Add headless mode if requested
    if kwargs.get("headless", False):
        options.add_argument("--headless")

    if running:
        portnumber = kwargs.get("portnumber", 9222)
        host = kwargs.get("host", "localhost")
        options.add_experimental_option("debuggerAddress", f"{host}:{portnumber}")
    else:
        options.add_experimental_option("detach", True)

    options.add_argument("--disable-logging")
    
    try:
        # If running in debug mode, don't specify chromedriver service
        if running:
            driver = webdriver.Chrome(options=options)
        else:
            # Use webdriver-manager to automatically download and manage chromedriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logging.exception(e)
        logging.critical("driver failed to start...")
        logging.critical("Make sure Chrome/Chromium is installed and chromedriver is in the correct location")
        exit(1)

    logging.debug("waiting for the drivers to start...")
    time.sleep(2)
    return driver


def sign_in(url: str, driver: object, username: str, password: str) -> None:
    logging.debug("Starting to load the page...")
    driver.get(url)
    time.sleep(3)
    logging.debug("Page loaded...")

    logging.debug("signing in...")

    try:
        # Check if we need to click "Sign in with email" button first
        try:
            # Look for "Sign in with email" button on the new LinkedIn login page
            email_signin_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in with email')]")
            logging.debug("Found 'Sign in with email' button, clicking it...")
            email_signin_btn.click()
            time.sleep(2)
        except:
            logging.debug("No 'Sign in with email' button found, proceeding to direct login...")
            pass

        # Now try to find username field
        try:
            username_input_box = driver.find_element(By.ID, value="session_key")
        except:
            # Alternative: try by name attribute
            username_input_box = driver.find_element(By.NAME, value="session_key")
        
        username_input_box.send_keys(username)
        time.sleep(0.5)

        try:
            password_input_box = driver.find_element(By.ID, value="session_password")
        except:
            # Alternative: try by name attribute
            password_input_box = driver.find_element(By.NAME, value="session_password")
        
        password_input_box.send_keys(password)
        time.sleep(0.5)

        # Try multiple selectors for the sign-in button
        try:
            btn = driver.find_element(By.CLASS_NAME, value="sign-in-form__submit-btn--full-width")
        except:
            try:
                btn = driver.find_element(By.XPATH, "//button[@type='submit']")
            except:
                btn = driver.find_element(By.XPATH, "//button[contains(@class, 'sign-in-form__submit-button')]")
        
        btn.click()
        time.sleep(10)
        print("✅ Signed in successfully!")
        logging.info("Successfully signed in to LinkedIn")
        
    except Exception as e:
        # Instead of exiting, we allow the user to manual login
        print("\n" + "="*60)
        print("⚠️  AUTOMATED LOGIN FAILED OR NOT ATTEMPTED")
        print("="*60)
        print("We could not automatically log you in (likely due to Captcha/Security).")
        print("Please log in MANUALLY in the Chrome window that is open.")
        print("="*60 + "\n")
        
        # Wait for user confirmation
        input("👉 Please log in, wait for the feed to load, then press ENTER here to continue...")
        logging.info("User confirmed manual login.")

def parse_urls_from_filepath(path: str) -> List[str]:
    try:
        with open(path, "r") as f:
            urls = f.readlines()
        urls = [url.strip() for url in urls]
        return urls
    except Exception as e:
        logging.exception(e)
        logging.critical("Error while reading the file...")
        exit(1)

def extract_profile_information(url: str, driver: object, save: bool, platform: str = "linkedin") -> None:
    """
    Extract profile information from LinkedIn or GitHub.

    Args:
        url: Profile URL or username
        driver: Selenium WebDriver instance
        save: Whether to save output to file
        platform: Platform to scrape ('linkedin' or 'github')
    """
    if platform == "github":
        # Extract username from URL or use as-is
        if url.startswith("http"):
            username = url.rstrip('/').split('/')[-1]
        else:
            username = url

        print(f"Scraping GitHub profile: {username}")

        # Get GitHub token from environment if available
        github_token = os.getenv("GITHUB_TOKEN")

        # GitHub scraper uses API primarily, driver is optional
        extractor = GitHubScraper(username, driver=driver, save=save, api_token=github_token)

        if save:
            extractor.save_output_in_file()
        else:
            print(extractor.output)

    else:  # LinkedIn
        ### GETTING PROFILE ###
        profile_url = url
        page_source = get_profile(driver, profile_url)
        ### PROFILE ACQUIRED ###

        ### EXTRACTING INFORMATION ###
        time.sleep(2)
        extractor = LinkedinScraper(page_source, driver, save)

        if save:
            extractor.save_output_in_file()
        else:
            print(extractor.output)

        ### INFORMATION EXTRACTED ###


def scroll_to_bottom(driver: Any) -> None:
    """Scroll to bottom of page to load all dynamic content"""
    logging.debug("Scrolling to load all sections...")
    
    # Get initial page height
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # Scroll in increments to trigger lazy loading
    scroll_pause_time = 1.5
    scroll_increment = 800
    
    current_position = 0
    while current_position < last_height:
        # Scroll down by increment
        current_position += scroll_increment
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        time.sleep(scroll_pause_time)
        
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height > last_height:
            last_height = new_height
    
    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    logging.debug("Scrolling complete")


def get_profile(driver: Any, url: str) -> str:
    if driver.current_url != url:
        logging.debug("getting profile...")

        driver.get(url)
        time.sleep(5)  # Increased from 3 to 5 seconds

        logging.debug("profile loaded...")
    else:
        logging.debug("profile already loaded...")

    # Scroll to load all dynamic sections
    scroll_to_bottom(driver)
    
    # Wait a bit more after scrolling
    time.sleep(2)
    
    profile = driver.page_source
    return profile


if __name__ == "__main__":
    ### PARSING ARGUMENTS ##
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--path",
        type=str,
        help="Path to the file containing URL's in .txt format",
        default=None,
    )
    group.add_argument(
        "--url",
        type=str,
        help="URL of the profile to scrape (LinkedIn or GitHub)",
        default="https://www.linkedin.com/in/kshivendu/",
    )

    parser.add_argument(
        "--platform",
        type=str,
        choices=["linkedin", "github"],
        help="Platform to scrape (linkedin or github)",
        default="linkedin",
    )
    parser.add_argument(
        "--running",
        type=bool,
        help="Take control of the already running chrome instance in debug mode (for LinkedIn or GitHub contribution scraping)",
        default=False,
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port number of the already running chrome instance in debug mode with LinkedIn signed in",
        default=int(os.getenv("CHROME_DEBUG_PORT", "9222")),
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Host address of the Chrome instance (use Windows IP for WSL, e.g., 172.24.128.1)",
        default="localhost",
    )
    parser.add_argument(
        "--save",
        type=bool,
        help="Save the output in a json file",
        default=False,
    )
    parser.add_argument(
        "--debug",
        type=bool,
        help="Debug mode",
        default=False,
    )
    parser.add_argument(
        "--headless",
        type=bool,
        help="Run Chrome in headless mode (no GUI)",
        default=False,
    )

    args = parser.parse_args()

    ### ARGUMENTS PARSED ###

    ### LOGGING CONFIG ###
    logging.basicConfig(filename="app.log", filemode="w")

    # adding sep log file for selenium
    selenium_logger = logging.getLogger("selenium.webdriver")
    selenium_logger.setLevel(logging.CRITICAL)

    logger = logging.getLogger()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    ### GETTING DRIVERS ###

    # GitHub API mode - no driver needed unless scraping contributions
    if args.platform == "github" and not args.running:
        print(f"Using GitHub API to scrape profile (no authentication required)")
        print("Set GITHUB_TOKEN environment variable to increase API rate limits")
        driver = None

        # If user wants contribution graph, they need a driver
        if args.save:
            print("Note: To scrape contribution graphs, use --running True with a browser")

    elif not args.running:
        # LinkedIn mode - requires login
        if args.platform == "linkedin":
            # Try to get credentials from environment variables first
            username = os.getenv("LINKEDIN_USERNAME")
            password = os.getenv("LINKEDIN_PASSWORD")

            # Fallback to config.ini if environment variables not set
            if not username or not password:
                logging.info("Environment variables not found, trying config.ini...")
                config = ConfigParser()
                try:
                    config.read("config.ini")
                    username = config["linkedin"]["username"]
                    password = config["linkedin"]["password"]
                except Exception as e:
                    logging.exception(e)
                    logging.critical("Error: No credentials found in environment variables or config.ini")
                    logging.critical("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD environment variables")
                    logging.critical("or create a config.ini file with your credentials")
                    exit(1)
            else:
                logging.info("Using credentials from environment variables")

            url = "https://www.linkedin.com/"
            driver = get_selenium_drivers(args.running, headless=args.headless)
            sign_in(url, driver, username, password)
        else:
            # GitHub with headless mode
            driver = get_selenium_drivers(args.running, headless=args.headless)
    else:
        # Remote debugging mode for both platforms
        driver = get_selenium_drivers(args.running, portnumber=args.port, host=args.host)

    ### DRIVER ACQUIRED ###

    if args.path is not None:
        profile_urls = parse_urls_from_filepath(path=args.path)
        for url in profile_urls:
            extract_profile_information(url, driver, args.save, args.platform)
    else:
        extract_profile_information(args.url, driver, args.save, args.platform)

    exit(0)        
