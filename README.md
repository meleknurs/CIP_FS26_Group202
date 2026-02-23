# CIP FS26 – Group 202

Swiss Job Market Trends & Salary Transparency Analysis

## Phase 1: Web Scraping (Current)

Collect job listings from multiple Swiss job boards. Each person implements one collector.

### Quick Start

1. **Install dependencies**
   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. **Run the pipeline** (test with existing collectors)
   ```bash
   python3 -m src.pipeline
   ```
   Output: CSV file in `data/processed/jobs_combined_{timestamp}.csv`

3. **Add a new collector** (for ictjobs.py or bfs.py)
   - Copy `src/sources/template.py` → `src/sources/<name>.py`
   - Implement `collect_raw(limit: int, headless: bool, start_url) -> pd.DataFrame`
   - Must return these columns: `source, url, job_id, title, company, location_raw, posted_date, employment_type, salary_raw, description_raw`
   - Test locally: `python3 -m src.sources.<name>`

### Project Structure

```
data/
  raw/, external/, processed/      ← outputs saved here
src/
  pipeline.py                       ← main entry point
  schema.py                         ← shared column schema
  sources/
    datacareer*.py                  ← example collectors (requests + selenium)
    template.py                     ← copy this for new sources
    ictjobs.py, bfs.py              ← implement these
notebooks/
  analysis and visualizations

```

### Technology

- **Static pages**: `requests` + `BeautifulSoup` (fast)
- **Dynamic pages** (JavaScript load): `Selenium` + `webdriver-manager` (auto-download Chrome driver)
- **Data format**: Pandas DataFrame → CSV

### Notes

- Phase 1 focuses only on scraping (collect_raw).
- Data mapping and enrichment (to_schema) will be added later.
- Keep functions simple; add short, clear comments.
