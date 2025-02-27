import time
import re
import os
from datetime import date
import requests
from bs4 import BeautifulSoup
from imap_tools import MailBox, A
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_otp(text):
    """Extract 6-digit OTP from email text"""
    regex = r"please input the code below to continue\.\s*([0-9]{6})"
    matches = re.findall(regex, text, re.IGNORECASE)

    if matches:
        latest_otp = matches[-1]  
        return latest_otp
    else:
        raise ValueError("OTP not found in the email.")

def get_otp(gmail_username, gmail_app_password, imap_server="imap.gmail.com"):   
    """Fetch OTP from Gmail using IMAP"""
    msg_text = ""
    try:
        # Wait for email to arrive
        time.sleep(5)
        with MailBox(imap_server).login(gmail_username, gmail_app_password, "Inbox") as mailbox:
            # Fetch all emails from today that match the sender and subject
            messages = mailbox.fetch(
                A(
                    date_gte=date.today(),
                    from_="donotreply@transactions.upstox.com",
                    subject="OTP to login",
                )
            )

            # Concatenate email contents (HTML or plain text) from the entire thread
            for msg in messages:
                msg_text += msg.html or msg.text  # Combine HTML or plain text parts

        if not msg_text:
            raise ValueError("No email message found.")

        # Parse the combined email content with BeautifulSoup
        soup = BeautifulSoup(msg_text, features="html.parser")
        for script in soup(["script", "style"]):
            script.extract()  # Remove unnecessary scripts/styles

        # Convert parsed HTML to plain text
        text = soup.get_text(separator="\n")
        otp = extract_otp(text)

        return otp
    except Exception as e:
        print(f"An error occurred while fetching OTP: {e}")
        return None

def setup_chrome_driver_for_render():
    """Set up Chrome WebDriver optimized for Render's environment"""
    options = Options()
    
    # Essential headless settings for Render
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Set window size to ensure elements are visible
    options.add_argument("--window-size=1920,1080")
    
    # Avoid detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Set user agent to look more like a real browser
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    # Check common locations for Chrome binary on Render
    if os.path.exists("/opt/render/project/chrome-bin/chrome"):
        options.binary_location = "/opt/render/project/chrome-bin/chrome"
    elif os.path.exists("/usr/bin/google-chrome"):
        options.binary_location = "/usr/bin/google-chrome"
    elif os.path.exists("/usr/bin/chromium"):
        options.binary_location = "/usr/bin/chromium"
    
    # Try to create the driver
    try:
        # Try with default ChromeDriver path in Render
        if os.path.exists("/usr/bin/chromedriver"):
            driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
        else:
            # Fallback to let Selenium find ChromeDriver
            driver = webdriver.Chrome(options=options)
        
        # Remove navigator.webdriver flag
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        raise

def generate_code(url, phone_no, password, gmail_username, gmail_app_password, imap_server="imap.gmail.com"):
    """Generate authorization code by automating the login process"""
    driver = setup_chrome_driver_for_render()
    
    try:
        print("Starting Chrome automation process...")
        # Navigate to the authorization URL
        driver.get(url)
        print("Opened authorization URL")
        
        # Wait for phone input to be visible and interact with it
        wait = WebDriverWait(driver, 30)  # Increased timeout for Render
        
        # Enter phone number
        phone_input = wait.until(EC.element_to_be_clickable((By.ID, "mobileNum")))
        phone_input.clear()
        phone_input.send_keys(phone_no)
        print("Entered phone number")
        
        # Click next button
        next_button = wait.until(EC.element_to_be_clickable((By.ID, "getOtp")))
        next_button.click()
        print("Requested OTP")
        
        # Wait and get OTP
        time.sleep(10)  # Increased wait time for OTP email
        otp = get_otp(gmail_username, gmail_app_password, imap_server)
        print("OTP retrieval process completed")
        
        if not otp:
            raise ValueError("Failed to retrieve OTP")
        
        # Enter OTP
        otp_input = wait.until(EC.element_to_be_clickable((By.ID, "otpNum")))
        otp_input.send_keys(otp)
        
        # Click continue after OTP
        enter_otp_button = wait.until(EC.element_to_be_clickable((By.ID, "continueBtn")))
        enter_otp_button.click()
        print("Submitted OTP")
        
        # Enter PIN/password
        password_input = wait.until(EC.element_to_be_clickable((By.ID, "pinCode")))
        password_input.send_keys(password)
        
        # Click continue after PIN
        enter_pin_button = wait.until(EC.element_to_be_clickable((By.ID, "pinContinueBtn")))
        enter_pin_button.click()
        print("Submitted PIN")
        
        # Wait for redirect to happen (with code in URL)
        time.sleep(10)  # Increased wait time for redirect
        
        # Extract code from URL
        current_url = driver.current_url
        
        code_match = re.search(r"code=([^&]+)", current_url)
        if not code_match:
            raise ValueError(f"Authorization code not found in URL")
            
        code = code_match.group(1)
        print("Successfully extracted authorization code")
        
        return code
    except Exception as e:
        print(f"Error in automation process: {e}")
        # Take screenshot for debugging if possible
        try:
            driver.save_screenshot("/tmp/error_screenshot.png")
            print("Saved error screenshot to /tmp/error_screenshot.png")
        except:
            pass
        raise
    finally:
        driver.quit()
        print("Chrome browser closed")

def get_access_token(api_key, secret_key, redirect_uri, phone_no, password, gmail_username, gmail_app_password, imap_server="imap.gmail.com"):
    """Complete OAuth flow to get access token"""
    # Step 1: Get authorization code
    url = f'https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}'
    try:
        print("Starting Upstox authentication process...")
        code = generate_code(url, phone_no, password, gmail_username, gmail_app_password, imap_server)
        
        # Step 2: Exchange code for access token
        print("Exchanging authorization code for access token...")
        token_url = 'https://api.upstox.com/v2/login/authorization/token'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = {
            'code': code,
            'client_id': api_key,
            'client_secret': secret_key,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }
        
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data['access_token']
        print("Successfully obtained access token")
        
        return access_token
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

# Example usage for testing
if __name__ == "__main__":
    try:
        access_token = get_access_token(
            api_key="173b1d0a-5048-43d4-b23c-8cb1b413d676",
            secret_key="q756s0sih5",
            redirect_uri="http://localhost:3000",
            phone_no="9316443359",
            password="310102",
            gmail_username="vrajpatel0218@gmail.com",
            gmail_app_password="uylm slxy cgqe qwkg"
        )
        print("Access Token:", access_token)
    except Exception as e:
        print(f"Failed to get access token: {e}")