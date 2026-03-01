"""Selenium collector for jobup.ch."""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin, urlsplit

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.jobup.ch"
SEARCH_URL = "https://www.jobup.ch/en/jobs/"

DEFAULT_ROLES = [
    "data scientist",
    "data analyst",
    "machine learning engineer",
    "data engineer",
    "ai engineer",
]


def _make_job_id(source: str, url: str) -> str:
    return hashlib.sha1(f"{source}|{url}".encode("utf-8")).hexdigest()


def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _make_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1400,900")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--lang=en-US")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


@dataclass(frozen=True)
class CollectConfig:
    roles: list[str]
    max_pages_per_role: int = 20
    limit_total: int = 1000
    headless: bool = True
    fetch_details: bool = True
    verbose: bool = False
    page_wait_s: int = 15
    polite_sleep_s: float = 1.0
    max_no_new_pages_per_role: int = 5


def _build_page_url(term: str, page: int) -> str:
    q = quote_plus(term)
    return f"{SEARCH_URL}?term={q}&page={page}"


def _is_job_detail_url(full_url: str) -> bool:
    """Keep only likely job detail URLs."""
    cleaned = re.sub(r"[?#].*$", "", (full_url or "")).rstrip("/")
    if not cleaned.startswith(BASE_URL):
        return False
    if cleaned in {f"{BASE_URL}/en/jobs", f"{BASE_URL}/en/jobs/"}:
        return False

    path_parts = [p for p in urlsplit(cleaned).path.split("/") if p]
    # expected minimum for detail-style urls: /en/jobs/<something>
    if len(path_parts) < 3:
        return False
    if path_parts[:2] != ["en", "jobs"]:
        return False
    if path_parts[2] in {"", "search", "results"}:
        return False
    return True


def _wait_serp_loaded(wait: WebDriverWait) -> None:
    """Wait for SERP cards (best-effort)."""
    try:
        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "div[data-cy='vacancy-serp-item'], [data-cy*='serp' i], #react-root, main, body",
                )
            )
        )
    except Exception:
        pass


def _detail_url_from_card(card, avoid_urls: set[str] | None = None) -> str:
    avoid_urls = avoid_urls or set()
    candidates: list[str] = []

    parent = card
    for _ in range(8):
        parent = parent.parent
        if parent is None:
            break
        if getattr(parent, "name", None) == "a" and parent.get("href"):
            candidates.append(urljoin(BASE_URL, parent.get("href")))

    for a in card.select("a[href]"):
        candidates.append(urljoin(BASE_URL, a.get("href")))

    valid = []
    for c in candidates:
        if not c:
            continue
        # Keep URLs even if they contain tracking/query params like ?term=...
        cleaned = re.sub(r"[?#].*$", "", c).rstrip("/")
        if not _is_job_detail_url(cleaned):
            continue
        valid.append(cleaned)

    if not valid:
        return ""

    # Prefer urls that explicitly contain /detail/, then longer paths.
    ranked = sorted(set(valid), key=lambda u: ("/detail/" not in u, -len(urlsplit(u).path)))
    for u in ranked:
        if u not in avoid_urls:
            return u
    return ranked[0]


def _extract_labeled_value(card, label_prefix: str) -> str:
    labels = card.select("span")
    label_prefix_l = label_prefix.lower()
    for label in labels:
        txt = _clean_text(label.get_text(" ", strip=True)).lower()
        if not txt.startswith(label_prefix_l):
            continue
        parent = label.parent
        if not parent:
            continue
        val = parent.select_one("p")
        if val:
            return _clean_text(val.get_text(" ", strip=True))
    return ""


