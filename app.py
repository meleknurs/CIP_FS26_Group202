from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# =========================================================
# Config
# =========================================================
DATA_PATH = Path("data/processed/jobs_merged_final.csv")

BG = "#F8F9FB"
BLUE = "#2C6E9E"
TEAL = "#2CA4A0"
ORANGE = "#E07B39"
GREEN = "#5BAD72"
PURPLE = "#7B5EA7"
ROSE = "#C94F6D"
OLIVE = "#A0853C"
GRAY = "#CCCCCC"
TEXT = "#333333"

COLORS = [BLUE, TEAL, ORANGE, GREEN, PURPLE, ROSE, OLIVE]

sns.set(style="whitegrid")


# =========================================================
# Utility helpers
# =========================================================
def normalize_skills(skills: list[object]) -> list[str]:
    skill_map = {
        "py": "python",
        "python3": "python",
        "ml": "machine learning",
        "machine-learning": "machine learning",
        "cicd": "ci/cd",
        "ci cd": "ci/cd",
        "amazon web services": "aws",
        "k8s": "kubernetes",
        "ms excel": "excel",
    }

    cleaned = []
    for s in skills:
        skill = str(s).strip().lower()
        if not skill:
            continue
        skill = skill_map.get(skill, skill)
        cleaned.append(skill)

    return list(dict.fromkeys(cleaned))


def parse_skills(x: object) -> list[str]:
    if pd.isna(x):
        return []
    if isinstance(x, list):
        return normalize_skills(x)

    raw = str(x).strip()
    if not raw:
        return []

    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return normalize_skills(parsed)
    except Exception:
        pass

    return normalize_skills([s.strip() for s in raw.split(",") if s.strip()])


def style_ax(ax: plt.Axes, remove_left: bool = False) -> None:
    ax.set_facecolor(BG)
    ax.spines[["top", "right"]].set_visible(False)
    if remove_left:
        ax.spines["left"].set_visible(False)
        ax.tick_params(left=False)


def workload_cat(row: pd.Series) -> str:
    wmin = row.get("workload_min", np.nan)
    wmax = row.get("workload_max", np.nan)

    if pd.isna(wmin) and pd.isna(wmax):
        return "Unknown"
    if pd.notna(wmax) and wmax <= 60:
        return "Part-time (<=60%)"
    if pd.notna(wmin) and wmin >= 90:
        return "Full-time (>=90%)"
    return "Flexible (61-89%)"


