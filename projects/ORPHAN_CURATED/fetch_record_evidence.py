"""Fetch a reproducible source snapshot; never author an equivalence judgment.

Example:
    uv run python projects/ORPHAN_CURATED/fetch_record_evidence.py O65922 A0A2K2C664 \
        --proteome UP000006729 --history-versions 90 119 130 \
        --output genes/POPTR/CCOAOMT2/CCOAOMT2-record-evidence.yaml

UniSave is UniProt's archive of prior entry versions. Sampled versions provide
dated observations, not proof of uninterrupted absence between those versions.
"""

import argparse
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def multiline(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    """Keep archived flat files legible and verbatim within the YAML snapshot."""
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str", value, style="|" if "\n" in value else None
    )


def main() -> None:
    """Collect current records, the reference proteome, and explicit old versions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("primary")
    parser.add_argument(
        "alternative",
        nargs="?",
        help="Omit when no supported counterpart was identified",
    )
    parser.add_argument("--proteome", required=True)
    parser.add_argument("--additional-proteome", action="append", default=[])
    parser.add_argument("--history-versions", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--ena", action="append", default=[], help="Include source nucleotide record(s)"
    )
    args = parser.parse_args()
    sources: list[dict[str, Any]] = []
    with requests.Session() as session:
        session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )
            ),
        )

        def fetch(url: str) -> requests.Response:
            """Fetch a source successfully and retain its retrieval provenance."""
            response = session.get(url, timeout=45)
            response.raise_for_status()
            sources.append(
                {
                    "url": response.url,
                    "retrieved_at": datetime.now(UTC).isoformat(),
                    "uniprot_release": response.headers.get("x-uniprot-release"),
                }
            )
            return response

        accessions = [args.primary] + ([args.alternative] if args.alternative else [])
        records = [
            fetch(f"https://rest.uniprot.org/uniprotkb/{a}.json").json()
            for a in accessions
        ]
        if [r["primaryAccession"] for r in records] != accessions:
            raise ValueError(
                "An accession redirected; inspect the current records before comparing"
            )
        proteome = fetch(
            f"https://rest.uniprot.org/proteomes/{args.proteome}.json"
        ).json()
        additional_proteomes = [
            fetch(f"https://rest.uniprot.org/proteomes/{p}.json").json()
            for p in args.additional_proteome
        ]
        history = []
        for version in args.history_versions:
            url = f"https://rest.uniprot.org/unisave/{args.primary}?format=txt&versions={version}"
            text = fetch(url).text
            if (
                len(re.findall(r"^ID   ", text, re.MULTILINE)) != 1
                or f"entry version {version}." not in text
            ):
                raise ValueError(f"Unexpected UniSave response for {url}")
            history.append(
                {
                    "entry_version": version,
                    "url": url,
                    "entry_date": re.findall(r"^DT   (.*entry version.*)$", text, re.MULTILINE)[
                        0
                    ],
                    "proteomes": re.findall(r"^DR   Proteomes; (UP\d+);", text, re.MULTILINE),
                    "reference_proteome_keyword": any(
                        "Reference proteome" in line
                        for line in text.splitlines()
                        if line.startswith("KW")
                    ),
                    "record_text": text,
                }
            )
        origin_records = []
        for accession in args.ena:
            url = f"https://www.ebi.ac.uk/ena/browser/api/embl/{accession}"
            record_text = fetch(url).text
            if (
                not record_text.startswith("ID   ")
                or f"AC   {accession};" not in record_text
            ):
                raise ValueError(f"Unexpected ENA response for {accession}")
            origin_records.append(
                {"accession": accession, "url": url, "record_text": record_text}
            )
    primary = records[0]
    alternative = records[1] if args.alternative else None
    memberships = [
        {
            x["id"]
            for x in r.get("uniProtKBCrossReferences", [])
            if x["database"] == "Proteomes"
        }
        for r in records
    ]
    primary_uniparc = primary["extraAttributes"]["uniParcId"]
    alternative_uniparc = (
        alternative["extraAttributes"]["uniParcId"] if alternative else None
    )
    observations = {
        "primary_accession": args.primary,
        "alternative_accession": args.alternative,
        "sequence_identical": (
            primary["sequence"]["value"] == alternative["sequence"]["value"]
        )
        if alternative
        else None,
        "primary_sequence_length": primary["sequence"]["length"],
        "alternative_sequence_length": alternative["sequence"]["length"]
        if alternative
        else None,
        "shared_uniparc_id": primary_uniparc
        if primary_uniparc == alternative_uniparc
        else None,
        "same_taxon": (
            primary["organism"]["taxonId"] == alternative["organism"]["taxonId"]
        )
        if alternative
        else None,
        "reference_proteome": args.proteome,
        "proteome_is_reference": proteome["proteomeType"] == "Reference proteome",
        "proteome_taxon_matches": proteome["taxonomy"]["taxonId"]
        == primary["organism"]["taxonId"],
        "primary_in_reference_proteome": args.proteome in memberships[0],
        "alternative_in_reference_proteome": args.proteome in memberships[1]
        if alternative
        else None,
        "searched_reference_proteomes": [args.proteome, *args.additional_proteome],
        "primary_in_any_reference_proteome": bool(
            memberships[0] & {args.proteome, *args.additional_proteome}
        ),
        "sampled_history_versions": args.history_versions,
        "sampled_versions_with_proteome_links": [
            h["entry_version"] for h in history if h["proteomes"]
        ],
    }
    document = {
        "snapshot_type": "uniprot_record_comparison",
        "sources": sources,
        "observations": observations,
        "current_records": records,
        "reference_proteome_record": proteome,
        "additional_reference_proteome_records": additional_proteomes,
        "unisave_records": history,
        "origin_records": origin_records,
    }
    yaml.SafeDumper.add_representer(str, multiline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=110)
    )
    print(yaml.safe_dump(observations, sort_keys=False))


if __name__ == "__main__":
    main()