def _extract_job_links_and_cards(soup: BeautifulSoup) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()

    cards = soup.select("div[data-cy='vacancy-serp-item']")
    if not cards:
        cards = soup.select("[data-cy*='vacancy-serp' i]")
    if not cards:
        cards = soup.select("[data-cy*='serp-item' i]")
    for card in cards:
        url = _detail_url_from_card(card, avoid_urls=seen)
        if not url or url in seen:
            continue
        seen.add(url)

        title_el = card.select_one("span[class*='fw_bold'], h2, h3")
        title = _clean_text(title_el.get_text(" ", strip=True) if title_el else "")

        company_el = card.select_one("p strong, strong")
        company = _clean_text(company_el.get_text(" ", strip=True) if company_el else "")

        posted_date_el = card.select_one("div[data-cy^='serp-item-'] p, p[class*='caption'], p")
        posted_date = _clean_text(posted_date_el.get_text(" ", strip=True) if posted_date_el else "")

        location_raw = _extract_labeled_value(card, "Place of work")
        employment_type = _extract_labeled_value(card, "Contract type")

        rows.append(
            {
                "url": url,
                "title": title,
                "company": company,
                "location_raw": location_raw,
                "posted_date": posted_date,
                "employment_type": employment_type,
                "salary_raw": "",
                "description_raw": "",
            }
        )

    return rows


def _extract_description_from_detail_soup(soup: BeautifulSoup) -> str:
    root = soup.select_one("div[data-cy='vacancy-description']")
    if root:
        teaser = root.select_one("section[aria-label='JobFit teaser']")
        if teaser:
            teaser.decompose()
        text = _clean_text(root.get_text(" ", strip=True))
        if len(text) >= 120:
            return text

    selectors = [
        "div[data-cy='vacancy-description']",
        "[data-cy*='vacancy-description' i]",
        "[data-cy*='description' i]",
        "[class*='description' i]",
        "[class*='job-description' i]",
        "article",
        "main",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if not el:
            continue
        text = _clean_text(el.get_text(" ", strip=True))
        if len(text) >= 120:
            return text

    meta = soup.select_one("meta[property='og:description']")
    if meta and meta.get("content"):
        return _clean_text(meta.get("content") or "")

    return ""


def _extract_header_facts_from_detail_soup(soup: BeautifulSoup) -> dict:
    """Extract stable detail-page facts."""
    out = {
        "title": "",
        "company": "",
        "location_raw": "",
        "posted_date": "",
        "workload_raw": "",
        "employment_type": "",
    }

    h1 = soup.select_one("h1[data-cy='vacancy-title']")
    if h1:
        out["title"] = _clean_text(h1.get_text(" ", strip=True))

    company = soup.select_one("a[data-cy='company-link'] span")
    if company:
        out["company"] = _clean_text(company.get_text(" ", strip=True))

    pub = soup.select_one("li[data-cy='info-publication'] span.white-space_nowrap")
    if pub:
        out["posted_date"] = _clean_text(pub.get_text())

    workload = soup.select_one("li[data-cy='info-workload'] span.white-space_nowrap")
    if workload:
        out["workload_raw"] = _clean_text(workload.get_text())

    contract = soup.select_one("li[data-cy='info-contract'] span")
    if contract:
        out["employment_type"] = _clean_text(contract.get_text())

    location = soup.select_one("div.grid-area_vacancy-info ul > li:not([data-cy]) span")
    if location:
        out["location_raw"] = _clean_text(location.get_text())

    if not out["posted_date"]:
        li = soup.select_one("li[data-cy='info-publication']")
        if li:
            out["posted_date"] = _clean_text(li.get_text(" ", strip=True))

    if not out["workload_raw"]:
        li = soup.select_one("li[data-cy='info-workload']")
        if li:
            out["workload_raw"] = _clean_text(li.get_text(" ", strip=True))

    if not out["employment_type"]:
        li = soup.select_one("li[data-cy='info-contract']")
        if li:
            out["employment_type"] = _clean_text(li.get_text(" ", strip=True))

    if not out["location_raw"]:
        p = soup.select_one("div[data-cy='vacancy-logo'] p")
        if p:
            out["location_raw"] = _clean_text(p.get_text(" ", strip=True))

    return out


def _fetch_detail_bundle(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    url: str,
    sleep_s: float,
) -> dict:
    try:
        driver.get(url)
        try:
            wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "h1[data-cy='vacancy-title'], div.grid-area_vacancy-info ul, div[data-cy='vacancy-description']",
                    )
                )
            )
        except Exception:
            pass

        time.sleep(sleep_s)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        facts = _extract_header_facts_from_detail_soup(soup)
        facts["description_raw"] = _extract_description_from_detail_soup(soup)
        return facts
    except Exception:
        return {
            "title": "",
            "company": "",
            "location_raw": "",
            "posted_date": "",
            "workload_raw": "",
            "employment_type": "",
            "description_raw": "",
        }


