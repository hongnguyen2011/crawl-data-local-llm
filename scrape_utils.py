#without Brightdata
import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

#With brightdata 
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re
from urllib.parse import urljoin, urlparse

load_dotenv()
SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")
print(f"SBR WebDriver URL: {SBR_WEBDRIVER}")
# Không raise exception ở đây, sẽ kiểm tra khi sử dụng hàm scrape_website_brightdata

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
    
    # Sử dụng WebDriver Manager để tự động tải và quản lý ChromeDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Optional: Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    try:
        # WebDriver Manager sẽ tự động tải ChromeDriver phiên bản tương thích
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(website)
        print(f"Page has been loaded: {website}")
        time.sleep(timeout)  # Wait for dynamic content to load
        html = driver.page_source
        return html
    except Exception as e:
        print(f"Error in scrape_website_nobright: {e}")
        raise e
    finally:
        try:
            driver.quit()
        except:
            pass

def scrape_website_brightdata(website, timeout=10):
    """
    Scrapes a website using Brightdata (with captcha handling).

    Args:
        website (str): The URL of the website to scrape.
        timeout (int): Wait time after loading the page.

    Returns:
        str: The HTML content of the scraped webpage.
    """
    if not SBR_WEBDRIVER:
        raise ValueError("SBR_WEBDRIVER URL is missing or not loaded from .env")
    
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
    If a captcha is detected and SBR_WEBDRIVER is available, falls back to the brightdata method.
    If SBR_WEBDRIVER is not available, uses only the nobright method.

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
            print("Captcha detected using nobright method.")
            if SBR_WEBDRIVER:
                print("SBR_WEBDRIVER available. Switching to brightdata method...")
                try:
                    html = scrape_website_brightdata(website, timeout=brightdata_timeout)
                    print("Scraping completed with brightdata method.")
                except Exception as e_bright:
                    print(f"Error during brightdata scraping: {e_bright}")
                    print("Using nobright method's content despite captcha detection.")
            else:
                print("SBR_WEBDRIVER not available. Using nobright method's content despite captcha detection.")
        else:
            print("No captcha detected. Using nobright method's content.")
        return html
    except Exception as e:
        print(f"Error during nobright scraping: {e}")
        if SBR_WEBDRIVER:
            print("Attempting to scrape using brightdata method...")
            try:
                html = scrape_website_brightdata(website, timeout=brightdata_timeout)
                print("Scraping completed with brightdata method.")
                return html
            except Exception as e_bright:
                print(f"Error during brightdata scraping: {e_bright}")
                raise e_bright  # Re-raise exception after logging
        else:
            print("SBR_WEBDRIVER not available. Cannot use brightdata method.")
            raise e  # Re-raise the original exception



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


def clean_body_content_with_links_and_images(body_content, base_url=None):
    """
    Làm sạch nội dung HTML nhưng giữ lại thông tin về links và images
    
    Args:
        body_content (str): HTML content của body
        base_url (str): Base URL để convert relative URLs thành absolute URLs
        
    Returns:
        str: Cleaned content với thông tin links và images được giữ lại
    """
    soup = BeautifulSoup(body_content, "html.parser")

    def make_absolute_url(url, base_url):
        """Chuyển đổi relative URL thành absolute URL"""
        if not url or not base_url:
            return url
        try:
            return urljoin(base_url, url)
        except:
            return url

    # Loại bỏ script và style
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Xử lý images - thêm thông tin src vào text
    for img in soup.find_all('img'):
        img_src = img.get('src', '')
        img_alt = img.get('alt', '')
        img_title = img.get('title', '')
        
        # Chuyển đổi relative URL thành absolute URL
        if img_src and base_url:
            img_src = make_absolute_url(img_src, base_url)
        
        # Tạo text mô tả cho image
        img_info = []
        if img_alt:
            img_info.append(f"Alt: {img_alt}")
        if img_title:
            img_info.append(f"Title: {img_title}")
        if img_src:
            img_info.append(f"URL: {img_src}")
            
        img_text = f"[IMAGE: {' | '.join(img_info)}]" if img_info else "[IMAGE]"
        img.replace_with(img_text)

    # Xử lý links - thêm thông tin href vào text
    for link in soup.find_all('a'):
        link_href = link.get('href', '')
        link_text = link.get_text(strip=True)
        link_title = link.get('title', '')
        
        # Chuyển đổi relative URL thành absolute URL
        if link_href and base_url:
            link_href = make_absolute_url(link_href, base_url)
        
        # Tạo text cho link
        if link_href:
            if link_text:
                # Nếu có text và href
                link_replacement = f"{link_text} [LINK: {link_href}]"
            else:
                # Nếu chỉ có href
                link_replacement = f"[LINK: {link_href}]"
        else:
            # Nếu không có href, chỉ giữ text
            link_replacement = link_text
            
        if link_title:
            link_replacement += f" [Title: {link_title}]"
            
        link.replace_with(link_replacement)

    # Xử lý các thẻ media khác (video, audio, source)
    for media in soup.find_all(['video', 'audio', 'source']):
        media_src = media.get('src', '')
        media_type = media.name.upper()
        
        # Chuyển đổi relative URL thành absolute URL
        if media_src and base_url:
            media_src = make_absolute_url(media_src, base_url)
        
        if media_src:
            media.replace_with(f"[{media_type}: {media_src}]")
        else:
            media.replace_with(f"[{media_type}]")

    # Lấy text đã được xử lý
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content


