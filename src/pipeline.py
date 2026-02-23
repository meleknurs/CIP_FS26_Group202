
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.sources import datacareer, bfs  # ictjobs later
# from src import cleaning, skills

DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")


def run() -> pd.DataFrame:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    scraped_at = datetime.now().isoformat(timespec="seconds")

    # 1) collect
    raw_jobs = datacareer.collect_raw(limit=10, max_pages=2)
    jobs = datacareer.to_schema(raw_jobs, scraped_at=scraped_at)

    # Example: BFS (if you have it)
    # raw_bfs = bfs.collect_raw(...)
    # bfs_df = bfs.to_schema(raw_bfs, scraped_at=scraped_at)

    # 2) merge
    df = pd.concat([jobs], ignore_index=True)

    # 3) save
    df.to_csv(DATA_PROCESSED / f"jobs_combined_{scraped_at}.csv", index=False)
    return df


if __name__ == "__main__":
    df = run()
    print(df.head(3))
    print("Rows:", len(df))