def collect_raw(
    roles: list[str] | None = None,
    max_pages_per_role: int = 20,
    limit_total: int = 1000,
    headless: bool = True,
    fetch_details: bool = True,
    verbose: bool = False,
) -> pd.DataFrame:
    cfg = CollectConfig(
        roles=roles or DEFAULT_ROLES,
        max_pages_per_role=max_pages_per_role,
        limit_total=limit_total,
        headless=headless,
        fetch_details=fetch_details,
        verbose=verbose,
    )

    source = "jobup"
    driver = _make_driver(headless=cfg.headless)

    rows: list[dict] = []
    seen_urls: set[str] = set()

    try:
        wait = WebDriverWait(driver, cfg.page_wait_s)

        for term in cfg.roles:
            no_new_pages = 0
            empty_pages = 0

            for page in range(1, cfg.max_pages_per_role + 1):
                if len(rows) >= cfg.limit_total:
                    break

                driver.get(_build_page_url(term, page))
                _wait_serp_loaded(wait)
                time.sleep(cfg.polite_sleep_s)

                soup = BeautifulSoup(driver.page_source, "html.parser")

                page_rows = _extract_job_links_and_cards(soup)
                if not page_rows:
                    empty_pages += 1
                    if cfg.verbose:
                        print(f"[jobup] term='{term}' page={page} cards=0")
                    if empty_pages >= 2:
                        break
                    continue
                empty_pages = 0

                added_this_page = 0

                for r in page_rows:
                    u = r.get("url", "")
                    if not u or u in seen_urls:
                        continue
                    seen_urls.add(u)

                    detail = {}
                    if cfg.fetch_details:
                        detail = _fetch_detail_bundle(driver, wait, u, cfg.polite_sleep_s)

                    title = detail.get("title") or r.get("title", "")
                    company = detail.get("company") or r.get("company", "")
                    location_raw = detail.get("location_raw") or r.get("location_raw", "")
                    posted_date = detail.get("posted_date") or r.get("posted_date", "")
                    employment_type = detail.get("employment_type") or r.get("employment_type", "")
                    workload_raw = detail.get("workload_raw", "")

                    description_raw = detail.get("description_raw") or r.get("description_raw", "")

                    rows.append(
                        {
                            "source": source,
                            "url": u,
                            "job_id": _make_job_id(source, u),
                            "title": title,
                            "company": company,
                            "location_raw": location_raw,
                            "posted_date": posted_date,
                            "employment_type": employment_type,
                            "salary_raw": r.get("salary_raw", ""),
                            "description_raw": description_raw,
                            "workload_raw": workload_raw,
                            "search_term": term,
                        }
                    )
                    added_this_page += 1

                    if len(rows) >= cfg.limit_total:
                        break

                if cfg.verbose:
                    print(
                        f"[jobup] term='{term}' page={page} cards={len(page_rows)} "
                        f"new={added_this_page} total={len(rows)}"
                    )

                if added_this_page == 0:
                    no_new_pages += 1
                    if cfg.verbose:
                        print(f"[jobup] term='{term}' page={page} no-new streak={no_new_pages}")
                    if no_new_pages >= cfg.max_no_new_pages_per_role:
                        if cfg.verbose:
                            print(
                                f"[jobup] term='{term}' stopping pagination after "
                                f"{no_new_pages} consecutive pages with no new jobs."
                            )
                        break
                else:
                    no_new_pages = 0

            if len(rows) >= cfg.limit_total:
                break

        return pd.DataFrame(rows)

    finally:
        driver.quit()


if __name__ == "__main__":
    df = collect_raw(
        roles=DEFAULT_ROLES,
        max_pages_per_role=2,
        limit_total=50,
        headless=False,
        fetch_details=True,
    )
    print(
        df[
            ["search_term", "title", "company", "location_raw", "workload_raw", "posted_date", "employment_type"]
        ].head(10).to_string(index=False)
    )
    print("rows", len(df))
