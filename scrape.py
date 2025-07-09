#without Brightdata
import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
import time

#With brightdata 
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re

load_dotenv()
SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")
print(f"SBR WebDriver URL: {SBR_WEBDRIVER}")
if not SBR_WEBDRIVER:
    raise ValueError("SBR_WEBDRIVER URL is missing or not loaded from .env")

def scrape_website_nobright(website, timeout=5):
    """
    Scrapes a website without using Brightdata.

    Args:
        website (str): The URL of the website to scrape.
        timeout (int): Wait time after loading the page.

    Returns:
        str: The HTML content of the scraped webpage.
    """
    print("Launching chromedriver (nobright)...")
    chrome_driver_path = "./chromedriver.exe"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Optional: Run in headless mode
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try:
        driver.get(website)
        print(f"Page has been loaded: {website}")
        time.sleep(timeout)  # Wait for dynamic content to load
        html = driver.page_source
        return html
    finally:
        driver.quit()

def scrape_website_brightdata(website, timeout=10):
    """
    Scrapes a website using Brightdata (with captcha handling).

    Args:
        website (str): The URL of the website to scrape.
        timeout (int): Wait time after loading the page.

    Returns:
        str: The HTML content of the scraped webpage.
    """
    print("Connecting to Scraping Browser (Brightdata)...")
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
    with Remote(sbr_connection, options=ChromeOptions()) as driver:
        driver.get(website)
        print("Waiting captcha to solve...")
        try:
            solve_res = driver.execute(
                "executeCdpCommand",
                {
                    "cmd": "Captcha.waitForSolve",
                    "params": {"detectTimeout": 10000},
                },
            )
            print("Captcha solve status:", solve_res["value"]["status"])
        except Exception as e:
            print(f"Error while solving captcha: {e}")
            # Depending on implementation, you might choose to proceed or raise an error

        print("Navigated! Scraping page content...")
        time.sleep(timeout)  # Wait for dynamic content to load
        html = driver.page_source
        return html
    
def scrape_website_combined(website, nobright_timeout=5, brightdata_timeout=10):
    """
    Attempts to scrape a website using the nobright method.
    If a captcha is detected, falls back to the brightdata method.

    Args:
        website (str): The URL of the website to scrape.
        nobright_timeout (int): Wait time after loading the page with the nobright method.
        brightdata_timeout (int): Wait time after loading the page with the brightdata method.

    Returns:
        str: The HTML content of the scraped webpage.
    """
    print("Attempting to scrape without Brightdata...")
    try:
        html = scrape_website_nobright(website, timeout=nobright_timeout)
        print("Scraping completed with nobright method.")
        if detect_captcha(html):
            print("Captcha detected using nobright method. Switching to brightdata method...")
            html = scrape_website_brightdata(website, timeout=brightdata_timeout)
            print("Scraping completed with brightdata method.")
        else:
            print("No captcha detected. Using nobright method's content.")
        return html
    except Exception as e:
        print(f"Error during nobright scraping: {e}")
        print("Attempting to scrape using brightdata method...")
        try:
            html = scrape_website_brightdata(website, timeout=brightdata_timeout)
            print("Scraping completed with brightdata method.")
            return html
        except Exception as e_bright:
            print(f"Error during brightdata scraping: {e_bright}")
            raise e_bright  # Re-raise exception after logging



def detect_captcha(html_content):
    """
    Detects the presence of a captcha in the provided HTML content.

    Args:
        html_content (str): The HTML content of the webpage.

    Returns:
        bool: True if a captcha is detected, False otherwise.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    lower_html = html_content.lower()

    # 1. Look for common captcha keywords
    captcha_keywords = ["captcha", "g-recaptcha", "h-captcha", "recaptcha", "human verification"]
    for keyword in captcha_keywords:
        if keyword in lower_html:
            return True

    # 2. Look for known captcha service scripts
    captcha_scripts = [
        "www.google.com/recaptcha/",
        "www.gstatic.com/recaptcha/",
        "hcaptcha.com",
        "api.hcaptcha.com",
    ]
    for script_url in captcha_scripts:
        if script_url in lower_html:
            return True

    # 3. Check for specific HTML elements commonly used in captchas
    captcha_div_ids = ["captcha", "recaptcha", "h-captcha"]
    for div_id in captcha_div_ids:
        if soup.find(id=div_id):
            return True

    # 4. Use regex to detect captcha-related patterns (optional)
    captcha_patterns = [
        r"data-sitekey\s*=",
        r"api\.hcaptcha\.com",
        r"onload=initRecaptcha",
    ]
    for pattern in captcha_patterns:
        if re.search(pattern, html_content, re.IGNORECASE):
            return True

    return False



def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""


def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Get text or further process the content
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content


def split_dom_content(dom_content, max_length=8000, max_batches=20):
    chunks = [
        dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)
    ]
    if len(chunks) > max_batches:
        raise ValueError(
            f"Content exceeds the maximum allowed size of {max_length * max_batches} characters "
            f"({max_batches} batches of {max_length} characters each). Please provide a shorter URL or "
            f"adjust the content length."
        )
    return chunks