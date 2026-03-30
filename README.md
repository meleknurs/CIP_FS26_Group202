# Swiss Job Market Trends & Salary Transparency Analysis

**CIP_FS26_Group202**

This repository contains the code and documentation for the CIP course
project\
**"Data Collection, Integration and Presentation (FS26)"**.

The project analyzes the Swiss data-related job market using web-scraped
job postings from **Jobup.ch** and macro-level vacancy statistics from
the **Swiss Federal Statistical Office (BFS)**.

The goal is to identify patterns in:

-   skill demand
-   regional job distribution
-   salary transparency in Swiss job advertisements

The project implements a **complete Python data pipeline** including web
scraping, preprocessing, data integration, analysis, and an interactive
**Streamlit dashboard**.

------------------------------------------------------------------------

# Research Questions

1.  Which skills and technologies are most frequently requested in Swiss
    data-related job postings?

2.  How do job requirements differ across regions, industries, roles,
    and seniority levels?

3.  How prevalent is salary information in job postings, and does salary
    transparency vary across roles or regions?

------------------------------------------------------------------------

# Quick Start

## Install dependencies

``` bash
python3 -m pip install -r requirements.txt
```

## Run the data pipeline

``` bash
python3 -m src.pipeline
```

Output dataset:

    data/processed/jobs_combined_{timestamp}.csv

------------------------------------------------------------------------

# Streamlit Dashboard

An interactive dashboard was implemented using **Streamlit** to explore
the project results.

Run the dashboard locally with:

``` bash
streamlit run job_market_dashboard.py
```

The dashboard reads the final dataset:

    data/processed/jobs_merged_final.csv

The dashboard allows users to explore:

-   skill demand across roles
-   regional distribution of job postings
-   salary transparency statistics
-   overall dataset summary

------------------------------------------------------------------------

# Pipeline Overview

The project consists of three main phases.

------------------------------------------------------------------------

# Phase 1 --- Web Scraping

Job listings are collected from **Jobup.ch** using **Selenium**.

Implementation:

    src/sources/jobup_selenium.py

Features:

-   pagination through search result pages
-   dynamic page interaction
-   detail-page extraction
-   headless browser execution
-   polite request delays

Extracted variables include:

-   job title\
-   company name\
-   location\
-   posted date\
-   contract type\
-   workload percentage\
-   job description

Output dataset:

    data/processed/jobs_combined_{timestamp}.csv

------------------------------------------------------------------------

# Phase 2 --- Data Cleaning & Preprocessing

The raw dataset is transformed into an **analysis-ready micro dataset**.

Input:

    data/processed/jobs_combined_{timestamp}.csv

Output:

    data/processed/jobs_micro_cleaned_final.csv

Key preprocessing steps:

-   structural validation (schema, duplicates, missing values)
-   text cleaning
-   city extraction and canton mapping
-   salary transparency reconstruction
-   seniority classification (intern / junior / mid / senior / lead)
-   skill extraction using regex dictionaries
-   workload percentage extraction
-   datetime conversion

The dataset becomes ready for:

-   skill demand analysis
-   regional comparison
-   salary transparency analysis
-   macro-data integration

------------------------------------------------------------------------

# Phase 3 --- Macro-Level Data Integration

The micro dataset is enriched with **Swiss Federal Statistical Office
(BFS)** vacancy statistics.

Data sources:

-   BFS PXWeb API
-   regional vacancy statistics
-   industry vacancy statistics (NOGA classification)

Processing steps:

-   API ingestion into pandas
-   column standardization
-   removal of aggregates
-   long-format restructuring
-   temporal alignment between datasets

Because job postings originate from **2026Q1** while BFS data is
available until **2025Q4**, a proxy variable `macro_quarter` was
introduced.

Final dataset:

    data/processed/jobs_merged_final.csv

This dataset combines:

Micro-level variables

-   job title
-   company
-   location
-   extracted skills
-   salary transparency
-   seniority level

Macro-level variables

-   regional vacancy indicators
-   industry vacancy indicators

------------------------------------------------------------------------

# Dataset Summary

  Metric                   Value
  ------------------------ -------
  Total job postings       743
  Unique companies         274
  Skills extracted         61.9%
  Salary transparency      1.2%
  Unclassified seniority   53%

------------------------------------------------------------------------

# Project Structure

    data/
      raw/            # original scraped data
      external/       # external datasets (BFS)
      processed/      # cleaned datasets used for analysis

    src/
      pipeline.py        # main pipeline entry point
      schema.py          # shared column schema
      cleaning.py        # preprocessing functions
      sources/
        jobup_selenium.py  # Selenium scraper

    notebooks/
      04_micro_macro_integration.ipynb
      05_eda_rq_analysis.ipynb

    job_market_dashboard.py   # Streamlit dashboard

    requirements.txt
    README.md

------------------------------------------------------------------------

# Technologies Used

Web scraping\
- Selenium\
- BeautifulSoup

Data processing\
- pandas\
- numpy

Visualization\
- matplotlib\
- seaborn

Dashboard\
- Streamlit

Data integration\
- BFS PXWeb API

Output format\
- CSV

------------------------------------------------------------------------

# Team Contributions

### Meleknur --- Data Collection & Dashboard

-   Implemented Selenium-based web scraper for Jobup.ch
    (`src/sources/jobup_selenium.py`)
-   Implemented pagination and detail-page extraction
-   Exported scraped outputs to `data/processed/`
-   Implemented the Streamlit dashboard (`job_market_dashboard.py`)
-   Set up the GitHub repository

------------------------------------------------------------------------

### Ellie --- Data Cleaning & Integration

-   Data preprocessing with pandas
-   Handling missing values and datatype checks
-   Fetching BFS macro data via API
-   Integrating micro and macro datasets
    (`notebooks/04_micro_macro_integration.ipynb`)
-   Contributing to final documentation

------------------------------------------------------------------------

### Faranak --- Analysis & Visualization

-   Exploratory data analysis (`notebooks/05_eda_rq_analysis.ipynb`)
-   Creating charts and figures for the research questions
-   Supporting the final documentation

------------------------------------------------------------------------

# Notes

The project focuses on **Python-based data acquisition, preprocessing,
and integration**, as required by the CIP course guidelines.

The pipeline is designed to be **modular and extensible**, allowing easy
expansion to additional roles, platforms, or macro datasets.

The Streamlit dashboard demonstrates the **practical usability of the
processed dataset**.