# =========================================================
# Data loading
# =========================================================
@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH).copy()

    if "skills" in df.columns:
        df["skills_list"] = df["skills"].apply(parse_skills)
    else:
        df["skills_list"] = [[] for _ in range(len(df))]

    if "skill_count" not in df.columns:
        df["skill_count"] = df["skills_list"].apply(len)

    if "salary_available" not in df.columns:
        df["salary_available"] = 0

    if "job_id" not in df.columns:
        if "b_id" in df.columns:
            df["job_id"] = df["b_id"]
        else:
            df["job_id"] = [f"job_{i}" for i in range(len(df))]

    expected_cols = [
        "title",
        "company",
        "role",
        "region",
        "canton",
        "industry",
        "seniority",
        "city",
        "workload_min",
        "workload_max",
        "macro_vacancies_region",
        "posted_date",
        "scraped_at",
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = np.nan

    df["salary_available"] = pd.to_numeric(
        df["salary_available"], errors="coerce"
    ).fillna(0).astype(float)
    df["skill_count"] = pd.to_numeric(df["skill_count"], errors="coerce")
    df["workload_min"] = pd.to_numeric(df["workload_min"], errors="coerce")
    df["workload_max"] = pd.to_numeric(df["workload_max"], errors="coerce")

    return df


# =========================================================
# Session state
# =========================================================
def init_session_state() -> None:
    defaults = {
        "f_roles": [],
        "f_regions": [],
        "f_cantons": [],
        "f_industries": [],
        "f_seniorities": [],
        "q_search": "",
        "min_group_n": 5,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_filters() -> None:
    st.session_state.f_roles = []
    st.session_state.f_regions = []
    st.session_state.f_cantons = []
    st.session_state.f_industries = []
    st.session_state.f_seniorities = []
    st.session_state.q_search = ""
    st.session_state.min_group_n = 5


# =========================================================
# Filters
# =========================================================
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    if st.sidebar.button("Reset filters", use_container_width=True):
        reset_filters()
        st.rerun()

    roles = sorted(df["role"].dropna().unique().tolist())
    st.sidebar.multiselect("Role", roles, key="f_roles")

    df_step = df.copy()
    if st.session_state.f_roles:
        df_step = df_step[df_step["role"].isin(st.session_state.f_roles)]

    regions = sorted(df_step["region"].dropna().unique().tolist())
    st.sidebar.multiselect("Region", regions, key="f_regions")
    if st.session_state.f_regions:
        df_step = df_step[df_step["region"].isin(st.session_state.f_regions)]

    cantons = sorted(df_step["canton"].dropna().unique().tolist())
    st.sidebar.multiselect("Canton", cantons, key="f_cantons")
    if st.session_state.f_cantons:
        df_step = df_step[df_step["canton"].isin(st.session_state.f_cantons)]

    industries = sorted(df_step["industry"].dropna().unique().tolist())
    st.sidebar.multiselect("Industry", industries, key="f_industries")
    if st.session_state.f_industries:
        df_step = df_step[df_step["industry"].isin(st.session_state.f_industries)]

    seniorities = sorted(df_step["seniority"].dropna().unique().tolist())
    st.sidebar.multiselect("Seniority", seniorities, key="f_seniorities")

    st.sidebar.text_input("Search title or company", key="q_search")
    st.sidebar.slider("Minimum sample size for grouped charts", 1, 30, key="min_group_n")

    filtered = df.copy()

    if st.session_state.f_roles:
        filtered = filtered[filtered["role"].isin(st.session_state.f_roles)]
    if st.session_state.f_regions:
        filtered = filtered[filtered["region"].isin(st.session_state.f_regions)]
    if st.session_state.f_cantons:
        filtered = filtered[filtered["canton"].isin(st.session_state.f_cantons)]
    if st.session_state.f_industries:
        filtered = filtered[filtered["industry"].isin(st.session_state.f_industries)]
    if st.session_state.f_seniorities:
        filtered = filtered[filtered["seniority"].isin(st.session_state.f_seniorities)]

    query = st.session_state.q_search.strip()
    if query:
        title_match = filtered["title"].astype(str).str.contains(query, case=False, na=False)
        company_match = filtered["company"].astype(str).str.contains(query, case=False, na=False)
        filtered = filtered[title_match | company_match]

    active_filters = sum(
        bool(x)
        for x in [
            st.session_state.f_roles,
            st.session_state.f_regions,
            st.session_state.f_cantons,
            st.session_state.f_industries,
            st.session_state.f_seniorities,
            st.session_state.q_search.strip(),
        ]
    )
    st.sidebar.caption(f"Active filters: {active_filters}")

    return filtered


# =========================================================
# Metrics and summaries
# =========================================================
def metric_row(df: pd.DataFrame) -> None:
    salary_rate = df["salary_available"].mean() * 100 if len(df) else 0
    skills_coverage = (df["skill_count"].fillna(0) > 0).mean() * 100 if len(df) else 0
    missing_seniority = df["seniority"].isna().mean() * 100 if len(df) else 0
    missing_canton = df["canton"].isna().mean() * 100 if len(df) else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Postings", f"{len(df):,}")
    c2.metric("Salary transparency", f"{salary_rate:.2f}%")
    c3.metric("Median skill count", f"{df['skill_count'].median():.1f}" if len(df) else "0.0")
    c4.metric("Unique companies", f"{df['company'].nunique():,}")
    c5.metric("Skill coverage", f"{skills_coverage:.1f}%")
    c6.metric("Missing canton", f"{missing_canton:.1f}%")

    c7, c8 = st.columns(2)
    c7.metric("Missing seniority", f"{missing_seniority:.1f}%")
    c8.metric("Postings with salary", f"{int(df['salary_available'].sum()):,}")


def build_top_skills(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    all_skills = [skill for skills in df["skills_list"] for skill in skills]
    return pd.DataFrame(Counter(all_skills).most_common(top_n), columns=["skill", "count"])


# =========================================================
# Context sections
# =========================================================
def render_project_context_text() -> None:
    st.subheader("Project Context and Pipeline")
    st.markdown(
        """
### CIP FS26 – Group 202  
**Swiss Job Market Trends & Salary Transparency Analysis**

This project examines structural characteristics of the Swiss job market, with a focus on salary transparency in online job advertisements. The analytical goal is to combine scraped posting data with official labour market indicators through a Python-based workflow.

**Pipeline**
1. **Web scraping:** collection of Swiss data and AI job postings  
2. **Micro-level preprocessing:** cleaning, standardization, salary reconstruction, skill extraction, seniority and workload derivation  
3. **Macro-level integration:** enrichment with BFS vacancy indicators for regional labour-market context  

**Analytical goal**
- identify demanded skills and technologies
- compare job requirements across roles, locations, industries, and seniority levels
- evaluate salary transparency across roles and regions
"""
    )


def render_data_quality_text(df: pd.DataFrame) -> None:
    missing_canton = df["canton"].isna().mean() * 100 if len(df) else 0
    missing_region = df["region"].isna().mean() * 100 if len(df) else 0
    missing_industry = df["industry"].isna().mean() * 100 if len(df) else 0
    missing_seniority = df["seniority"].isna().mean() * 100 if len(df) else 0
    missing_workload = df["workload_min"].isna().mean() * 100 if "workload_min" in df.columns else 100.0
    skills_zero = (df["skill_count"].fillna(0) == 0).mean() * 100 if len(df) else 0

    st.subheader("Data Quality and Methodology")
    st.markdown(
        f"""
- **Unit of analysis:** one row per job posting
- **Skills:** parsed from the `skills` field and lightly normalized
- **Skill heatmaps:** share of postings in which a skill appears
- **Salary transparency:** based on explicit salary information in the posting
- **Macro context:** BFS values are contextual and not directly equivalent to scraped posting counts

**Missingness overview**
- Canton missing: **{missing_canton:.1f}%**
- Region missing: **{missing_region:.1f}%**
- Industry missing: **{missing_industry:.1f}%**
- Seniority missing: **{missing_seniority:.1f}%**
- Workload missing: **{missing_workload:.1f}%**
- Zero extracted skills: **{skills_zero:.1f}%**

**Interpretation notes**
- Small groups can produce unstable percentages.
- Salary disclosure is sparse and should be interpreted cautiously.
- Macro comparisons provide broad contextual validation rather than direct equivalence.
"""
    )


# =========================================================
# Charts
# =========================================================
def plot_role_distribution(df: pd.DataFrame) -> None:
    role_counts = df["role"].dropna().value_counts()
    if role_counts.empty:
        st.info("No role data after filters.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=BG)
    bars = ax.barh(
        role_counts.index[::-1],
        role_counts.values[::-1],
        color=COLORS[: len(role_counts)][::-1],
        edgecolor="none",
        height=0.65,
    )
    for bar in bars:
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2, f"{int(bar.get_width())}", va="center", fontsize=9, color=TEXT)
    ax.set_xlabel("Number of postings")
    ax.set_title("Job Role Distribution")
    style_ax(ax, remove_left=True)
    st.pyplot(fig)


def plot_canton_distribution(df: pd.DataFrame) -> None:
    loc_counts = df["canton"].dropna().value_counts()
    if loc_counts.empty:
        st.info("No canton data after filters.")
        return

    denom = (loc_counts.values.max() - loc_counts.values.min()) or 1
    norm_vals = (loc_counts.values - loc_counts.values.min()) / denom
    cmap = plt.cm.Blues
    cols = [cmap(0.3 + 0.65 * v) for v in norm_vals]

    fig, ax = plt.subplots(figsize=(8, 6), facecolor=BG)
    bars = ax.barh(loc_counts.index[::-1], loc_counts.values[::-1], color=cols[::-1], edgecolor="none", height=0.7)
    for bar in bars:
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2, f"{int(bar.get_width())}", va="center", fontsize=8, color=TEXT)
    ax.set_xlabel("Postings")
    ax.set_title("Job Postings by Canton")
    style_ax(ax, remove_left=True)
    st.pyplot(fig)


def plot_top_skills(df: pd.DataFrame) -> None:
    top15 = build_top_skills(df, 15)
    if top15.empty:
        st.info("No skill data after filters.")
        return

    cmap = plt.colormaps["YlGnBu"]
    cols = [cmap(0.35 + 0.6 * (i / max(len(top15) - 1, 1))) for i in range(len(top15))]

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=BG)
    bars = ax.barh(top15["skill"][::-1], top15["count"][::-1], color=cols[::-1], edgecolor="none", height=0.65)
    for bar in bars:
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2, f"{int(bar.get_width())}", va="center", fontsize=8, color=TEXT)
    ax.set_xlabel("Postings mentioning skill")
    ax.set_title("Top 15 Most Requested Skills")
    style_ax(ax, remove_left=True)
    st.pyplot(fig)


