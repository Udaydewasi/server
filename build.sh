#!/bin/bash

# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
mkdir -p google-chrome
dpkg -x google-chrome-stable_current_amd64.deb google-chrome

# Add Chrome to PATH
export PATH="$(pwd)/google-chrome/opt/google/chrome:$PATH"

# Get Chrome version and extract the major version number
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1)
echo "Chrome version: $CHROME_VERSION"

# Fetch the correct ChromeDriver version
CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)
if [[ $CHROMEDRIVER_VERSION == *"Error"* ]]; then
    echo "Failed to fetch ChromeDriver version. Using latest stable version."
    CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
fi
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"

# Download and install ChromeDriver
wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver $(pwd)/chromedriver  # Move ChromeDriver to the current directory
chmod +x $(pwd)/chromedriver

# Add ChromeDriver to PATH
export PATH="$(pwd):$PATH"

# Install Python dependencies
pip install -r requirements.txt