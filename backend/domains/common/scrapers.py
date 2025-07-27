from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC

NAVER_BASE_URL = "https://new-m.pay.naver.com"


class SeleniumClient:

    def __init__(self, driver: Chrome, timeout: int = 10):
        self.driver = driver
        self.timeout = timeout

    @property
    def next_page_button(self):
        selector = 'button[class*=" Pagination_next"]'
        wait = WebDriverWait(self.driver, self.timeout)
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    @property
    def has_next_page(self):
        disabled = self.next_page_button.get_attribute("disabled")
        return disabled is None


class BaseNaverCrawler(ABC, SeleniumClient):

    @abstractmethod
    def scrape_detail(self, url: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def scrape_urls(self, path: str) -> List[str]:
        pass