def plot_skill_count_by_role(df: pd.DataFrame) -> None:
    plot_df = df.dropna(subset=["role", "skill_count"]).copy()
    if plot_df.empty:
        st.info("No skill count data after filters.")
        return

    role_order = plot_df.groupby("role")["skill_count"].median().sort_values(ascending=False).index
    data_box = [plot_df.loc[plot_df["role"] == role, "skill_count"].values for role in role_order]

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=BG)
    bp = ax.boxplot(
        data_box,
        vert=False,
        patch_artist=True,
        medianprops=dict(color="white", linewidth=2),
        whiskerprops=dict(color="#888"),
        capprops=dict(color="#888"),
        flierprops=dict(marker="o", color="#888", alpha=0.4, markersize=4),
    )
    for patch, color in zip(bp["boxes"], COLORS * 5):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)

    ax.set_yticks(range(1, len(role_order) + 1))
    ax.set_yticklabels(role_order)
    ax.set_xlabel("Skill count per posting")
    ax.set_title("Skill Count Distribution by Role")
    style_ax(ax)
    st.pyplot(fig)


def compute_skill_presence_matrix(
    df: pd.DataFrame,
    group_col: str,
    top_n: int = 10,
    min_group_n: int = 5,
) -> pd.DataFrame:
    top10 = [s for s, _ in Counter([s for sl in df["skills_list"] for s in sl]).most_common(top_n)]
    if not top10:
        return pd.DataFrame()

    valid = df[group_col].dropna().astype(str).str.strip()
    groups = valid[valid != ""].value_counts()
    groups = groups[groups >= min_group_n].index.tolist()
    if not groups:
        return pd.DataFrame()

    rows = []
    idx = []
    for group in groups:
        sub = df[df[group_col] == group].copy()
        total = len(sub)
        if total == 0:
            continue

        row = {}
        for skill in top10:
            present = sub["skills_list"].apply(lambda lst: skill in set(lst)).sum()
            row[skill] = present / total * 100
        rows.append(row)
        idx.append(group)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows, index=idx)[top10]


