# src/pipeline.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import pandas as pd

from src.sources.datacareer_selenium import collect_raw as collect_raw_selenium
from src.sources.datacareer import to_schema

DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")


def run() -> pd.DataFrame:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    scraped_at = datetime.now().isoformat(timespec="seconds")

    # Collect using Selenium
    raw_jobs = collect_raw_selenium(limit=20, load_more_clicks=2, headless=True)

    # Map to schema
    jobs = to_schema(raw_jobs, scraped_at=scraped_at)

    # Merge
    df = pd.concat([jobs], ignore_index=True)

    # Save
    out_path = DATA_PROCESSED / f"jobs_combined_{scraped_at}.csv"
    df.to_csv(out_path, index=False)

    print(f"Saved: {out_path}")
    return df


if __name__ == "__main__":
    df = run()
    print(df.head(3))
    print("Rows:", len(df))