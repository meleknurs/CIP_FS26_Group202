# CIP FS26 – Group 202  
## Swiss Job Market Trends & Salary Transparency Analysis

---

## Phase 1: Web Scraping (Completed)

Collect job listings from **Jobup.ch** using Selenium and export a schema-aligned dataset.

### Quick Start

1. **Install dependencies**
   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. **Run the pipeline**
   ```bash
   python3 -m src.pipeline
   ```

   **Output:**  
   `data/processed/jobs_combined_{timestamp}.csv`

### Common Options

```bash
python3 -m src.pipeline \
  --roles "data scientist,data analyst,machine learning engineer,data engineer,ai engineer" \
  --limit 5000 \
  --max-pages-per-role 200 \
  --verbose
```

- `--roles`: comma-separated list of search roles  
- `--limit`: maximum number of jobs per role  
- `--max-pages-per-role`: pagination cap  
- `--no-details`: skip opening detail pages (faster, no full description)  

### Default Roles

- `data scientist`
- `data analyst`
- `machine learning engineer`
- `data engineer`
- `ai engineer`

---

## Phase 2: Micro-Level Data Preprocessing (Completed)

Transforms the raw scraped dataset into an analysis-ready micro dataset.

### Input
`data/processed/jobs_combined_{timestamp}.csv`

### Output
`data/processed/jobs_micro_cleaned_final.csv`

### Key Preprocessing Steps

- Structural validation (schema check, duplicates, missing values)
- Text cleaning (`description_clean`, `title_clean`)
- City extraction + canton mapping (`city_clean`, `canton`)
- Salary transparency reconstruction (`salary_available`)
- Seniority classification (`intern`, `junior`, `mid`, `senior`, `lead`)
- Skill extraction + `skill_count` (regex-based, conservative matching)
- Workload percentage extraction (`workload_min`)
- Datetime conversion (`posted_date`, `scraped_at`)

The cleaned dataset is now ready for:
- Regional comparison
- Skill demand analysis
- Salary transparency evaluation
- Integration with BFS macro-level vacancy data

---

## Phase 3: Macro-Level Data Integration

To enrich the job posting dataset with macroeconomic labour market indicators, we integrated vacancy data from the Swiss Federal Statistical Office (BFS).

### Data Source

The macro-level vacancy data was obtained via the BFS API and includes:

- Regional vacancy statistics (BFS major regions)
- Vacancy statistics by economic division (NOGA classification)

These datasets provide quarterly indicators of labour demand across Switzerland.

### Processing Steps

1. Data was fetched from the BFS API.
2. Raw API responses were converted into structured pandas DataFrames.
3. Column names were standardized and translated to English.
4. Aggregates and missing values were removed.
5. The datasets were reshaped into tidy format with:

- `region`
- `industry`
- `quarter`
- `vacancies`

The cleaned job posting dataset was merged with the macro-level BFS vacancy indicators to create a combined analysis dataset.

### Merge Keys

The integration required constructing several variables from the micro dataset:

- `quarter` derived from job posting dates
- `region` derived from canton information using BFS major region mapping
- `industry` assigned to the ICT sector (`58-63 ICT`) based on the technical nature of the job roles

### Time Alignment

The job postings dataset contains mostly observations from **2026Q1**, while the BFS vacancy data is available only up to **2025Q4**.

To align the datasets, a proxy variable `macro_quarter` was created:

---

## Project Structure

```
data/
  raw/           # original scraped data
  external/      # external macro datasets (e.g., BFS)
  processed/     # cleaned & analysis-ready datasets

src/
  pipeline.py        # main entry point
  schema.py          # shared column schema
  cleaning.py        # raw → schema mapping
  sources/
    jobup_selenium.py  # active collector

notebooks/
  analysis and visualizations
```

---

## Technology

- **Web scraping:** Selenium + webdriver-manager  
- **Data handling:** Pandas  
- **Output format:** CSV  

---

## Notes

- Phase 1 focuses scraping from Jobup and exporting schema-aligned CSV.
- Keep functions simple; add short, clear comments.
- Phase 2 focuses on transparent, rule-based preprocessing.
- The project follows a modular pipeline design for easy extension (e.g., BFS API integration in Phase 3).

