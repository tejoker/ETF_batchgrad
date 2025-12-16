import time
import logging
import argparse
import os
import io
import json
from base64 import b64decode

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import pytesseract

from ollama_wrapper import OllamaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("visual_scraper.log"),
        logging.StreamHandler()
    ]
)

def get_selenium_drivers(running: bool, **kwargs) -> webdriver.Chrome:
    """
    Initializes Chrome driver. Reused from scraper.py
    """
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    
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
        if running:
            logging.info(f"Connecting to existing Chrome instance on {host}:{portnumber}")
            driver = webdriver.Chrome(options=options)
        else:
            logging.info("Starting new Chrome instance...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logging.critical(f"Driver failed to start: {e}")
        exit(1)

    time.sleep(2)
    return driver

def scroll_to_bottom(driver) -> None:
    """Scroll to bottom of page to load all dynamic content"""
    logging.info("Scrolling to load all sections...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_pause_time = 1.5
    scroll_increment = 800
    
    current_position = 0
    while current_position < last_height:
        current_position += scroll_increment
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height > last_height:
            last_height = new_height
    
    # Scroll back to top for screenshot? 
    # Actually, for a long page, we might want to take multiple screenshots or a full page one.
    # Selenium's save_screenshot usually only captures the viewport or the visible area depending on the driver.
    # For Chrome, standard screenshot is viewport.
    # To capture the whole page properly often requires a stitched approach or headless trickery.
    # For now, let's scroll back to top and assume the user wants a visible screenshot or we do a simple full page trick.
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    logging.info("Scrolling complete")

def capture_full_page(driver) -> Image.Image:
    """
    Captures a full page screenshot by stitching or using CDP.
    Simplest approach: Print to PDF or use a stitching library.
    Here we'll try a simple method: Set window size to body height (if headless) or just take viewport screenshots and stitch.
    
    Given the complexity of stitching, we will start with a tall window approach if headless, or just a viewport screenshot 
    if that contains enough info (it won't).
    
    Let's try a rolling screenshot approach:
    1. Screenshot viewport.
    2. Scroll down by viewport height.
    3. Repeat until bottom.
    4. Stitch.
    """
    
    total_width = driver.execute_script("return document.body.offsetWidth")
    total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
    viewport_width = driver.execute_script("return document.body.clientWidth")
    viewport_height = driver.execute_script("return window.innerHeight")
    
    logging.info(f"Capturing page: {total_width}x{total_height}")
    
    rectangles = []
    i = 0
    while i < total_height:
        ii = 0
        top_height = i + viewport_height
        
        if top_height > total_height:
            top_height = total_height
            
        while ii < total_width:
            top_width = ii + viewport_width
            
            if top_width > total_width:
                top_width = total_width
                
            rectangles.append((ii, i, top_width, top_height))
            
            ii = ii + viewport_width
            
        i = i + viewport_height
        
    stitch_image = Image.new('RGB', (total_width, total_height))
    
    previous = None
    part = 0
    
    for rectangle in rectangles:
        if previous is not None:
            driver.execute_script(f"window.scrollTo({rectangle[0]}, {rectangle[1]})")
            time.sleep(0.5) # Wait for render
            
        file_name = f"part_{part}.png"
        driver.get_screenshot_as_file(file_name)
        screenshot = Image.open(file_name)
        
        if rectangle[1] + viewport_height > total_height:
            offset = (0, total_height - viewport_height)
        else:
            offset = (0, 0)
            
        box = (rectangle[0], rectangle[1], rectangle[2], rectangle[3])
        
        # Calculate paste position
        # This simple stitching is prone to duplicates if headers are sticky.
        # But it's a start.
        # Ideally, we crop the scrollbar out too.
        
        stitch_image.paste(screenshot, (rectangle[0], rectangle[1]))
        os.remove(file_name)
        part += 1
        previous = rectangle
        
    return stitch_image

def process_image(image_path: str):
    logging.info(f"Processing image for OCR: {image_path}")
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        logging.info(f"OCR extracted {len(text)} characters.")
        return text
    except Exception as e:
        logging.error(f"OCR failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Visual LinkedIn Scraper")
    parser.add_argument("--url", type=str, required=True, help="Profile URL")
    parser.add_argument("--running", action="store_true", help="Attach to running Chrome")
    parser.add_argument("--port", type=int, default=9222, help="Debug port")
    parser.add_argument("--headless", action="store_true", help="Headless mode")
    
    args = parser.parse_args()
    
    driver = get_selenium_drivers(
        running=args.running, 
        portnumber=args.port, 
        headless=args.headless
    )

    # Set timeouts to be more generous
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)
    
    try:

        target_url = args.url
        if not target_url.startswith("http"):
            target_url = "https://" + target_url
            
        # Navigate if not already there
        if driver.current_url != target_url:
            logging.info(f"Navigating to {target_url}")
            try:
                driver.get(target_url)
            except Exception as e:
                logging.warning(f"Navigation timeout or error: {e}. Attempting to proceed anyway.")
            time.sleep(3)
        
        # Disable animations for performance
        logging.info("Disabling animations...")
        driver.execute_script("""
            var style = document.createElement('style');
            style.type = 'text/css';
            style.innerHTML = '* { transition: none !important; animation: none !important; }';
            document.head.appendChild(style);
        """)
        time.sleep(1)
        

        # Resize window to reduce rendering load
        try:
            driver.set_window_size(1280, 800)
        except Exception as e:
            logging.warning(f"Could not resize window: {e}")
        time.sleep(1)

        # Rolling OCR Loop
        accumulated_text = []
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        scroll_position = 0
        
        logging.info("Starting Rolling OCR...")
        
        while True:
            # Capture current viewport with retry using CDP
            max_retries = 3
            png_data = None
            
            for attempt in range(max_retries):
                try:
                    # Use CDP which is often faster/more robust than standard save_screenshot
                    result = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})
                    png_data = b64decode(result['data'])
                    break
                except Exception as e:
                    logging.warning(f"Screenshot attempt {attempt+1} failed: {e}")
                    time.sleep(2)
            
            if png_data:
                with open("temp_viewport.png", "wb") as f:
                    f.write(png_data)
                
                # OCR the chunk
                chunk_text = process_image("temp_viewport.png")
                if chunk_text:
                    accumulated_text.append(chunk_text)
            else:
                logging.error("Failed to capture screenshot after retries. Skipping frame.")
            
            # Scroll down
            scroll_position += (viewport_height * 0.8) # 80% scroll to ensure overlap but progress
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(3) # Increased wait time for renderer to catch up
            
            # Check if we reached bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if scroll_position >= new_height:
                break
                
        logging.info("Rolling OCR complete.")
        
        # Combine text
        full_text = "\n".join(accumulated_text)
        
        # Save raw text
        with open("ocr_text.txt", "w") as f:
            f.write(full_text)
            
        if full_text:
            logging.info("Sending accumulated text to Ollama...")
            client = OllamaClient()
            # Updated prompt to handle repetition and noise
            prompt = """
            The following text is extracted from a LinkedIn profile using rolling OCR screenshots. 
            There may be duplicate text or noise (like navigation bars). 
            Ignore the noise and duplicates.
            
            Extract:
            1. Candidate Name (Look at the main profile header, NOT the navbar user)
            2. Headline
            3. Current Company
            4. Summary of Skills
            5. Experience Summary
            """
            
            summary = client.process_profile({"raw_ocr_text": full_text}, custom_prompt=prompt)
            
            print("\n" + "="*50)
            print("OLLAMA SUMMARY")
            print("="*50)
            print(summary)
            print("="*50 + "\n")
            
        # Cleanup
        if os.path.exists("temp_viewport.png"):
            os.remove("temp_viewport.png")
                
    except Exception as e:
        logging.exception(f"Error: {e}")
    finally:
        if not args.running:
            driver.quit()

if __name__ == "__main__":
    main()
