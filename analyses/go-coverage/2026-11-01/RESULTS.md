# Equivalent records retain different GO evidence

The 2026-11-01 capture found **48 non-IEA annotation rows, including 41
experimental-code rows, on the 18 preferred Swiss-Prot accessions without
matching evidence on their assessed reference-proteome counterparts**. The
counterparts have 69 rows: 59 IEA and 10 IBA, with no experimental-code rows.
These are database coverage observations, not a recommendation to copy every row.

The full comparison is in the [generated report](report/REPORT.md), with
[per-annotation match flags](report/annotations.csv),
[pair counts](report/pairs.csv), and [provenance](report/provenance.json).
The cohort comes from AI Gene Review revision
`6f76823948d9ae45adda6169d593c2afc41b39d6`, selecting only
`REFERENCE_PROTEOME_EQUIVALENT` relationships. All 18 pairs still pass the live
taxonomy, reviewed-source, and reference-proteome membership checks.

## What the counts mean

The source accessions have 110 distinct canonical support rows. Across pairs,
55 distinct assertions are shared, 29 occur only on the source under the exact
matching rules, and nine occur only on the counterpart. Counts of assertions
and evidence rows are different: several papers or interaction partners can
support one assertion.

Of the 41 experimental-code source rows:

- **Nine have the same exact assertion on the counterpart with other evidence.**
  This is an evidence/provenance difference, not an absent GO assertion.
- **32 lack an exact assertion match.** Three of those have the same GO term but
  different relations: CP12 chloroplast localization, aatA peroxisomal-matrix
  localization/activity, and aatA penicillin biosynthesis. They should not be
  described as missing GO terms.
- **29 lack even the same GO ID on the counterpart.** Twelve of these are bare
  `GO:0005515` protein-binding rows. Excluding that uninformative term leaves
  **17 experimental rows with an absent exact GO ID**, still requiring biological
  and ontology-level review before calling them gaps.

The seven other non-IEA source rows are four ISS and three TAS. All 48 non-IEA
rows lack a counterpart match even at the less strict code/reference level, so
this result is not merely an artifact of differing WITH/FROM or assigned-by.
The ten counterpart IBA rows are themselves based on PAINT curation and
experimental grounding through a phylogenetic model. Their lack of direct
experimental-code rows does not mean they lack curated support. This analysis
does not audit those phylogenetic models or challenge the IBA assertions.
There are no isoform rows in this capture. Exact duplicate support/date handling
and isoform separation are covered by regression tests for future cohorts.

## Useful examples for follow-up

**AVR9 (`P22287` → `L7YER9`) is the clearest coverage case.** QuickGO returns
five source annotations (three EXP, two TAS) and a verified zero-hit response for
the counterpart. The five rows describe two GO assertions. This is a candidate
for asking UniProt how the curated source and genome-derived counterpart should
be linked, while retaining the preferred Swiss-Prot accession. It is not proof
that the annotations will be deleted or that the biological relationship should
be resolved by merging records.

**nas-8 (`D2KBH9` → `A0A4U8UYW6`) illustrates an evidence-only difference.**
Both records carry `GO:0004222` metalloendopeptidase activity with `enables`, but
the source has EXP evidence citing `PMID:20670659`, whereas the counterpart's
row is IEA. The GO assertion is represented; the experimental citation is not.

**aatA (`P15802` → `A0ABQ8WFJ5`) shows why qualifiers must remain visible.**
The counterpart has all three GO IDs carried by the source. Nevertheless, two
source rows lack an exact assertion match because their relations differ, and
the six non-IEA source rows lack matching evidence on the counterpart. Calling
this six missing functions would be misleading.

**The strongest evidence differences are not concentrated in Populus.** The
five Populus equivalents in this cohort have one non-IEA source row (PAL, ISS)
and no experimental-code GO rows in this live capture. The other poplar case,
WIN6, remains a candidate and is correctly excluded from an equivalent-only
comparison. The lack of experimental GO rows says nothing about whether the
proteins have experimental literature or curated UniProt descriptions.

## Limits and next action

The comparison is exact: no ontology closure or relation entailment is applied.
A counterpart may have a broader or narrower term that overlaps the source's
biology. It also does not re-adjudicate the original equivalence decisions or
read each experimental paper anew. The presence of an annotation is not evidence
for accepting its function in a gene review.

Use AVR9 and nas-8 as complementary examples in a focused UniProt query, with
the full report available for inspection. Ask about record linkage and
preserving access to curated evidence, rather than requesting indiscriminate
annotation transfer. No external feedback has been sent by this analysis.

QuickGO and UniProt responses were retrieved between
2026-11-01T22:46:37Z and 2026-11-01T22:47:58Z. UniProt reported release
2026_03; QuickGO did not expose a dataset release. This is an 81-second collection
window, not a synchronized database release. Full source pages and their hashes
are committed beside the report.

## Reproducibility checklist

- [x] Scripts accept explicit cohort, revision, cache, and output paths; no gene list or conclusions are hardcoded.
- [x] The same workflow ran on 18 independent pairs across ten taxa.
- [x] All source requests completed; pagination and hit totals were checked, including a legitimate zero-hit response.
- [x] Live taxonomy and proteome membership checks passed for all 18 pairs.
- [x] Raw responses, normalized comparison tables, and source/code hashes are retained.
- [x] Summary interpretation is separate from the generated report and code.
- [x] Synthetic tests distinguish evidence-only differences, NOT, qualifiers, extensions, AND/OR groups, duplicates, isoforms, and incomplete responses.
- [x] The committed report was regenerated offline and checked for identical outputs.
