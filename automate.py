from selenium.webdriver.common.by import By
from seleniumbase import Driver
import time
import re
import config
from imap_tools import MailBox, A
from bs4 import BeautifulSoup
import config
import re
import time
from datetime import date
import pandas as pd
import requests


global code
code = ""

def extract_otp(text):
    regex = r"please input the code below to continue\.\s*([0-9]{6})"
    matches = re.findall(regex, text, re.IGNORECASE)

    if matches:
        latest_otp = matches[-1]  
        return latest_otp
    else:
        raise ValueError("OTP not found in the email.")

def get_otp():   
    msg_text = ""
    try:

        time.sleep(5)
        with MailBox(config.imap_server).login(
            config.gmail_username, config.gmail_app_password, "Inbox"

        ) as mailbox:
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

def generate_code (url):

    driver = Driver(uc=True)
    try:
        # Open the login page
        url = url
        driver.uc_open_with_reconnect(url, 4)
        driver.uc_gui_click_captcha()
    
        time.sleep(2)  # Wait for the page to load
    
        # Locate and fill in the phone number field
        phone_input = driver.find_element(By.ID, "mobileNum")
        phone_input.send_keys(config.PHONE_NUMBER)
    
        # Click the 'Next' button
        next_button = driver.find_element(By.ID, "getOtp")
        next_button.click()
    
        time.sleep(2) 
    
        otp_input = driver.find_element(By.ID, "otpNum")  # Change ID as per the website
        otp = get_otp() 
        otp_input.send_keys(otp)
     
        enter_otp_button = driver.find_element(By.ID, "continueBtn")
        enter_otp_button.click()
    
        time.sleep(2)
    
        # Locate and fill in the password field
        password_input = driver.find_element(By.ID, "pinCode")
        password_input.send_keys(config.PASSWORD)
    
        enter_pin_button = driver.find_element(By.ID, "pinContinueBtn")
        enter_pin_button.click()
    
        time.sleep(2)  # Wait for login to process
    
        current_url = driver.current_url
        code = re.search(r"code=([^&]+)", current_url).group(1)

        return code
       
    finally:
        driver.quit()  # Close the browser

def get_access_token() :
    
    url = f'https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={config.apikey}&redirect_uri={config.redirect_uri}'
    code = generate_code(url)
   
    url = 'https://api.upstox.com/v2/login/authorization/token'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = {
        'code': code,
        'client_id': config.apikey,
        'client_secret': config.secretkey,
        'redirect_uri': config.redirect_uri,
        'grant_type': 'authorization_code',
    }
    
    response = requests.post(url, headers=headers, data=data)  
    access_token = response.json()['access_token']
    return access_token
  
acess_token = get_access_token()
# print(acess_token)
    



