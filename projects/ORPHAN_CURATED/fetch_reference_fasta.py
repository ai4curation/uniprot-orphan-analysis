"""Download a live proteome FASTA with matching provenance for local comparison."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests


def main() -> None:
    """Fetch the explicit proteome and save retrieval metadata beside the FASTA."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proteome")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    response = requests.get(
        "https://rest.uniprot.org/uniprotkb/stream",
        params={"query": f"proteome:{args.proteome}", "format": "fasta"},
        timeout=120,
    )
    response.raise_for_status()
    if not response.text.startswith(">"):
        raise ValueError("No FASTA records returned")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(response.text)
    provenance = {
        "url": response.url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "uniprot_release": response.headers.get("x-uniprot-release"),
        "sequence_count": sum(
            line.startswith(">") for line in response.text.splitlines()
        ),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }
    args.output.with_suffix(".provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
