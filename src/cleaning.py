from __future__ import annotations

import re

import pandas as pd

from src.schema import SCHEMA_COLUMNS


def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def to_schema(df_raw: pd.DataFrame, scraped_at: str) -> pd.DataFrame:
    """Map raw dataframe to the common schema."""
    df = df_raw.copy()

    base_cols = [
        "source",
        "url",
        "job_id",
        "search_term",
        "title",
        "company",
        "location_raw",
        "posted_date",
        "employment_type",
        "workload_raw",
        "salary_raw",
        "description_raw",
    ]
    for col in base_cols:
        if col not in df.columns:
            df[col] = ""

    df["scraped_at"] = scraped_at
    df["canton"] = ""
    df["seniority"] = ""
    df["description_clean"] = df["description_raw"].fillna("").map(_clean_text)
    df["skills"] = ""
    df["skill_count"] = 0

    df["salary_raw"] = df["salary_raw"].fillna("").astype(str)
    df["salary_available"] = (df["salary_raw"].str.len() > 0).astype(int)

    for c in SCHEMA_COLUMNS:
        if c not in df.columns:
            df[c] = ""

    return df[SCHEMA_COLUMNS]
