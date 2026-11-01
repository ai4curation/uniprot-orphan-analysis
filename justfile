test:
    uv run pytest

analyze *ARGS:
    uv run python projects/ORPHAN_CURATED/analyze_report.py projects/ORPHAN_CURATED/reports/orphan-curated.csv {{ARGS}}

export-evidence reviews_root revision="HEAD":
    uv run python -m uniprot_orphan_analysis.export_evidence --reviews-root "{{reviews_root}}" --revision "{{revision}}"

check-evidence reviews_root revision="HEAD":
    uv run python -m uniprot_orphan_analysis.export_evidence --reviews-root "{{reviews_root}}" --revision "{{revision}}" --check

# Prepare, fetch or compare GO coverage; all cohort/cache/output paths are explicit.
[positional-arguments]
go-coverage *ARGS:
    uv run python -m uniprot_orphan_analysis.go_coverage "$@"
