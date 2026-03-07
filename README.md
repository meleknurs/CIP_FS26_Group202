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

## Phase 3: Macro-Level Data Integration (Completed)

This phase enriches the primary job posting dataset with macroeconomic labor market indicators from the **Swiss Federal Statistical Office (BFS)** to provide market-wide context.

### Data Source and Scope

Macro-level vacancy data is retrieved via the **BFS API**, focusing on two primary dimensions:
* **Regional Statistics:** BFS Major Regions (e.g., Lake Geneva, Zurich).
* **Economic Divisions:** NOGA Classification (specifically **58-63 ICT**).

### Processing Pipeline

1.  **Ingestion:** Automated retrieval and conversion of raw API responses to pandas DataFrames.
2.  **Cleaning:** Standardization of column names (English), removal of aggregates, and handling of missing values.
3.  **Tidying:** Reshaping data into a long-form format featuring `region`, `industry`, `quarter`, and `vacancies`.
4.  **Temporal Alignment:** Since current job postings (2026Q1) exceed the latest BFS release (2025Q4), a `macro_quarter` proxy was implemented to map postings to the most recent available macro indicators.

### Integration Logic

The datasets are merged using keys derived from the micro-level job data:

| **quarter** | Extracted from job posting timestamps. |
| **region** | Mapped from Canton-level data to BFS Major Regions. |
| **industry** | Assigned to `58-63 ICT` based on technical role classification. |

### Final Dataset Structure

The resulting dataset, `data/processed/jobs_micro_macro_merged_final.csv`, combines:

* **Micro-level Variables:** Job title, company, location, description, extracted skills, and salary transparency.
* **Macro-level Variables:** Regional vacancy levels and ICT-specific industry demand indices.

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

