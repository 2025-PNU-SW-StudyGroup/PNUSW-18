#!/bin/bash

# Chrome 버전 확인
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
echo "Detected Chrome version: $CHROME_VERSION"

# ChromeDriver 다운로드 URL
CHROMEDRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_VERSION}/linux64/chromedriver-linux64.zip"

# ChromeDriver 다운로드 및 설치
wget -O chromedriver_linux64.zip $CHROMEDRIVER_URL
unzip -o chromedriver_linux64.zip
sudo mv -f chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
sudo chown root:root /usr/local/bin/chromedriver
sudo chmod +x /usr/local/bin/chromedriver

# 정리
rm -rf chromedriver_linux64.zip chromedriver-linux64

echo "ChromeDriver $CHROME_VERSION has been installed successfully."
chromedriver --version
