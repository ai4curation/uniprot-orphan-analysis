"""Export compact, source-backed evidence for the AI Gene Review cohort.

Read archive files from a Git commit, never from mutable working-tree outputs.
Quotes select original source lines with context; review text is never copied
into the evidence as a substitute for a source. Unmatched quotes fail the export.
"""

import argparse
import csv
import hashlib
import io
import re
import subprocess
from pathlib import Path

import yaml

REPOSITORY = "https://github.com/ai4curation/uniprot-orphan-analysis"
ROOT = Path(__file__).resolve().parents[2]
REPORT = "projects/ORPHAN_CURATED/reports/orphan-curated.csv"


class EvidenceDumper(yaml.SafeDumper):
    """Keep original excerpts readable without changing their contents."""


def multiline(dumper, value):
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", value, style="|" if "\n" in value else None
    )


EvidenceDumper.add_representer(str, multiline)


def quoted_evidence(data):
    """Collect unique quotes of archive sources, including consolidated extracts."""
    quotes = set()
    if isinstance(data, dict):
        ref = data.get("reference_id", "")
        if ref.startswith("file:") and (
            ref.endswith(("-record-evidence.yaml", "-origin-evidence.yaml"))
            or "/reference-counterparts/" in ref
        ) and data.get("supporting_text"):
            quotes.add(data["supporting_text"])
        for value in data.values():
            quotes.update(quoted_evidence(value))
    elif isinstance(data, list):
        for value in data:
            quotes.update(quoted_evidence(value))
    return quotes


def source_excerpts(raw, quotes, context=2):
    """Return original line spans and the quotes they cover, allowing only whitespace variation."""
    lines = raw.splitlines(keepends=True)
    spans = []
    matched = set()
    for quote in sorted(quotes):
        pattern = r"\s+".join(re.escape(word) for word in quote.split())
        if not pattern:
            raise ValueError("Empty source quotation")
        for match in re.finditer(pattern, raw):
            matched.add(quote)
            start = max(0, raw.count("\n", 0, match.start()) - context)
            end = min(len(lines), raw.count("\n", 0, match.end()) + context + 1)
            spans.append((start, end))
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return [
        {"start_line": start + 1, "end_line": end, "text": "".join(lines[start:end])}
        for start, end in merged
    ], matched


