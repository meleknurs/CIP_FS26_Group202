from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
import pandas as pd

from src.cleaning import to_schema
from src.sources.jobup_selenium import collect_raw as collect_raw_jobup

DATA_PROCESSED = Path("data/processed")


def run(
    roles: list[str] | None = None,
    limit: int = 10000,
    max_pages_per_role: int = 100,
    headless: bool = True,
    fetch_details: bool = True,
    verbose: bool = False,
) -> pd.DataFrame:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    scraped_at = datetime.now().isoformat(timespec="seconds")
    safe_ts = scraped_at.replace(":", "-")

    raw_jobs = collect_raw_jobup(
        roles=roles,
        limit_total=limit,
        max_pages_per_role=max_pages_per_role,
        headless=headless,
        fetch_details=fetch_details,
        verbose=verbose,
    )

    jobs = to_schema(raw_jobs, scraped_at=scraped_at)

    out_path = DATA_PROCESSED / f"jobs_combined_{safe_ts}.csv"
    jobs.to_csv(out_path, index=False)

    print(f"Saved: {out_path}")
    return jobs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--roles",
        type=str,
        default=None,
        help='Comma-separated roles, e.g. "data scientist,machine learning engineer"',
    )
    parser.add_argument("--limit", type=int, default=10000, help="Max rows to collect")
    parser.add_argument("--max-pages-per-role", type=int, default=100, help="Pagination depth per role query")
    parser.add_argument("--headful", action="store_true", help="Run browser in visible mode (not headless)")
    parser.add_argument("--verbose", action="store_true", help="Print page-level collector progress")
    parser.add_argument("--no-details", action="store_true", help="Skip opening detail pages (description + detail fields)")
    args = parser.parse_args()
    roles = [r.strip() for r in args.roles.split(",") if r.strip()] if args.roles else None

    df = run(
        roles=roles,
        limit=args.limit,
        max_pages_per_role=args.max_pages_per_role,
        headless=not args.headful,
        fetch_details=not args.no_details,
        verbose=args.verbose,
    )
    print(df.head(3))
    print("Rows:", len(df))
