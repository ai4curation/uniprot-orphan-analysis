"""Verify archived sequence and membership observations independently of reviews."""

import csv
from pathlib import Path

import pytest
import yaml
from Bio import SeqIO

from uniprot_orphan_analysis.record_counterparts import accession, compare_sequences

ROOT = Path(__file__).parents[1]
with (ROOT / "projects/ORPHAN_CURATED/reports/orphan-curated.csv").open() as handle:
    ROWS = list(csv.DictReader(handle))


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["accession"])
def test_archived_sources_and_selected_sequence_metrics(row):
    folder = ROOT / Path(row["review_paths"]).parent
    gene = folder.name
    snapshot = yaml.safe_load((folder / f"{gene}-record-evidence.yaml").read_text())
    primary = snapshot["current_records"][0]
    assert primary["primaryAccession"] == row["accession"]
    reference_ids = set(row["reference_proteomes"].split(";"))
    memberships = {
        x["id"] for x in primary["uniProtKBCrossReferences"] if x["database"] == "Proteomes"
    }
    assert not memberships & reference_ids
    proteomes = [
        snapshot["reference_proteome_record"],
        *snapshot.get("additional_reference_proteome_records", []),
    ]
    assert {p["id"] for p in proteomes} == reference_ids
    assert all(p["proteomeType"] == "Reference proteome" for p in proteomes)
    assert all(p["taxonomy"]["taxonId"] == primary["organism"]["taxonId"] for p in proteomes)
    for history in snapshot["unisave_records"]:
        assert f"entry version {history['entry_version']}." in history["record_text"]
    analysis = folder / f"{gene}-bioinformatics/reference-counterparts"
    if analysis.exists():
        comparison = yaml.safe_load((analysis / "comparison.yaml").read_text())
        assert comparison["candidate_count"] == len(comparison["candidates"])
        assert str(SeqIO.read(analysis / "query.fasta", "fasta").seq) == primary["sequence"]["value"]
        candidates = {
            accession(record.id): str(record.seq)
            for record in SeqIO.parse(analysis / "candidates.fasta", "fasta")
        }
        assert set(candidates) == {c["accession"] for c in comparison["candidates"]}
    if len(snapshot["current_records"]) == 2:
        target = snapshot["current_records"][1]
        assert target["organism"]["taxonId"] == primary["organism"]["taxonId"]
        assert any(
            x["database"] == "Proteomes" and x["id"] in reference_ids
            for x in target["uniProtKBCrossReferences"]
        )
        if analysis.exists():
            assert candidates[target["primaryAccession"]] == target["sequence"]["value"]
            selected = next(c for c in comparison["candidates"] if c["accession"] == target["primaryAccession"])
            observed, _ = compare_sequences(primary["sequence"]["value"], target["sequence"]["value"])
            assert all(selected[key] == value for key, value in observed.items())
        else:
            assert primary["sequence"]["value"] == target["sequence"]["value"]
            assert primary["extraAttributes"]["uniParcId"] == target["extraAttributes"]["uniParcId"]
            loci = [
                {x["id"] for x in record["uniProtKBCrossReferences"] if x["database"] == "Gramene"}
                for record in (primary, target)
            ]
            assert loci[0] & loci[1]
