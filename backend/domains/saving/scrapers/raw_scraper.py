import re
from typing import Any, Dict, List
from bs4 import BeautifulSoup, Tag
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By

import time

from domains.common.scrapers import NAVER_BASE_URL, BaseNaverCrawler
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def parse_product_guide(soup: BeautifulSoup):
    """상품 상세 정보 추출"""

    category_map = {
        "기간": "term",
        "금액": "amount",
        "대상": "targets",
        "예금자 보호": "protection",
        "이자지급": "inssuance",
        "적립방법": "earn_method",
        "가입방법": "enroll_method",
        "유의": "warnings",
    }

    product_guide_element = soup.select_one("#PRODUCT_GUIDE")

    if not product_guide_element:
        raise ValueError("상품 상세 정보 데이터가 존재하지 않습니다.")

    items = product_guide_element.select('[class^="TextList_item"]')

    data = {}

    for item in items:
        dt = item.select_one("dt")
        dd = item.select_one("dd")

        if not dt or not dd:
            raise ValueError("상품 상세 정보 데이터가 존재하지 않습니다.")

        category = dt.get_text()

        if category not in category_map:
            raise ValueError("잘못된 상품 상세 정보입니다.")

        data[category_map[category]] = dd.get_text()

    return data


def parse_basic_info(soup: BeautifulSoup):
    """상품 기본 정보 추출"""

    main_info_element = soup.find(class_=re.compile('^MainInfo_article'))
    #main_info_element = soup.find(class=re.compile('^=MainInfo_article'))

    if not main_info_element:
        raise ValueError("상품 기본 정보가 없습니다.")

    assert type(main_info_element) is Tag

    data = {}

    title_element = main_info_element.select_one('[class^="MainInfo_title"]')
    if not title_element:
        raise ValueError("상품명이 존재하지 않습니다.")

    data["title"] = title_element.get_text(strip=True)

    institution_element = title_element.next_sibling
    if not institution_element:
        raise ValueError("회사명이 존재하지 않습니다.")

    data["institution"] = institution_element.get_text(strip=True)

    event_element = main_info_element.select_one('[class^="MainInfo_area-event"]')
    if event_element:
        desc_element = soup.find(class_=re.compile('^MainInfo_desc'))
        if desc_element:
            data["event_offer"] = desc_element.get_text(strip=True)

    base_interest_rate_element = main_info_element.select(
        'dd[class^="MainInfo_rate"]')[-1]
    max_interest_rate_element = main_info_element.select(
        'dd[class^="MainInfo_rate"]')[0]

    data["base_interest_rate"] = base_interest_rate_element.get_text(strip=True)
    data["max_interest_rate"] = max_interest_rate_element.get_text(strip=True)

    return data


def parse_interest_rate_guide(soup: BeautifulSoup):
    """금리 관련 정보 추출"""

    product_guide_element = soup.select_one("#INTEREST_RATE_GUIDE")

    if not product_guide_element:
        raise ValueError("우대금리 데이터가 존재하지 않습니다.")

    data = {}

    # 기간별 금리 엘리먼트
    per_terms_element = product_guide_element.select_one(
        '[class^="InterestRateGuide_area-table"]')

    if per_terms_element:
        table = per_terms_element.select_one("table")
        if not table:
            raise ValueError("기간별 금리 표가 없습니다")

        data["interest_rate_per_terms"] = str(table.prettify())

    # 금리 안내 섹션의 텍스트 엘리먼트
    interests_text_elements = product_guide_element.select(
        '[class^="InterestRateGuide_area-text-info"]')

    for element in interests_text_elements:

        label_element = element.select_one('[class^="TextList_label"]')
        if not label_element:
            continue

        label_text = label_element.get_text(strip=True)

        if label_text == "조건별":

            items = element.select('[class^="TextList_item"]')

            conditions: List[str] = []

            for item in items:

                dt = item.select_one("dt")
                dd = item.select_one("dd")

                if not dt or not dd:
                    raise ValueError("우대금리 조건에 대한 설명이 없습니다.")

                list_element = dd.select_one("ul > li")
                p_element = dd.select_one("p")

                if not list_element and p_element:
                    data["description"] = dd.get_text(strip=True)
                    continue

                if not list_element and not p_element:
                    data["interest_type"] = dd.get_text(strip=True)
                    continue

                condition_element = dd.select_one("ul")
                if not condition_element:
                    continue

                conditions.append(condition_element.get_text(strip=True,
                                                             separator="\n"))

            data["conditions"] = conditions

    return data


def parse_raw_data(soup: BeautifulSoup) -> Dict[str, Any]:

    return {
        "basic_info": parse_basic_info(soup),
        "product_guide": parse_product_guide(soup),
        "interest_rate_guide": parse_interest_rate_guide(soup),
    }


class RawSavingCrawler(BaseNaverCrawler):

    def scrape_detail(self, url: str):
        print(f"적금 상품 상세 데이터 수집중 (url: {url})")

        self.driver.get(url)

        time.sleep(0.1)

        html = self.driver.page_source
        soup = BeautifulSoup(html)

        raw_data = parse_raw_data(soup)
        raw_data["url"] = url

        return raw_data

    def scrape_urls(self, path: str = "/savings/list/saving"):
        print("적금 상품 URL 수집중...")

        list_url = f"{NAVER_BASE_URL}{path}"

        self.driver.get(list_url)

        urls: List[str] = []

        while True:

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    '[class^="ProductListSection_article"] a[class^="ProductList_link"]'
                )))

            products = self.driver.find_elements(
                by=By.CSS_SELECTOR,
                value=
                '[class^="ProductListSection_article"] a[class^="ProductList_link"]')

            for product in products:
                href = product.get_attribute("href")
                if not href:
                    continue

                urls.append(href)

            if not self.has_next_page:
                break

            self.next_page_button.click()

        return urls


import json

if __name__ == "__main__":

    driver = Chrome()
    crawler = RawSavingCrawler(driver)

    urls = crawler.scrape_urls()

    datas = []

    with open("savings.jsonl", "w") as f:

        for url in urls:
            data = crawler.scrape_detail(url)
            json_line = json.dumps(data, ensure_ascii=False)
            f.write(json_line + "\n")

    print("크롤링 성공!")