def split_dom_content(dom_content, max_length=8000, max_batches=50):
    """
    Phân chia DOM content thành các chunks nhỏ hơn để AI có thể xử lý tốt hơn
    
    Args:
        dom_content (str): Nội dung DOM cần phân chia
        max_length (int): Độ dài tối đa mỗi chunk (giảm xuống để AI xử lý tốt hơn)
        max_batches (int): Số lượng batch tối đa (tăng lên để xử lý nhiều dữ liệu hơn)
    
    Returns:
        list: Danh sách các chunks
    """
    chunks = [
        dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)
    ]
    if len(chunks) > max_batches:
        raise ValueError(
            f"Content exceeds the maximum allowed size of {max_length * max_batches} characters "
            f"({max_batches} batches of {max_length} characters each). Please provide a shorter URL or "
            f"adjust the content length."
        )
    
    print(f"Chia DOM content thành {len(chunks)} chunks, mỗi chunk tối đa {max_length} ký tự")
    return chunks


def scrape_website_nobright_only(website, timeout=5):
    """
    Scrapes a website using only the nobright method (without BrightData).
    This is a simplified version that doesn't require SBR_WEBDRIVER.

    Args:
        website (str): The URL of the website to scrape.
        timeout (int): Wait time after loading the page.

    Returns:
        str: The HTML content of the scraped webpage.
    """
    print("Scraping using nobright method only...")
    return scrape_website_nobright(website, timeout)


def analyze_content_for_missing_data(dom_content):
    """
    Phân tích DOM content để tìm dấu hiệu có thể có nhiều dữ liệu hơn
    
    Args:
        dom_content (str): Nội dung DOM đã được clean
        
    Returns:
        dict: Thông tin phân tích và gợi ý
    """
    analysis = {
        'total_length': len(dom_content),
        'potential_issues': [],
        'suggestions': []
    }
    
    # Kiểm tra các dấu hiệu pagination
    pagination_keywords = [
        'trang tiếp', 'next page', 'load more', 'xem thêm', 
        'pagination', 'trang', 'page', 'show more',
        'infinite scroll', 'lazy load'
    ]
    
    for keyword in pagination_keywords:
        if keyword.lower() in dom_content.lower():
            analysis['potential_issues'].append(f"Phát hiện từ khóa phân trang: '{keyword}'")
            analysis['suggestions'].append("Website có thể sử dụng phân trang - cần crawl nhiều trang")
            break
    
    # Kiểm tra JavaScript dynamic loading
    js_indicators = [
        'loading...', 'đang tải', 'spinner', 'skeleton',
        'data-lazy', 'lazy-load', 'dynamic'
    ]
    
    for indicator in js_indicators:
        if indicator.lower() in dom_content.lower():
            analysis['potential_issues'].append(f"Phát hiện loading động: '{indicator}'")
            analysis['suggestions'].append("Nội dung có thể được load bằng JavaScript - cần tăng thời gian chờ")
            break
    
    # Kiểm tra table với ít rows
    if 'table' in dom_content.lower():
        row_count = dom_content.lower().count('<tr>') + dom_content.lower().count('row')
        if row_count < 10:
            analysis['potential_issues'].append(f"Phát hiện bảng với ít dòng dữ liệu: {row_count}")
            analysis['suggestions'].append("Bảng có thể chưa load đầy đủ dữ liệu")
    
    # Kiểm tra list items
    list_count = dom_content.lower().count('<li>') + dom_content.lower().count('item')
    if list_count < 20:
        analysis['potential_issues'].append(f"Phát hiện ít items trong danh sách: {list_count}")
    
    # Kiểm tra content length
    if len(dom_content) < 50000:
        analysis['potential_issues'].append("Nội dung tương đối ngắn")
        analysis['suggestions'].append("Trang web có thể chưa load đầy đủ nội dung")
    
    return analysis