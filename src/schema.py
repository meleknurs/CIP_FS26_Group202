
# Central schema column order used across collectors
SCHEMA_COLUMNS = [
	"source",
	"url",
	"job_id",
	"title",
	"company",
	"location_raw",
	"posted_date",
	"employment_type",
	"salary_raw",
	"description_raw",

	# Enriched / common fields
	"scraped_at",
	"canton",
	"seniority",
	"description_clean",
	"skills",
	"skill_count",
	"salary_available",
]

