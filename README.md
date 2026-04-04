# CIP FS26 – Group 202
## Swiss Job Market Trends & Salary Transparency Analysis

---

## Quick Start

1. **Install dependencies**
```bash
   python3 -m pip install -r requirements.txt
```

2. **Run the pipeline**
```bash
   python3 -m src.pipeline
```
   Output: `data/processed/jobs_combined_{timestamp}.csv`

   Common options:
   - `--roles`: comma-separated list of search roles (default: data scientist, data analyst, machine learning engineer, data engineer, ai engineer)
   - `--limit`: max jobs per role
   - `--max-pages-per-role`: pagination cap
   - `--no-details`: skip detail pages (faster)

3. **Run the Streamlit dashboard**
```bash
   streamlit run app.py
```
   Data source: `data/processed/jobs_merged_final.csv`

---

## Project Structure
```
data/
  raw/           # original scraped data
  external/      # BFS macro datasets
  processed/     # cleaned & analysis-ready datasets

src/
  pipeline.py        # main entry point
  schema.py          # shared column schema
  cleaning.py        # raw → schema mapping
  sources/
    jobup_selenium.py  # Jobup.ch scraper

notebooks/
  analysis and visualizations

job_market_dashboard.py             # Streamlit dashboard
```

---

## Team Contributions

### Meleknur – Data Collection
- Scraping job postings from Jobup.ch with Selenium + BeautifulSoup (`src/sources/jobup_selenium.py`)
- Implementing pagination and detail-page extraction
- Exporting scraped outputs and setting up the GitHub repository
- Streamlit dashboard (`app.py`)

### Ellie – Data Cleaning and Integration
- Cleaning and preprocessing with pandas (`notebooks/01_micro_preprocessing.py`)
- Fetching BFS macro vacancy data via API (`notebooks/02_macro_level_cleaning_dataset A/B.py`)
- Merging micro and macro datasets (`notebooks/04_micro_macro_integration.ipynb`)
- Writing the final documentation

### Faranak – Analysis, Visualization, and Documentation
- EDA and research-question analysis (`notebooks/05_eda_rq_analysis.ipynb`)
- Charts (bar charts, heatmaps, distribution plots)
- Writing the final documentation

# Notes

The project focuses on **Python-based data acquisition, preprocessing,
and integration**, as required by the CIP course guidelines.

The pipeline is designed to be **modular and extensible**, allowing easy
expansion to additional roles, platforms, or macro datasets.

The Streamlit dashboard demonstrates the **practical usability of the
processed dataset**.
