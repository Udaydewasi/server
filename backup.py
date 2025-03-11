from selenium.webdriver.common.by import By
from seleniumbase import Driver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
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

def get_otp(gmail_username, gmail_app_password, imap_server):
    msg_text = ""
    try:

        time.sleep(5)
        with MailBox(imap_server).login(
            gmail_username, gmail_app_password, "Inbox"

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
                messages = mailbox.fetch(
                    A(
                        date_gte=date.today(),
                        from_="noreply@upstox.com",
                        subject="OTP to login",
                    )
                )

            for msg in messages:
                msg_text += msg.html or msg.text

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

def generate_code(url, phone_no, password, gmail_username, gmail_app_password, imap_server):
    driver = Driver(uc=True)
    try:
        # Open the login page
        driver.uc_open_with_reconnect(url, 4)
        driver.uc_gui_click_captcha()

        # Step 1: Enter phone number
        try:
            print(phone_no)
            phone_input = WebDriverWait(driver, 300, poll_frequency=5).until(
                EC.visibility_of_element_located((By.ID, "mobileNum"))
            )
            phone_input.send_keys(phone_no)
        except Exception:
            return {"status": "failed", "message": "Phone input field not found"}

        # Step 2: Click 'Next' button
        try:
            next_button = WebDriverWait(driver, 300, poll_frequency=5).until(
                EC.element_to_be_clickable((By.ID, "getOtp"))
            )
            next_button.click()
            print("next button clicked")
        except Exception:
            return {"status": "failed", "message": "Next button not clickable"}

        # Step 3: Get OTP
        try:
            otp = get_otp(gmail_username, gmail_app_password, imap_server)
            if not otp:
                return {"status": "failed", "message": "OTP not fetched from email"}
        except Exception:
            return {"status": "failed", "message": "Error occurred while fetching OTP"}

        # Step 4: Enter OTP
        try:
            otp_input = WebDriverWait(driver, 300, poll_frequency=5).until(
                EC.visibility_of_element_located((By.ID, "otpNum"))
            )
            otp_input.send_keys(otp)
            print("otp entered")
        except Exception:
            return {"status": "failed", "message": "OTP input field not found"}

        # Step 5: Click 'Continue' after OTP
        try:
            enter_otp_button = WebDriverWait(driver, 300, poll_frequency=5).until(
                EC.element_to_be_clickable((By.ID, "continueBtn"))
            )
            enter_otp_button.click()
            print("otp continue button clicked")
        except Exception:
            return {"status": "failed", "message": "Continue button after OTP not clickable"}

        # Step 6: Enter Password
        try:
            password_input = WebDriverWait(driver, 300, poll_frequency=5).until(
                EC.visibility_of_element_located((By.ID, "pinCode"))
            )
            password_input.send_keys(password)
        except Exception:
            return {"status": "failed", "message": "Password input field not found"}

        # Step 7: Click 'Continue' after Password
        try:
            enter_pin_button = WebDriverWait(driver, 300, poll_frequency=5).until(
                EC.element_to_be_clickable((By.ID, "pinContinueBtn"))
            )
            enter_pin_button.click()
            print("pin continue button clicked")
        except Exception:
            return {"status": "failed", "message": "Continue button after PIN not clickable"}

        # Step 8: Extract Code from URL
        try:
            WebDriverWait(driver, 300, poll_frequency=5).until(
                EC.url_contains("code=")
            )
            current_url = driver.current_url
            code = re.search(r"code=([^&]+)", current_url).group(1)
            
            return {"status": "success", "code": code}
        except Exception:
            return {"status": "failed", "message": "Code not found in URL"}

    finally:
        driver.quit()

def get_access_token(api_key, secret_key, redirect_uri, phone_no, password, gmail_username, gmail_app_password, imap_server) :
    print(api_key, secret_key, redirect_uri, phone_no, password, gmail_username, gmail_app_password, imap_server)
    url = f'https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}'
    response = generate_code(url, phone_no, password, gmail_username, gmail_app_password, imap_server)
    if response["status"] == "success":
        code = response["code"]
    else:
        return response["message"]


    url = 'https://api.upstox.com/v2/login/authorization/token'
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

    response = requests.post(url, headers=headers, data=data)
    access_token = response.json()['access_token']
    print("access token generated successfully", access_token)
    return {"status": "success", "code": access_token}

# acess_token = get_access_token("173b1d0a-5048-43d4-b23c-8cb1b413d67", "q756s0sih5", "http://localhost:3000", "9316443359", "310102", "vrajpatel0218@gmail.com", "uylm slxy cgqe qwkg", "imap.gmail.com")
# print(acess_token)