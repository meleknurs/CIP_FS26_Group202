"""Collector template for new sources.

Implement `collect_raw(...)` returning a DataFrame with the base columns.
Use requests+BeautifulSoup or Selenium as needed.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urljoin

import pandas as pd

# Required base columns for raw collectors
TEMPLATE_COLUMNS = [
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


def collect_raw(limit: int = 30, headless: bool = False, start_url: Optional[str] = None) -> pd.DataFrame:
	"""Return raw job rows as a DataFrame with `TEMPLATE_COLUMNS`.

	- Implement scraping logic here (requests or selenium).
	- Fill at least the TEMPLATE_COLUMNS for each row.
	- Keep function signature compatible with pipeline.
	"""
	rows: list[dict] = []

	# Example stub row (remove in real collector)
	# rows.append({c: "" for c in TEMPLATE_COLUMNS})

	return pd.DataFrame(rows, columns=TEMPLATE_COLUMNS)


if __name__ == "__main__":
	# Quick local test: print empty template frame
	df = collect_raw(limit=5)
	print(df.head())