def heatmap_top10_by_group(
    df: pd.DataFrame,
    group_col: str,
    title: str,
    cmap: str,
    min_group_n: int = 5,
) -> None:
    hm = compute_skill_presence_matrix(df, group_col, top_n=10, min_group_n=min_group_n)
    if hm.empty:
        st.info(f"No sufficient {group_col} data after filters (min n={min_group_n}).")
        return

    fig, ax = plt.subplots(figsize=(10, max(3.5, 0.45 * len(hm))), facecolor=BG)
    sns.heatmap(
        hm,
        ax=ax,
        cmap=cmap,
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        linecolor="#eee",
        cbar_kws={"label": "% of postings"},
    )
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.xticks(rotation=30, ha="right")
    plt.yticks(rotation=0)
    st.pyplot(fig)


def plot_workload_by_role(df: pd.DataFrame, min_group_n: int = 5) -> None:
    tmp = df.copy()
    tmp["workload_cat"] = tmp.apply(workload_cat, axis=1)

    counts = tmp["role"].value_counts()
    keep_roles = counts[counts >= min_group_n].index
    tmp = tmp[tmp["role"].isin(keep_roles)]

    if tmp.empty:
        st.info(f"No sufficient workload-by-role data after filters (min n={min_group_n}).")
        return

    wl = tmp.groupby(["role", "workload_cat"]).size().unstack(fill_value=0)
    wl_pct = wl.div(wl.sum(axis=1), axis=0) * 100

    colors = {
        "Full-time (>=90%)": BLUE,
        "Flexible (61-89%)": TEAL,
        "Part-time (<=60%)": ORANGE,
        "Unknown": GRAY,
    }

    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=BG)
    bottom = np.zeros(len(wl_pct))
    for cat in ["Full-time (>=90%)", "Flexible (61-89%)", "Part-time (<=60%)", "Unknown"]:
        if cat in wl_pct.columns:
            vals = wl_pct[cat].values
            ax.bar(
                wl_pct.index,
                vals,
                bottom=bottom,
                label=cat,
                color=colors[cat],
                edgecolor="white",
                linewidth=0.5,
            )
            bottom += vals

    ax.set_ylabel("% of postings")
    ax.set_title("Workload Distribution by Role")
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)
    plt.xticks(rotation=15, ha="right")
    style_ax(ax)
    st.pyplot(fig)


