"""Search a protein FASTA, then globally align every returned candidate.

MMseqs2 provides a sensitive full-proteome search, not an exhaustive guarantee.
Biopython global BLOSUM62 alignments use gap open -10 and extension -0.5,
including terminal gaps. Identity is identities / all alignment columns;
coverage is paired residues / the respective full sequence length. Outputs
record observations only: selecting an equivalent record is manual curation.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import Bio
from Bio import SeqIO
from Bio.Align import PairwiseAligner, substitution_matrices
from Bio.SeqRecord import SeqRecord
import yaml


def compare_sequences(query: str, target: str) -> tuple[dict[str, Any], str]:
    """Return global alignment measurements and the actual alignment text."""
    if not query or not target:
        raise ValueError("Both sequences must be nonempty")
    aligner = PairwiseAligner(
        mode="global",
        substitution_matrix=substitution_matrices.load("BLOSUM62"),
        open_gap_score=-10,
        extend_gap_score=-0.5,
    )
    alignment = aligner.align(query, target)[0]
    counts = alignment.counts()
    paired = int(counts.identities + counts.mismatches)
    substitutions = []
    for q_index, t_index in zip(*alignment.indices):
        if q_index >= 0 and t_index >= 0 and query[q_index] != target[t_index]:
            substitutions.append(
                {
                    "query_position": int(q_index) + 1,
                    "query_residue": query[q_index],
                    "target_position": int(t_index) + 1,
                    "target_residue": target[t_index],
                }
            )
    return {
        "global_score": float(alignment.score),
        "query_length": len(query),
        "target_length": len(target),
        "alignment_columns": alignment.length,
        "identities": int(counts.identities),
        "mismatches": int(counts.mismatches),
        "gap_columns": int(counts.gaps),
        "identity_percent": round(100 * counts.identities / alignment.length, 4),
        "query_coverage_percent": round(100 * paired / len(query), 4),
        "target_coverage_percent": round(100 * paired / len(target), 4),
        "substitutions": substitutions,
    }, str(alignment)


def accession(identifier: str) -> str:
    """Extract an accession from either a UniProt FASTA ID or a bare ID."""
    fields = identifier.split("|")
    return fields[1] if len(fields) >= 3 else identifier


def merge_reference_fastas(paths: list[Path], output: Path) -> int:
    """Build a union for taxa with several reference proteomes, rejecting conflicts."""
    records: dict[str, SeqRecord] = {}
    for path in paths:
        for record in SeqIO.parse(path, "fasta"):
            key = accession(record.id)
            if key in records and records[key].seq != record.seq:
                raise ValueError(f"Conflicting sequences for {key}")
            records[key] = record
    SeqIO.write([records[k] for k in sorted(records)], output, "fasta")
    return len(records)


def retain_alignment_details(
    document: dict[str, Any], output: Path, limit: int
) -> None:
    """Retain all candidate scores/sequences but detailed alignments only for top hits."""
    if limit < 1:
        raise ValueError("At least one detailed alignment must be retained")
    document["provenance"]["detailed_alignment_limit"] = limit
    for candidate in document["candidates"][limit:]:
        candidate.pop("substitutions", None)
        (output / f"{candidate['accession']}.alignment.txt").unlink(missing_ok=True)


def analyze(
    query_path: Path,
    targets_path: Path,
    output: Path,
    target_provenance: Path | None = None,
    detail_limit: int = 10,
) -> dict[str, Any]:
    """Search one query and retain all hits, candidate sequences, and alignments."""
    queries = list(SeqIO.parse(query_path, "fasta"))
    if len(queries) != 1:
        raise ValueError("Provide exactly one query sequence")
    query = queries[0]
    query_id = accession(query.id)
    output.mkdir(parents=True, exist_ok=True)
    query_copy = output / "query.fasta"
    SeqIO.write([query], query_copy, "fasta")
    hits_path = output / "search.tsv"
    command = [
        "mmseqs",
        "easy-search",
        str(query_copy),
        str(targets_path),
        str(hits_path),
        str(output / "tmp"),
        "--threads",
        "4",
        "-s",
        "7.5",
        "-e",
        "1e-5",
        "--max-seqs",
        "1000",
        "--format-output",
        "query,target,pident,alnlen,qstart,qend,qlen,tstart,tend,tlen,evalue,bits",
        "--remove-tmp-files",
        "1",
        "-v",
        "1",
    ]
    subprocess.run(command, check=True)
    hits: dict[str, dict[str, Any]] = {}
    for line in hits_path.read_text().splitlines():
        fields = line.split("\t")
        if len(fields) != 12 or accession(fields[0]) != query_id:
            raise ValueError(f"Unexpected search row: {line}")
        hits[accession(fields[1])] = {
            "evalue": float(fields[10]),
            "bit_score": float(fields[11]),
        }
    candidates = []
    count = 0
    for record in SeqIO.parse(targets_path, "fasta"):
        count += 1
        if accession(record.id) in hits:
            candidates.append(record)
    if len(candidates) != len(hits):
        raise ValueError("Search targets could not be uniquely resolved in the FASTA")
    SeqIO.write(candidates, output / "candidates.fasta", "fasta")
    rows = []
    for candidate in candidates:
        target_id = accession(candidate.id)
        metrics, alignment = compare_sequences(str(query.seq), str(candidate.seq))
        rows.append(
            {
                "accession": target_id,
                "description": candidate.description,
                **hits[target_id],
                **metrics,
            }
        )
        (output / f"{target_id}.alignment.txt").write_text(
            "\n".join(line.rstrip() for line in alignment.splitlines()) + "\n"
        )
    rows.sort(key=lambda r: (-r["global_score"], r["accession"]))
    provenance = {
        "query_accession": query_id,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "biopython_version": Bio.__version__,
        "mmseqs_version": subprocess.check_output(
            ["mmseqs", "version"], text=True
        ).strip(),
        "command": command,
        "target_sequence_count": count,
        "query_sha256": hashlib.sha256(query_copy.read_bytes()).hexdigest(),
        "targets_sha256": hashlib.sha256(targets_path.read_bytes()).hexdigest(),
        "global_alignment": {
            "mode": "global",
            "matrix": "BLOSUM62",
            "open_gap": -10,
            "extend_gap": -0.5,
            "terminal_gaps_penalized": True,
        },
        "identity_denominator": "All global alignment columns, including gaps",
        "coverage_denominator": "Full query/target length; numerator is paired nongap residues",
        "limitation": "MMseqs2 heuristic search; no guarantee of exhaustive retrieval or locus equivalence",
    }
    if target_provenance:
        provenance["target_source"] = json.loads(target_provenance.read_text())
    document = {
        "provenance": provenance,
        "candidate_count": len(rows),
        "candidates": rows,
    }
    retain_alignment_details(document, output, detail_limit)
    (output / "comparison.yaml").write_text(
        yaml.dump(document, Dumper=yaml.CSafeDumper, sort_keys=False, width=110)
    )
    return document


def main() -> None:
    """Run a reproducible comparison from explicit sequence inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--target-provenance", type=Path)
    args = parser.parse_args()
    document = analyze(
        args.query, args.targets, args.output_dir, args.target_provenance
    )
    print(
        f"{document['provenance']['query_accession']}: {document['candidate_count']} candidates"
    )


if __name__ == "__main__":
    main()
