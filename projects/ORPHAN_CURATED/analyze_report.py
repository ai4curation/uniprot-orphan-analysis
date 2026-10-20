"""Compute counterpart-search observations for each review in an audit CSV.

Requires cached current entries under CACHE/entries/ACCESSION.json and downloaded
reference FASTAs with .provenance.json sidecars. No relationship judgments are
generated. Existing comparison files are retained unless --rerun is requested.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import requests

from uniprot_orphan_analysis.record_counterparts import analyze, merge_reference_fastas


def main() -> None:
    """Analyze explicit report entries using their exact-taxon reference proteomes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--cache", type=Path, default=Path(".cache/orphan-curated"))
    parser.add_argument("--exclude-species", action="append", default=[])
    parser.add_argument("--rerun", action="store_true")
    parser.add_argument("--accession", action="append", default=[])
    parser.add_argument(
        "--fetch", action="store_true", help="Fetch missing entry and proteome caches"
    )
    args = parser.parse_args()
    with args.report.open() as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row["species"] in args.exclude_species:
            continue
        if args.accession and row["accession"] not in args.accession:
            continue
        proteomes = row["reference_proteomes"].split(";")
        if args.fetch:
            entry_path = args.cache / "entries" / f"{row['accession']}.json"
            if not entry_path.exists():
                response = requests.get(
                    f"https://rest.uniprot.org/uniprotkb/{row['accession']}.json",
                    timeout=45,
                )
                response.raise_for_status()
                entry_path.parent.mkdir(parents=True, exist_ok=True)
                entry_path.write_text(json.dumps(response.json(), indent=2))
            for proteome in proteomes:
                fasta = args.cache / f"{proteome}.fasta"
                if not fasta.exists():
                    subprocess.run(
                        [
                            "uv",
                            "run",
                            "python",
                            "projects/ORPHAN_CURATED/fetch_reference_fasta.py",
                            proteome,
                            "--output",
                            str(fasta),
                        ],
                        check=True,
                    )
        target = args.cache / ("__".join(proteomes) + ".fasta")
        if len(proteomes) > 1 and (not target.exists() or args.rerun):
            inputs = [args.cache / f"{p}.fasta" for p in proteomes]
            count = merge_reference_fastas(inputs, target)
            target.with_suffix(".provenance.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            json.loads(p.with_suffix(".provenance.json").read_text())
                            for p in inputs
                        ],
                        "sequence_count": count,
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                        "proteomes": proteomes,
                    },
                    indent=2,
                )
            )
        for review in row["review_paths"].split(";"):
            review_path = Path(review)
            gene = review_path.name.removesuffix("-ai-review.yaml")
            output = (
                review_path.parent / f"{gene}-bioinformatics" / "reference-counterparts"
            )
            if (output / "comparison.yaml").exists() and not args.rerun:
                continue
            entry = json.loads(
                (args.cache / "entries" / f"{row['accession']}.json").read_text()
            )
            if entry["primaryAccession"] != row["accession"]:
                raise ValueError("Primary accession changed; reassess the audit first")
            output.mkdir(parents=True, exist_ok=True)
            query = output / "query.fasta"
            query.write_text(f">{row['accession']}\n{entry['sequence']['value']}\n")
            document = analyze(
                query, target, output, target.with_suffix(".provenance.json")
            )
            print(
                row["accession"], gene, document["candidate_count"], "hits", flush=True
            )


if __name__ == "__main__":
    main()