def plot_region_vs_macro(df: pd.DataFrame, min_group_n: int = 1) -> None:
    rc = (
        df[df["region"].notna()]
        .groupby("region")
        .agg(job_postings=("job_id", "count"), macro_vacancies=("macro_vacancies_region", "mean"))
        .reset_index()
    )

    rc = rc[rc["job_postings"] >= min_group_n].sort_values("job_postings", ascending=True)

    if rc.empty:
        st.info("No region data after filters.")
        return

    fig, ax1 = plt.subplots(figsize=(9, 5), facecolor=BG)
    ax2 = ax1.twinx()

    ax1.barh(rc["region"], rc["job_postings"], color=BLUE, alpha=0.85, label="Job Postings", height=0.5)
    ax2.plot(rc["macro_vacancies"], rc["region"], "o-", color=ORANGE, linewidth=2, markersize=7, label="BFS Vacancies")

    ax1.set_xlabel("Job Postings", color=BLUE)
    ax2.set_xlabel("BFS Macro Vacancies", color=ORANGE)
    ax1.set_title("Scraped Postings vs BFS Vacancies by Region")
    ax1.set_facecolor(BG)
    ax2.set_facecolor(BG)
    ax1.spines[["top"]].set_visible(False)
    ax2.spines[["top"]].set_visible(False)
    st.pyplot(fig)


def plot_salary_transparency(df: pd.DataFrame, min_group_n: int = 10) -> None:
    salary_by_canton = (
        df[df["canton"].notna()]
        .groupby("canton")
        .agg(postings=("salary_available", "size"), salary_rate=("salary_available", "mean"))
        .reset_index()
    )
    salary_by_canton = salary_by_canton[salary_by_canton["postings"] >= min_group_n]
    salary_by_canton = salary_by_canton[salary_by_canton["salary_rate"] > 0].sort_values("salary_rate", ascending=False)

    salary_by_role = (
        df[df["role"].notna()]
        .groupby("role")
        .agg(postings=("salary_available", "size"), salary_rate=("salary_available", "mean"))
        .reset_index()
    )
    salary_by_role = salary_by_role[salary_by_role["postings"] >= min_group_n]
    salary_by_role = salary_by_role[salary_by_role["salary_rate"] > 0].sort_values("salary_rate", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots(figsize=(5.5, 3.8), facecolor=BG)
        if salary_by_canton.empty:
            st.info(f"No salary-transparency signal by canton with min n={min_group_n}.")
        else:
            bars = ax1.barh(
                salary_by_canton["canton"][::-1],
                salary_by_canton["salary_rate"][::-1] * 100,
                color=PURPLE,
                edgecolor="none",
                height=0.55,
            )
            for bar, (_, row) in zip(bars, salary_by_canton.iloc[::-1].iterrows()):
                ax1.text(
                    bar.get_width() + 0.05,
                    bar.get_y() + bar.get_height() / 2,
                    f"{row['salary_rate'] * 100:.1f}% (n={int(row['postings'])})",
                    va="center",
                    fontsize=8,
                    color=TEXT,
                )
            ax1.set_xlabel("% with salary")
            ax1.set_title("Salary Transparency by Canton")
            style_ax(ax1, remove_left=True)
            st.pyplot(fig1)

    with col2:
        fig2, ax2 = plt.subplots(figsize=(5.5, 3.8), facecolor=BG)
        if salary_by_role.empty:
            st.info(f"No salary-transparency signal by role with min n={min_group_n}.")
        else:
            bars = ax2.barh(
                salary_by_role["role"][::-1],
                salary_by_role["salary_rate"][::-1] * 100,
                color=GREEN,
                edgecolor="none",
                height=0.5,
            )
            for bar, (_, row) in zip(bars, salary_by_role.iloc[::-1].iterrows()):
                ax2.text(
                    bar.get_width() + 0.05,
                    bar.get_y() + bar.get_height() / 2,
                    f"{row['salary_rate'] * 100:.1f}% (n={int(row['postings'])})",
                    va="center",
                    fontsize=8,
                    color=TEXT,
                )
            ax2.set_xlabel("% with salary")
            ax2.set_title("Salary Transparency by Role")
            style_ax(ax2, remove_left=True)
            st.pyplot(fig2)


def plot_top_companies(df: pd.DataFrame, top_n: int = 10) -> None:
    company_counts = df["company"].dropna().astype(str)
    company_counts = company_counts[company_counts.str.strip() != ""].value_counts().head(top_n)

    if company_counts.empty:
        st.info("No company data after filters.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=BG)
    bars = ax.barh(company_counts.index[::-1], company_counts.values[::-1], color=ROSE, edgecolor="none", height=0.6)
    for bar in bars:
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2, f"{int(bar.get_width())}", va="center", fontsize=8, color=TEXT)
    ax.set_xlabel("Postings")
    ax.set_title(f"Top {top_n} Companies by Posting Count")
    style_ax(ax, remove_left=True)
    st.pyplot(fig)


def render_preview(df: pd.DataFrame) -> None:
    st.subheader("Overview")
    preview_cols = [
        "job_id",
        "title",
        "company",
        "role",
        "seniority",
        "canton",
        "region",
        "city",
        "industry",
        "skill_count",
        "salary_available",
    ]
    preview_cols = [col for col in preview_cols if col in df.columns]

    preview = df[preview_cols].copy()
    preview["salary_available"] = preview["salary_available"].map({1.0: "Yes", 0.0: "No"}).fillna("No")

    st.caption(f"Showing up to 200 rows out of {len(preview):,} filtered postings.")
    st.dataframe(preview.head(200), use_container_width=True, hide_index=True)

    csv_bytes = preview.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_jobs.csv",
        mime="text/csv",
    )