def select_unisave_blocks(raw, quotes):
    """Retain complete matching flat-file fields, including their evidence tags.

    Keep citation blocks together and split CC at topic boundaries. The consumer's
    existing UniProt provenance classifier can still distinguish curated statements
    from labels and predictions without storing whole entries or protein sequences.
    """
    blocks = []
    current = []
    previous = None
    for line in raw.splitlines(keepends=True):
        field = line[:2]
        group = "REF" if field in {"RN", "RP", "RC", "RX", "RG", "RA", "RT", "RL"} else field
        if current and (group != previous or line.startswith(("CC   -!-", "RN   "))):
            blocks.append("".join(current))
            current = []
        current.append(line)
        previous = group
    if current:
        blocks.append("".join(current))
    retained = []
    for block in blocks:
        plain = re.sub(r"(?m)^[A-Z]{2}   ", "", block)
        for quote in quotes:
            pattern = r"\s+".join(re.escape(word) for word in quote.split())
            if pattern and (re.search(pattern, block) or re.search(pattern, plain)):
                retained.append(block)
                break
    return "".join(retained)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def export_document(review, folder, revision):
    """Build one gene's extract entirely from committed source material."""
    gene = folder.name
    paths = [folder / f"{gene}-record-evidence.yaml"]
    for suffix in (
        f"{gene}-bioinformatics/reference-counterparts/comparison.yaml",
        f"{gene}-origin-evidence.yaml",
    ):
        path = folder / suffix
        if git("ls-tree", revision, "--", path.as_posix()).strip():
            paths.append(path)
    raw_sources = {
        path: git("show", f"{revision}:{path.as_posix()}").decode() for path in paths
    }
    snapshot = yaml.safe_load(raw_sources[paths[0]])
    quotes = quoted_evidence(review)
    found = set()
    archived_sources = []
    for path, raw in raw_sources.items():
        excerpts, matched = source_excerpts(raw, quotes)
        found.update(matched)
        archived_sources.append({
            "path": path.as_posix(),
            "url": f"{REPOSITORY}/blob/{revision}/{path.as_posix()}",
            "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "excerpts": excerpts,
        })
    if quotes - found:
        raise ValueError(f"{folder}: quotations absent from archive: {sorted(quotes - found)}")
    records = []
    for record in snapshot["current_records"]:
        records.append({
            key: record[key] for key in
            ("primaryAccession", "entryType", "entryAudit", "genes", "geneLocations")
            if key in record
        })
        records[-1]["organism"] = {
            key: value for key, value in record["organism"].items()
            if key in ("taxonId", "scientificName")
        }
        records[-1]["sequence"] = {
            "length": record["sequence"]["length"],
            "sha256": hashlib.sha256(record["sequence"]["value"].encode()).hexdigest(),
        }
        records[-1]["uniProtKBCrossReferences"] = [
            xref for xref in record["uniProtKBCrossReferences"]
            if xref["database"] in ("Proteomes", "Gramene")
        ]
    proteomes = [
        snapshot["reference_proteome_record"],
        *snapshot.get("additional_reference_proteome_records", []),
    ]
    document = {
        "snapshot_type": "uniprot_record_evidence_extract",
        "archive": {"repository": REPOSITORY, "commit": revision},
        "extraction": (
            "Original source line ranges with two context lines; not complete records. "
            "Structured fields are selected from the same archived snapshots. "
            "Sequence values are replaced by lengths and SHA-256 digests."
        ),
        "sources": snapshot["sources"],
        "observations": snapshot["observations"],
        "current_records": records,
        "reference_proteomes": [
            {key: p[key] for key in ("id", "proteomeType", "taxonomy")} for p in proteomes
        ],
        "unisave_records": [
            {
                **{key: value for key, value in h.items() if key != "record_text"},
                "record_text": select_unisave_blocks(h["record_text"], quotes),
            }
            for h in snapshot["unisave_records"]
        ],
        "archived_sources": archived_sources,
    }
    for path, raw in raw_sources.items():
        if path.name != "comparison.yaml":
            continue
        comparison = yaml.safe_load(raw)
        selected_ids = {a["id"] for a in review.get("alternative_records", [])}
        selected_ids.update(c["accession"] for c in comparison["candidates"][:2])
        alignment_files = git(
            "ls-tree", "-r", "--name-only", revision, "--", path.parent.as_posix()
        ).decode().splitlines()
        document["comparison"] = {
            "provenance": comparison["provenance"],
            "candidate_count": comparison["candidate_count"],
            "retained_alignment_count": sum(p.endswith(".alignment.txt") for p in alignment_files),
            "candidates": [
                {key: value for key, value in c.items() if key != "substitutions"}
                for c in comparison["candidates"] if c["accession"] in selected_ids
            ],
        }
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews-root", type=Path, required=True)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    revision = git("rev-parse", "--verify", f"{args.revision}^{{commit}}").decode().strip()
    rows = csv.DictReader(io.StringIO(git("show", f"{revision}:{REPORT}").decode()))
    stale = []
    count = 0
    for row in rows:
        for review_path in row["review_paths"].split(";"):
            path = Path(review_path)
            review = yaml.safe_load((args.reviews_root / path).read_text())
            document = export_document(review, path.parent, revision)
            destination = args.reviews_root / path.parent / f"{path.parent.name}-record-evidence.yaml"
            rendered = yaml.dump(document, Dumper=EvidenceDumper, sort_keys=False, width=100)
            if args.check:
                if not destination.exists() or destination.read_text() != rendered:
                    stale.append(str(destination))
            else:
                destination.write_text(rendered)
            count += 1
    if stale:
        raise SystemExit("Stale evidence extracts:\n" + "\n".join(stale))
    print(f"{'Checked' if args.check else 'Exported'} {count} evidence extracts from {revision}")


if __name__ == "__main__":
    main()
