"""Coverage comparisons must not erase evidence, qualifiers or context."""

from copy import deepcopy
from pathlib import Path

import pytest

from uniprot_orphan_analysis.go_coverage import (
    assertion,
    compare,
    compare_rows,
    normalize,
    packed,
    quickgo_rows,
    support,
    unique_rows,
)


def annotation(**overrides):
    return {
        "id": "UniProtKB:P12345!1", "geneProductId": "UniProtKB:P12345",
        "goId": "GO:0000001", "goName": "example", "qualifier": "enables",
        "goEvidence": "IDA", "evidenceCode": "ECO:0000314", "reference": "PMID:123",
        "assignedBy": "UniProt", "taxonId": 1234, "date": "20260101",
        "withFrom": None, "extensions": None, **overrides,
    }


def test_accession_and_date_do_not_create_a_support_difference():
    source = normalize(annotation())
    target = normalize(annotation(geneProductId="UniProtKB:Q12345", date="20261101"))
    result = compare_rows([source], [target])[0]
    assert result["same_assertion"] and result["same_support"]


@pytest.mark.parametrize("change", [
    {"goEvidence": "IEA", "evidenceCode": "ECO:0000501"},
    {"reference": "PMID:456"}, {"assignedBy": "GO_Central"},
    {"withFrom": [{"connectedXrefs": [{"db": "UniProtKB", "id": "Q12345"}]}]},
])
def test_same_assertion_is_not_the_same_support(change):
    result = compare_rows([normalize(annotation())], [normalize(annotation(**change))])[0]
    assert result["same_assertion"] and not result["same_support"]
    assert result["same_code_reference"] == (not ("reference" in change or "goEvidence" in change))


@pytest.mark.parametrize("change", [
    {"qualifier": "NOT|enables"}, {"qualifier": "contributes_to"},
    {"extensions": [{"connectedXrefs": [{"relation": "occurs_in", "id": "GO:0000002"}]}]},
    {"goEvidence": "ND"},
])
def test_qualifiers_extensions_and_nd_are_not_collapsed(change):
    result = compare_rows([normalize(annotation())], [normalize(annotation(**change))])[0]
    assert result["same_term"] and not result["same_assertion"]


def test_and_or_groups_are_preserved_but_order_does_not_matter():
    a = {"db": "UniProtKB", "id": "A"}
    b = {"db": "UniProtKB", "id": "B"}
    both = [{"connectedXrefs": [a, b]}]
    either = [{"connectedXrefs": [a]}, {"connectedXrefs": [b]}]
    assert packed(both) == packed([{"connectedXrefs": [b, a]}])
    assert packed(both) != packed(either)


def test_duplicates_ignore_date_but_keep_distinct_evidence_and_isoforms():
    rows = unique_rows([
        annotation(), annotation(id="second", date="20260201"),
        annotation(reference="PMID:456"), annotation(geneProductId="UniProtKB:P12345-2"),
    ])
    assert len(rows) == 3
    selected = next(r for r in rows if r["product"] == "UniProtKB:P12345" and r["reference"] == "PMID:123")
    assert selected["date"] == "20260201"


def page(rows, total, number=1):
    return {"body": {"numberOfHits": total, "results": rows, "pageInfo": {"current": number}}}


def test_empty_valid_response_is_zero_but_incomplete_response_is_not():
    assert quickgo_rows([page([], 0)], "P12345") == []
    assert quickgo_rows([page([], 0, number=0)], "P12345") == []
    with pytest.raises(ValueError, match="Incomplete"):
        quickgo_rows([page([], 1)], "P12345")
    with pytest.raises(ValueError, match="Missing"):
        quickgo_rows([], "P12345")


def test_multi_page_completeness_drift_and_duplicates():
    pages = [page([annotation()], 2), page([annotation(id="second")], 2, 2)]
    assert len(quickgo_rows(pages, "P12345")) == 2
    drift = deepcopy(pages)
    drift[1]["body"]["numberOfHits"] = 3
    with pytest.raises(ValueError, match="changed"):
        quickgo_rows(drift, "P12345")
    duplicate = deepcopy(pages)
    duplicate[1]["body"]["results"][0]["id"] = annotation()["id"]
    with pytest.raises(ValueError, match="duplicate"):
        quickgo_rows(duplicate, "P12345")


def test_unrelated_products_are_rejected_and_isoforms_are_retained_for_separate_accounting():
    assert quickgo_rows([page([annotation(geneProductId="UniProtKB:P12345-2")], 1)], "P12345")
    with pytest.raises(ValueError, match="Unrelated"):
        quickgo_rows([page([annotation(geneProductId="UniProtKB:Q12345")], 1)], "P12345")


def test_ancestor_labels_or_similar_names_do_not_imply_an_exact_assertion():
    a = normalize(annotation())
    b = normalize(annotation(goId="GO:0000002"))
    assert assertion(a) != assertion(b)
    assert support(a) != support(b)


def test_required_fields_fail_closed():
    with pytest.raises(ValueError, match="Missing annotation field"):
        normalize(annotation(goEvidence=None))


def test_committed_capture_reproduces_reports_offline(tmp_path):
    run = Path(__file__).parents[1] / "analyses/go-coverage/2026-11-01"
    compare(run / "cohort.json", run / "sources", tmp_path)
    assert {p.name for p in tmp_path.iterdir()} == {p.name for p in (run / "report").iterdir()}
    for expected in (run / "report").iterdir():
        assert (tmp_path / expected.name).read_bytes() == expected.read_bytes(), expected.name
