from __future__ import annotations

import time
import hashlib
import re
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


BASE_URL = "https://www.datacareer.ch"
START_URL = "https://www.datacareer.ch/categories/datascience/"


def _make_job_id(source: str, url: str) -> str:
    return hashlib.sha1(f"{source}|{url}".encode("utf-8")).hexdigest()


def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _make_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1400,900")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def collect_raw(limit: int = 30, load_more_clicks: int = 3, headless: bool = True) -> pd.DataFrame:
    """Selenium collector: click 'Load more' and extract listing fields."""
    source = "datacareer"
    driver = _make_driver(headless=headless)

    try:
        driver.get(START_URL)
        wait = WebDriverWait(driver, 15)

        for _ in range(load_more_clicks):
            try:
                btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.load-more")))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.5)
                btn.click()
                time.sleep(1.5)
            except Exception:
                break

        soup = BeautifulSoup(driver.page_source, "html.parser")

        rows = []
        for card in soup.select("article.listing-item.listing-item__jobs"):
            a = card.select_one(".listing-item__title a.link")
            title = _clean_text(a.get_text(" ", strip=True)) if a else ""
            url = urljoin(BASE_URL, a["href"]) if a and a.get("href") else ""
            if not url:
                continue

            posted_date = _clean_text(card.select_one(".listing-item__date").get_text(" ", strip=True)) \
                if card.select_one(".listing-item__date") else ""

            employment_type = _clean_text(card.select_one(".listing-item__employment-type").get_text(" ", strip=True)) \
                if card.select_one(".listing-item__employment-type") else ""

            company = _clean_text(card.select_one(".listing-item__info--item-company").get_text(" ", strip=True)) \
                if card.select_one(".listing-item__info--item-company") else ""

            location_raw = _clean_text(card.select_one(".listing-item__info--item-location").get_text(" ", strip=True)) \
                if card.select_one(".listing-item__info--item-location") else ""

            description_raw = _clean_text(card.select_one(".listing-item__desc").get_text(" ", strip=True)) \
                if card.select_one(".listing-item__desc") else ""

            rows.append({
                "source": source,
                "url": url,
                "job_id": _make_job_id(source, url),
                "title": title,
                "company": company,
                "location_raw": location_raw,
                "posted_date": posted_date,
                "employment_type": employment_type,
                "salary_raw": "",
                "description_raw": description_raw,
            })

            if len(rows) >= limit:
                break

        return pd.DataFrame(rows)

    finally:
        driver.quit()