# GO coverage comparison

Compare current GO annotations on manually assessed equivalent orphan Swiss-Prot
and reference-proteome records. The input cohort is derived from committed gene
YAML and the project frontmatter in AI Gene Review, not a hardcoded accession list.
Candidates, locus counterparts with altered function, and negative assessments
are excluded.

The [2026-11-01 results](2026-11-01/RESULTS.md) interpret the first completed run.
Its [generated report](2026-11-01/report/REPORT.md) and CSV tables are rebuilt
entirely from the captured source responses.

## Reproduction

Use `uv sync --locked` in this repository. Python dependencies are pinned by
`uv.lock`; this analysis uses requests and PyYAML, with no sequence-search binary.

Prepare a new cohort from an explicit review revision:

```sh
just go-coverage prepare \
  --reviews-root /path/to/ai-gene-review \
  --revision REVIEW_COMMIT \
  --project projects/ORPHAN_CURATED.md \
  --output /path/to/new-run/cohort.json
just go-coverage fetch \
  --cohort /path/to/new-run/cohort.json \
  --cache /path/to/new-run/sources
just go-coverage compare \
  --cohort /path/to/new-run/cohort.json \
  --cache /path/to/new-run/sources \
  --output /path/to/new-run/report
```

Fetch requires an unused source directory. After an interrupted capture, pass
`--resume` to fetch missing files, retaining earlier retrieval timestamps.
Comparison requires all sources and checks pagination, annotation identifiers,
hit totals, taxonomy, current accession identity, exact-taxon reference proteomes,
source Swiss-Prot status, counterpart membership, source nonmembership, and a
single UniProt release. Errors are never interpreted as zero annotations.

QuickGO does not supply a dataset release in these responses. Each request's
retrieval time and HTTP date are retained; this is a short collection window,
not an atomic cross-database release. UniProt release headers are also recorded.
Raw response bodies, cohort/review hashes, analysis-code hash, and source hashes
allow inspection and offline reproduction without changing the review caches.

Reproduce the committed run without network access:

```sh
just go-coverage compare \
  --cohort analyses/go-coverage/2026-11-01/cohort.json \
  --cache analyses/go-coverage/2026-11-01/sources \
  --output /tmp/orphan-go-coverage-reproduced
diff -r analyses/go-coverage/2026-11-01/report /tmp/orphan-go-coverage-reproduced
```

## Interpretation

`pairs.csv` summarizes each comparison; `annotations.csv` preserves both sides
with separate exact-term, exact-assertion, code/reference, and full-support match
flags. `evidence-counts.csv` counts evidence codes. Dates and accessions are ignored
when matching support across a pair; GO/ECO evidence, reference, WITH/FROM and
assigned-by are retained. Qualifiers, NOT, extensions, and ND status distinguish
assertions. Duplicate support differing only by date is counted once. Isoforms
are recorded separately because curated protein equivalence does not establish
isoform correspondence.

No ontology ancestor/descendant inference is performed. A missing exact match
does not establish missing biological coverage. Existing GO annotations are
audited as database assertions, not treated as evidence that their functions are
correct. Non-IEA is broader than experimental evidence. In particular, bare
protein-binding rows should not become proposed annotation transfers merely
because they are absent from a counterpart. Biological review precedes feedback.

Methods: [QuickGO API](https://www.ebi.ac.uk/QuickGO/api/index.html) and
[UniProt REST API](https://rest.uniprot.org/).
