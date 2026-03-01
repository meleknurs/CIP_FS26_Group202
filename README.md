# CIP FS26 – Group 202

Swiss Job Market Trends & Salary Transparency Analysis

## Phase 1: Web Scraping (Current)

Collect job listings from Jobup.ch via Selenium.

### Quick Start

1. **Install dependencies**
   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. **Run the pipeline**
   ```bash
   python3 -m src.pipeline
   ```
   Output: CSV file in `data/processed/jobs_combined_{timestamp}.csv`

   Common options:
   ```bash
   python3 -m src.pipeline --roles "data scientist,machine learning engineer,data engineer,ai engineer" --limit 5000 --max-pages-per-role 200 --verbose
   ```
   - `--roles`: comma-separated role list
   - `--no-details`: skip opening detail pages (faster, no full description)

### Project Structure

```
data/
  raw/, external/, processed/      ← outputs saved here
src/
  pipeline.py                       ← main entry point
  schema.py                         ← shared column schema
  cleaning.py                       ← raw → schema mapping
  sources/
    jobup_selenium.py               ← active collector
notebooks/
  analysis and visualizations

```

### Technology

- **Dynamic pages** (JavaScript load): `Selenium` + `webdriver-manager` (auto-download Chrome driver)
- **Data format**: Pandas DataFrame → CSV

### Notes

- Phase 1 focuses scraping from Jobup and exporting schema-aligned CSV.
- Keep functions simple; add short, clear comments.
