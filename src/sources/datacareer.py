from __future__ import annotations

import hashlib
import re
from typing import Optional
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.schema import SCHEMA_COLUMNS


# NOTE: Your HTML is from datacareer.ch (not datajobs.ch)
BASE_URL = "https://www.datacareer.ch"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CIP-StudentProject/1.0)"
}


def _make_job_id(source: str, url: str) -> str:
    return hashlib.sha1(f"{source}|{url}".encode("utf-8")).hexdigest()


def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _get_soup(url: str, timeout: int = 30) -> BeautifulSoup:
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def collect_raw(
    limit: int = 60,
    start_url: Optional[str] = None,
    max_pages: int = 10,
) -> pd.DataFrame:
    """
    Updated collector for datacareer.ch job listings (category: Data Science).

    The website uses a "Load more" button, but under the hood it loads:
      /jobs/?categories[]=Data Science&page=2,3,...

    So we can emulate this with requests + BeautifulSoup (no Selenium needed here).
    """
    source = "datacareer"

    # Matches the site JS pattern; percent-encoded brackets are fine too
    start_url = start_url or f"{BASE_URL}/jobs/?categories%5B%5D=Data%20Science"

    rows = []
    seen_urls: set[str] = set()

    for page in range(1, max_pages + 1):
        if len(rows) >= limit:
            break

        if page == 1:
            page_url = start_url
        else:
            # Equivalent to their JS: '?categories[]=Data%20Science&page=' + page
            page_url = f"{BASE_URL}/jobs/?categories%5B%5D=Data%20Science&page={page}"

        soup = _get_soup(page_url)

        cards = soup.select("article.listing-item.listing-item__jobs")
        if not cards:
            # No more listings
            break

        for card in cards:
            # Title + detail URL
            a = card.select_one(".listing-item__title a.link")
            title = _clean_text(a.get_text(" ", strip=True)) if a else ""
            url = urljoin(BASE_URL, a["href"]) if a and a.get("href") else ""
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

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

            # Salary doesn't appear in listing HTML (in your snippet), keep empty for now
            salary_raw = ""

            rows.append(
                {
                    "source": source,
                    "url": url,
                    "job_id": _make_job_id(source, url),
                    "title": title,
                    "company": company,
                    "location_raw": location_raw,
                    "posted_date": posted_date,
                    "employment_type": employment_type,
                    "salary_raw": salary_raw,
                    "description_raw": description_raw,
                }
            )

            if len(rows) >= limit:
                break

    return pd.DataFrame(rows)


def to_schema(df_raw: pd.DataFrame, scraped_at: str) -> pd.DataFrame:
    """
    Map raw dataframe to the common schema.
    Missing fields are filled with empty strings / NA.
    """
    df = df_raw.copy()

    # Ensure required base cols exist
    base_cols = [
        "source",
        "url",
        "job_id",
        "title",
        "company",
        "location_raw",
        "posted_date",
        "employment_type",
        "salary_raw",
        "description_raw",
    ]
    for col in base_cols:
        if col not in df.columns:
            df[col] = ""

    # Minimal cleaning/enrichment placeholders
    df["scraped_at"] = scraped_at
    df["canton"] = ""          # optionally map later from location_raw
    df["seniority"] = ""       # optionally infer later from title
    df["description_clean"] = df["description_raw"].fillna("").map(_clean_text)

    # Skills: keep empty for now; your shared skills.py can enrich later
    df["skills"] = ""
    df["skill_count"] = 0

    df["salary_raw"] = df["salary_raw"].fillna("").astype(str)
    df["salary_available"] = (df["salary_raw"].str.len() > 0).astype(int)

    # Fill any missing schema columns
    for c in SCHEMA_COLUMNS:
        if c not in df.columns:
            df[c] = ""

    # Return in exact schema order
    return df[SCHEMA_COLUMNS]