"""Extracts must be actual source spans, retaining context and evidence tags."""

from uniprot_orphan_analysis.export_evidence import (
    quoted_evidence,
    select_unisave_blocks,
    source_excerpts,
)


def test_excerpts_preserve_source_lines_and_merge_overlapping_context():
    raw = "before\n  name: A\n  length: 20\n  identity: 80\nafter\noutside\n"
    excerpts, matched = source_excerpts(raw, {"name: A", "length: 20\nidentity: 80"}, context=1)
    assert matched == {"name: A", "length: 20\nidentity: 80"}
    assert excerpts == [{"start_line": 1, "end_line": 5, "text": "".join(raw.splitlines(True)[:5])}]
    assert source_excerpts(raw, {"invented: claim"}) == ([], set())


def test_only_archive_quotes_select_excerpts():
    assert quoted_evidence({"supported_by": [
        {"reference_id": "PMID:1", "supporting_text": "not from archive"},
        {"reference_id": "file:X/X-record-evidence.yaml", "supporting_text": "actual source"},
    ]}) == {"actual source"}


def test_unisave_extract_retains_whole_comment_with_provenance():
    raw = (
        "ID   TEST\n"
        "CC   -!- FUNCTION: Acts on a\n"
        "CC       substrate. {ECO:0000256|ARBA:ARBA1}.\n"
        "CC   -!- SUBCELLULAR LOCATION: Cytoplasm.\n"
        "SQ   SEQUENCE   3 AA;\n"
        "     AAA\n//\n"
    )
    assert select_unisave_blocks(raw, {"Acts on a substrate"}) == (
        "CC   -!- FUNCTION: Acts on a\n"
        "CC       substrate. {ECO:0000256|ARBA:ARBA1}.\n"
    )
