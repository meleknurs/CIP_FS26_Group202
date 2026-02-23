# Contributing — collectors

Short guide for adding a new web collector (phase 1: scraping only).

1. Collector API
- Create `src/sources/<name>.py` (e.g. `ictjobs.py`, `bfs.py`).
- Implement `collect_raw(limit: int = 30, headless: bool = False, start_url: Optional[str]=None) -> pd.DataFrame`.
- Returned DataFrame must include these base columns:
  - `source, url, job_id, title, company, location_raw, posted_date, employment_type, salary_raw, description_raw`

2. Tips
- Use `requests + BeautifulSoup` for static pages.
- Use `selenium` (with `webdriver-manager`) when pages need JS or clicking.
- Keep comments short and functions typed.

3. Local testing
- Run the module directly for quick checks:
  ```bash
  python3 -m src.sources.<name>
  ```
- Or run the pipeline after switching the collector import in `src/pipeline.py`.

4. Requirements
- If your collector uses Selenium, ensure `webdriver-manager` is added to `requirements.txt`.
- Document extra system requirements (e.g. Chrome) at top of the collector file.

5. Pull request
- Add your collector file, a short README entry (one paragraph), and a sample output CSV (optional).
- Keep PRs focused: scraping only in phase 1. Data mapping and downstream steps will follow.

Thanks — keep functions small and tests simple.
