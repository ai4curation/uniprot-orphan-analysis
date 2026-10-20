# UniProt orphan analysis

Reproducible searches and source records for reviewed UniProt proteins outside
the reference proteomes selected for their exact taxon. The initial cohort is
39 accessions across 23 taxa, captured for the
[AI Gene Review ORPHAN_CURATED project](https://github.com/ai4curation/ai-gene-review/blob/cmungall/aigr-missing-swissprot/projects/ORPHAN_CURATED.md).

This repository owns the analysis artifacts. Current counterpart decisions,
functional reviews, GO annotation assessments, and generated curation reports
belong in [ai-gene-review](https://github.com/ai4curation/ai-gene-review).
The preferred Swiss-Prot accessions are retained there; these searches do not
transfer annotations or automatically establish locus or functional equivalence.

## Contents

- `genes/SPECIES/GENE/GENE-record-evidence.yaml`: full source snapshots,
  including UniProtKB records, reference-proteome metadata, sampled UniSave
  entries, retrieval dates, release headers, and selected ENA provenance.
- `genes/SPECIES/GENE/GENE-bioinformatics/reference-counterparts/`: query and
  candidate FASTAs, raw search tables, global comparison metrics, detailed
  alignments, and per-gene commands. `RESULTS.md` preserves the interpretation
  at the time of analysis; consult the gene review for the current decision.
- `projects/ORPHAN_CURATED/reports/orphan-curated.csv`: fixed input cohort.
- `projects/ORPHAN_CURATED/counterpart-decisions.yaml`: historical batch-import
  manifest, not the source of current curation decisions.
- `src/uniprot_orphan_analysis/`: sequence comparison and compact evidence export.

The initial artifacts were migrated from AI Gene Review revision
`a879ee61ed` (PR #5219 / superseded data PR #5244). Full reference-proteome
FASTAs are downloaded into the ignored `.cache/` directory. Candidate sequences
and query sequences used by the archived comparisons are committed here.
Original source URLs and attribution remain in each snapshot; `LICENSE` covers
the repository's code, while third-party source records retain their own terms.

## Reproduce an analysis

Install Python 3.12+, `uv`, `just`, and MMseqs2 **18-8cc5c**. `uv.lock` pins the
Python environment, including Biopython **1.85**.

```sh
uv sync --locked
just test
just analyze --fetch --accession Q8L4H4 --rerun
```

The batch command takes explicit accession filters and uses the fixed cohort's
exact-taxon reference-proteome IDs. Existing comparisons are retained without
`--rerun`. The per-gene `justfile` also provides snapshot and analysis commands;
the older Populus recipes use `just fetch-target` before `just analyze`.

Live UniProt downloads can change since the captured release. Source checksums,
software versions, search parameters, and retrieval dates are recorded in the
comparison files. A rerun creates new observations, requiring manual reassessment.
MMseqs2 is heuristic; a negative search does not prove genomic absence. A result
at the 1,000-hit cap is not an exhaustive list. Shared sequences and close matches
do not by themselves distinguish paralogs, alleles, or source cultivars.

## Publish compact evidence back to the reviews

Commit the analysis first, then export against that immutable commit:

```sh
just export-evidence /path/to/ai-gene-review "$(git rev-parse HEAD)"
just check-evidence /path/to/ai-gene-review "$(git rev-parse HEAD)"
```

The exporter reads source files directly from the requested Git commit and uses
the review's citations to select original source line ranges with context. It
fails if a quotation is absent from the archive. Each small per-gene extract
records the archive commit, source paths, SHA-256 digests, pinned links, and
original source metadata. Complete matching UniSave fields retain their evidence
tags for the review repository's provenance checks. No full protein sequences or
complete candidate tables are exported.

`--check` verifies the extracts against the archive without rewriting them.
Review curation and its history remain in AI Gene Review; refreshing an extract
does not adjudicate any biological relationship.