# =========================================================
# Main
# =========================================================
def main() -> None:
    st.set_page_config(page_title="Swiss Job Market Dashboard", layout="wide")
    init_session_state()

    st.title("Swiss Job Market Dashboard")
    st.caption(
        "Interactive dashboard for Swiss data and AI job postings with micro-level job signals and BFS macro labour-market context."
    )

    try:
        df = load_data()
    except Exception as exc:
        st.error(str(exc))
        return

    filtered = apply_filters(df)

    if filtered.empty:
        st.warning("No rows left after filters. Please relax your filters.")
        return

    metric_row(filtered)

    # 1) Project context and pipeline
    render_project_context_text()
    p1, p2 = st.columns(2)
    with p1:
        plot_role_distribution(filtered)
    with p2:
        plot_canton_distribution(filtered)

    p3, p4 = st.columns(2)
    with p3:
        plot_top_companies(filtered, top_n=10)
    with p4:
        plot_region_vs_macro(filtered, min_group_n=1)

    st.divider()

    # 2) Data quality and methodology
    render_data_quality_text(filtered)
    d1, d2 = st.columns(2)
    with d1:
        plot_skill_count_by_role(filtered)
    with d2:
        plot_workload_by_role(filtered, min_group_n=st.session_state.min_group_n)

    st.divider()

    # 3) Research questions
    st.subheader("Research Questions")

    # RQ1
    st.markdown(
        """
### RQ1. Which skills and technologies are most frequently requested in Swiss job postings?
This section focuses on overall skill demand and on how technical competencies cluster across roles and industries.
"""
    )
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        plot_top_skills(filtered)
    with r1c2:
        heatmap_top10_by_group(
            filtered,
            "role",
            "Top 10 Skills by Role (% of postings)",
            "PuBuGn",
            min_group_n=st.session_state.min_group_n,
        )

    r1c3, r1c4 = st.columns(2)
    with r1c3:
        heatmap_top10_by_group(
            filtered,
            "industry",
            "Top 10 Skills by Industry (% of postings)",
            "YlOrRd",
            min_group_n=st.session_state.min_group_n,
        )
    with r1c4:
        plot_skill_count_by_role(filtered)

    st.divider()

    # RQ2
    st.markdown(
        """
### RQ2. How do job requirements differ across locations, industries, roles, and seniority levels?
This section compares geographic concentration, role structure, seniority profiles, and workload patterns.
"""
    )
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        plot_canton_distribution(filtered)
    with r2c2:
        plot_role_distribution(filtered)

    r2c3, r2c4 = st.columns(2)
    with r2c3:
        heatmap_top10_by_group(
            filtered,
            "seniority",
            "Top 10 Skills by Seniority (% of postings)",
            "Blues",
            min_group_n=st.session_state.min_group_n,
        )
    with r2c4:
        plot_workload_by_role(filtered, min_group_n=st.session_state.min_group_n)

    st.divider()

    # RQ3
    st.markdown(
        """
### RQ3. How prevalent is salary information, and does salary transparency vary by region or role?
This section treats salary disclosure as an analytical dimension in its own right.
"""
    )
    plot_salary_transparency(filtered, min_group_n=max(10, st.session_state.min_group_n))

    st.divider()

    # Overview en altta
    render_preview(filtered)


if __name__ == "__main__":
    main()