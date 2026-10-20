"""Apply explicit manual decisions with citations to previously captured evidence.

This command never selects a counterpart or judges equivalence. Its input decision
manifest supplies those judgments. It refuses to overwrite existing assessments
and preserves all pre-existing review content, including GO annotation decisions.
"""

import argparse
import csv
from pathlib import Path
import re
import textwrap
from typing import Any

import yaml


class CuratedDumper(yaml.SafeDumper):
    """Keep multiline evidence quotations readable."""


def represent_text(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    """Use literal blocks for multiline quotations."""
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", value, style="|" if "\n" in value else None
    )


CuratedDumper.add_representer(str, represent_text)


def claim(
    kind: str, description: str, source: str, quotes: list[str]
) -> dict[str, Any]:
    """Build a typed claim with explicit source citations."""
    return {
        "type": kind,
        "description": description,
        "supported_by": [
            {"reference_id": source, "supporting_text": q} for q in quotes
        ],
    }


def apply_decision(row: dict[str, str], decision: dict[str, Any], date: str) -> None:
    """Attach one already-adjudicated assessment to every local copy of a review."""
    for review_path in row["review_paths"].split(";"):
        path = Path(review_path)
        gene = path.name.removesuffix("-ai-review.yaml")
        original = path.read_text()
        before = yaml.safe_load(original)
        if before.get("alternative_records") or before.get(
            "reference_proteome_assessments"
        ):
            raise ValueError(f"Assessment already exists: {path}")
        snapshot_path = path.parent / f"{gene}-record-evidence.yaml"
        snapshot_text = snapshot_path.read_text()
        snapshot = yaml.load(snapshot_text, Loader=yaml.CSafeLoader)
        analysis_dir = path.parent / f"{gene}-bioinformatics" / "reference-counterparts"
        comparison = yaml.load(
            (analysis_dir / "comparison.yaml").read_text(), Loader=yaml.CSafeLoader
        )
        source = "file:" + str(snapshot_path.relative_to("genes"))
        analysis_source = "file:" + str(
            (analysis_dir / "comparison.yaml").relative_to("genes")
        )
        accession = decision["accession"]
        alternative = decision["alternative"]
        proteomes = row["reference_proteomes"].split(";")
        assert snapshot["observations"]["primary_accession"] == accession
        assert snapshot["observations"]["alternative_accession"] == alternative
        assert not snapshot["observations"]["primary_in_any_reference_proteome"]
        count = comparison["candidate_count"]
        searched = comparison["provenance"]["target_sequence_count"]
        search_description = (
            f"MMseqs2 searched {searched:,} sequences across {', '.join(proteomes)} at E <= 1e-5 and "
            f"sensitivity 7.5, returning {count} hits. "
            + (
                "Every returned sequence was globally aligned using BLOSUM62 with gap-open -10 "
                "and extension -0.5. All candidate scores and sequences are retained; detailed "
                f"alignments are retained for {min(count, 10)} leading candidates. "
                if count else "The search table and candidate FASTA are empty; no alignments were generated. "
            )
            + "The heuristic search does not establish genomic absence or unique locus identity."
        )
        if count >= 1000:
            search_description += " The search reached its 1000-hit retrieval cap."
        evidence = [
            claim(
                "PROTEOME_SEARCH",
                search_description,
                analysis_source,
                [f"target_sequence_count: {searched}", f"candidate_count: {count}"],
            )
        ]
        if alternative:
            assert snapshot["observations"]["alternative_in_reference_proteome"]
            assert snapshot["observations"]["same_taxon"]
            candidate = next(
                c for c in comparison["candidates"] if c["accession"] == alternative
            )
            fields = [
                "query_length",
                "target_length",
                "alignment_columns",
                "identities",
                "mismatches",
                "gap_columns",
                "identity_percent",
                "query_coverage_percent",
                "target_coverage_percent",
            ]
            quote = "\n".join(f"  {key}: {candidate[key]}" for key in fields).lstrip()
            evidence.append(
                claim(
                    "SEQUENCE_COMPARISON",
                    f"{alternative}: {candidate['identities']} identities across {candidate['alignment_columns']} "
                    f"global-alignment columns ({candidate['identity_percent']}% identity including gaps), "
                    f"{candidate['mismatches']} substitutions and {candidate['gap_columns']} gap columns. "
                    f"Identity over paired residues is {100 * candidate['identities'] / (candidate['identities'] + candidate['mismatches']):.4f}% "
                    f"({candidate['identities']}/{candidate['identities'] + candidate['mismatches']}); gap columns are excluded from this denominator. "
                    f"Query coverage is {candidate['query_coverage_percent']}%; target coverage is "
                    f"{candidate['target_coverage_percent']}%. Sequence similarity is interpreted in the manual rationale.",
                    analysis_source,
                    [quote],
                )
            )
        membership = "The primary accession is outside every searched exact-taxon reference proteome."
        membership_quotes = ["primary_in_any_reference_proteome: false"]
        if alternative:
            membership += f" Current UniProt records place {alternative} in {proteomes[0]} and give it the same taxon as the primary."
            membership_quotes += [
                "alternative_in_reference_proteome: true",
                "same_taxon: true",
            ]
        evidence.append(
            claim("PROTEOME_MEMBERSHIP", membership, source, membership_quotes)
        )
        history_descriptions, history_quotes = [], []
        for historical in snapshot["unisave_records"]:
            links = ", ".join(historical["proteomes"]) or "no Proteomes cross-reference"
            history_descriptions.append(f"{historical['entry_date']}: {links}")
            start = snapshot_text.index("  entry_date: " + historical["entry_date"])
            end = snapshot_text.index("  reference_proteome_keyword:", start)
            history_quotes.append(snapshot_text[start:end].strip())
        history_description = (
            "Sampled UniSave observations: " + "; ".join(history_descriptions) + ". "
        )
        history_description += ("This dated observation does" if len(history_descriptions) == 1 else "These dated observations do") + " not establish uninterrupted membership/absence, the exact change date, or UniProt's motivation."
        evidence.append(
            claim("RECORD_HISTORY", history_description, source, history_quotes)
        )
        for extra in decision.get("additional_evidence", []):
            evidence.append(
                claim(extra["type"], extra["description"], source, extra["quotes"])
            )
        reason = (
            f"Retain {accession} as the primary Swiss-Prot accession. "
            + decision["reason"]
        )
        if alternative:
            block = {
                "alternative_records": [
                    {
                        "id": alternative,
                        "relationship": "REFERENCE_PROTEOME_" + decision["assessment"],
                        "reference_proteome": proteomes[0],
                        "reviewed_on": date,
                        "reason": reason,
                        "evidence": evidence,
                    }
                ]
            }
        else:
            block = {
                "reference_proteome_assessments": [
                    {
                        "reference_proteomes": proteomes,
                        "status": "NO_SUPPORTED_COUNTERPART",
                        "reviewed_on": date,
                        "reason": reason,
                        "evidence": evidence,
                    }
                ]
            }
        serialized = yaml.dump(block, Dumper=CuratedDumper, sort_keys=False, width=100)
        anchors = [key for key in ("existing_annotations:\n", "references:\n") if key in original]
        if not anchors:
            raise ValueError(f"No insertion anchor in {path}")
        anchor = min(anchors, key=original.index)
        updated = original.replace(anchor, serialized + anchor, 1)
        references = [
            {
                "id": source,
                "title": f"UniProt and UniSave counterpart-assessment snapshot for {accession} ({date})",
            },
            {
                "id": analysis_source,
                "title": f"Reference-proteome search and global alignments for {accession} ({date})",
            },
        ]
        reference_start = original.index("references:\n") + len("references:\n")
        match = re.search(r"(?m)^( *)- ", original[reference_start:])
        if match is None:
            raise ValueError(f"Could not determine reference-list indentation: {path}")
        reference_items = textwrap.indent(
            yaml.safe_dump(references, sort_keys=False, width=100), match.group(1)
        )
        updated = updated.replace("references:\n", "references:\n" + reference_items, 1)
        after = yaml.safe_load(updated)
        assert {k: v for k, v in before.items() if k != "references"} == {
            k: v
            for k, v in after.items()
            if k
            not in [
                "references",
                "alternative_records",
                "reference_proteome_assessments",
            ]
        }
        assert all(r in after["references"] for r in before.get("references", []))
        path.write_text(updated)
        print(path, decision["assessment"], flush=True)


def main() -> None:
    """Apply the supplied manual decision manifest; fail on unexpected source state."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("decisions", type=Path)
    args = parser.parse_args()
    with args.report.open() as handle:
        rows = {r["accession"]: r for r in csv.DictReader(handle)}
    decisions = yaml.safe_load(args.decisions.read_text())
    for decision in decisions["decisions"]:
        apply_decision(rows[decision["accession"]], decision, decisions["reviewed_on"])


if __name__ == "__main__":
    main()
