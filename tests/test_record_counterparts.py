"""Sequence differences and coverage must remain explicit in counterpart reports."""

import pytest
from Bio import SeqIO
from uniprot_orphan_analysis.record_counterparts import (
    compare_sequences,
    merge_reference_fastas,
    retain_alignment_details,
)


def test_exact_sequence_comparison():
    result, _ = compare_sequences("MAPIAVGDVLPDGK", "MAPIAVGDVLPDGK")
    assert result["identities"] == 14
    assert result["identity_percent"] == 100
    assert result["gap_columns"] == 0
    assert result["substitutions"] == []


def test_substitution_reports_one_based_coordinates():
    result, alignment = compare_sequences("MAPIAVGDVLPDGK", "MAPIAVGDILPDGK")
    assert result["mismatches"] == 1
    assert result["substitutions"] == [
        {
            "query_position": 9,
            "query_residue": "V",
            "target_position": 9,
            "target_residue": "I",
        }
    ]
    assert result["query_coverage_percent"] == 100
    assert "MAPIAVGDILPDGK" in alignment


def test_truncation_is_not_full_length_identity():
    result, _ = compare_sequences("MAPIAVGDVLPDGK", "MAPIAVGDVL")
    assert result["identities"] == 10
    assert result["gap_columns"] == 4
    assert result["identity_percent"] < 100
    assert result["query_coverage_percent"] < 100
    assert result["target_coverage_percent"] == 100


def test_reference_union_deduplicates_identical_accessions(tmp_path):
    first, second = tmp_path / "one.fa", tmp_path / "two.fa"
    first.write_text(">tr|P12345|ONE\nMAPIAVGDVL\n")
    second.write_text(">tr|P12345|ONE\nMAPIAVGDVL\n>tr|Q12345|TWO\nMAPPAVGDVL\n")
    output = tmp_path / "union.fa"
    assert merge_reference_fastas([first, second], output) == 2
    assert len(list(SeqIO.parse(output, "fasta"))) == 2
    second.write_text(">tr|P12345|ONE\nMAPPAVGDVL\n")
    with pytest.raises(ValueError, match="Conflicting"):
        merge_reference_fastas([first, second], output)


def test_compaction_retains_all_scores_and_top_alignment(tmp_path):
    document = {
        "provenance": {},
        "candidate_count": 2,
        "candidates": [
            {"accession": "P12345", "global_score": 90, "substitutions": []},
            {
                "accession": "Q12345",
                "global_score": 40,
                "substitutions": ["difference"],
            },
        ],
    }
    for a in ["P12345", "Q12345"]:
        (tmp_path / f"{a}.alignment.txt").write_text("alignment")
    retain_alignment_details(document, tmp_path, 1)
    assert document["candidate_count"] == 2
    assert document["candidates"][1]["global_score"] == 40
    assert "substitutions" not in document["candidates"][1]
    assert (tmp_path / "P12345.alignment.txt").exists()
    assert not (tmp_path / "Q12345.alignment.txt").exists()
