"""Compare live GO annotation coverage for explicitly curated equivalent pairs.

No GO annotations or counterpart judgments are generated. Prepare a cohort from
a committed review project; fetch complete QuickGO and UniProt responses; then
compare offline. All paths and the input revision are explicit CLI arguments.
"""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

QUICKGO = "https://www.ebi.ac.uk/QuickGO/services/annotation/search"
UNIPROT = "https://rest.uniprot.org"
EXPERIMENTAL = frozenset(["EXP", "IDA", "IPI", "IMP", "IGI", "IEP", "HTP", "HDA", "HMP", "HGI", "HEP"])


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def prepare(root, revision, project, output):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args]).decode()
    revision = git("rev-parse", "--verify", f"{revision}^{{commit}}").strip()
    text = git("show", f"{revision}:{project}")
    metadata = yaml.safe_load(text.split("---", 2)[1])
    pairs = []
    seen = set()
    for symbol in metadata["genes"]:
        species, gene = symbol.split("/")
        path = f"genes/{species}/{gene}/{gene}-ai-review.yaml"
        raw = git("show", f"{revision}:{path}")
        review = yaml.safe_load(raw)
        for alternative in review.get("alternative_records", []):
            if alternative["relationship"] != "REFERENCE_PROTEOME_EQUIVALENT":
                continue
            key = (review["id"], alternative["id"])
            if key in seen:
                raise ValueError(f"Duplicate equivalent pair: {key}")
            seen.add(key)
            pairs.append({
                "orphan": review["id"], "counterpart": alternative["id"],
                "gene": symbol, "taxon": int(review["taxon"]["id"].split(":")[1]),
                "reference_proteome": alternative["reference_proteome"],
                "reviewed_on": str(alternative["reviewed_on"]),
                "review_path": path, "review_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            })
    if not pairs:
        raise ValueError("No curated equivalents in project")
    write_json(output, {
        "review_repository": "https://github.com/ai4curation/ai-gene-review",
        "review_revision": revision, "project": project,
        "pairs": sorted(pairs, key=lambda pair: pair["gene"]),
    })
    print(f"Prepared {len(pairs)} equivalent pairs from {revision}", flush=True)


def request_page(session, url, params=None):
    response = session.get(url, params=params, headers={"Accept": "application/json"}, timeout=60)
    response.raise_for_status()
    return {
        "url": response.url, "retrieved_at": datetime.now(UTC).isoformat(),
        "headers": {key: response.headers[key] for key in (
            "Date", "x-uniprot-release", "x-uniprot-release-date", "x-total-results"
        ) if key in response.headers},
        "body": response.json(), "next": response.links.get("next", {}).get("url"),
    }


def quickgo_rows(pages, accession):
    """Fail on incomplete pages, changing totals, repeated IDs or unrelated products."""
    if not pages:
        raise ValueError("Missing QuickGO response")
    total = pages[0]["body"]["numberOfHits"]
    if not isinstance(total, int) or total < 0:
        raise ValueError("Invalid QuickGO hit count")
    rows = []
    for number, page in enumerate(pages, 1):
        body = page["body"]
        empty_first = total == 0 and number == 1 and body["pageInfo"]["current"] == 0
        if body["numberOfHits"] != total or (body["pageInfo"]["current"] != number and not empty_first):
            raise ValueError("QuickGO totals/pages changed during fetch")
        rows.extend(body["results"])
    if len(rows) != total or len({r["id"] for r in rows}) != total:
        raise ValueError(f"Incomplete/duplicate QuickGO results for {accession}")
    for row in rows:
        product = row["geneProductId"]
        if product != f"UniProtKB:{accession}" and not product.startswith(f"UniProtKB:{accession}-"):
            raise ValueError(f"Unrelated QuickGO product: {product}")
    return rows


def fetch_item(task):
    kind, identifier, path = task
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=Retry(
            total=4, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )))
        pages = []
        if kind == "quickgo":
            while True:
                params = [("geneProductId", f"UniProtKB:{identifier}"),
                          ("includeFields", "goName"), ("limit", "200")]
                if pages:
                    params.append(("page", str(len(pages) + 1)))
                page = request_page(session, QUICKGO, params)
                pages.append(page)
                count = sum(len(p["body"]["results"]) for p in pages)
                expected = page["body"]["numberOfHits"]
                if count >= expected:
                    break
                if not page["body"]["results"]:
                    raise ValueError("QuickGO returned an empty intermediate page")
            quickgo_rows(pages, identifier)
        elif kind == "entries":
            pages.append(request_page(session, f"{UNIPROT}/uniprotkb/{identifier}.json"))
            if pages[0]["body"]["primaryAccession"] != identifier:
                raise ValueError(f"Accession redirected: {identifier}")
        else:
            params = {"query": f"reference:true AND taxonomy_id:{identifier}", "size": 500, "format": "json"}
            pages.append(request_page(session, f"{UNIPROT}/proteomes/search", params))
            while pages[-1]["next"]:
                url = pages[-1]["next"]
                if not url.startswith(UNIPROT + "/") or url in {p["url"] for p in pages}:
                    raise ValueError("Invalid proteome pagination")
                pages.append(request_page(session, url))
            total = int(pages[0]["headers"]["x-total-results"])
            if sum(len(p["body"]["results"]) for p in pages) != total:
                raise ValueError("Incomplete proteome search")
        write_json(path, {"kind": kind, "identifier": identifier, "pages": pages})
    print(f"Fetched {kind}/{identifier}", flush=True)


def fetch(cohort, cache, resume=False):
    pairs = read_json(cohort)["pairs"]
    tasks = []
    for accession in sorted({p[k] for p in pairs for k in ("orphan", "counterpart")}):
        tasks += [(kind, accession, cache / kind / f"{accession}.json") for kind in ("entries", "quickgo")]
    tasks += [("proteomes", taxon, cache / "proteomes" / f"{taxon}.json") for taxon in sorted({p["taxon"] for p in pairs})]
    # A fresh output directory prevents accidental mixing with a previous snapshot.
    if not resume and any(path.exists() for _, _, path in tasks):
        raise ValueError("Use a new source directory for each live snapshot")
    if resume:
        tasks = [task for task in tasks if not task[2].exists()]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch_item, tasks))


def canonical(value):
    """Sort unordered sets while preserving nested AND/OR group boundaries."""
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return sorted((canonical(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    return value


def packed(value):
    return json.dumps(canonical(value or []), sort_keys=True, separators=(",", ":"))


def normalize(row):
    for key in ("geneProductId", "goId", "qualifier", "goEvidence", "evidenceCode", "reference", "assignedBy", "taxonId"):
        if not row.get(key):
            raise ValueError(f"Missing annotation field: {key}")
    return {
        "product": row["geneProductId"], "go_id": row["goId"], "go_name": row.get("goName") or "",
        "qualifier": "|".join(sorted({part.strip() for part in re.split(r"[|,]", row["qualifier"])})),
        "extensions": packed(row.get("extensions")), "evidence": row["goEvidence"],
        "eco": row["evidenceCode"], "reference": row["reference"],
        "with_from": packed(row.get("withFrom")), "assigned_by": row["assignedBy"],
        "date": row.get("date") or "", "taxon": row["taxonId"],
    }


def assertion(row):
    # ND reports lack of knowledge; it must not match a positive functional assertion.
    return row["go_id"], row["qualifier"], row["extensions"], row["evidence"] == "ND"


def support(row):
    return assertion(row) + tuple(row[k] for k in ("evidence", "eco", "reference", "with_from", "assigned_by"))


def code_reference(row):
    return assertion(row) + (row["evidence"], row["reference"])


def unique_rows(rows):
    unique = {}
    for raw in rows:
        row = normalize(raw)
        key = (row["product"], support(row))
        if key not in unique or row["date"] > unique[key]["date"]:
            unique[key] = row
    return sorted(unique.values(), key=lambda row: (row["product"], support(row)))


def compare_rows(left, right):
    """Compare exact assertions and evidence, excluding the accession and annotation date."""
    assertions = {assertion(row) for row in right}
    supports = {support(row) for row in right}
    codes_refs = {code_reference(row) for row in right}
    terms = {row["go_id"] for row in right}
    return [{**row, "same_term": row["go_id"] in terms,
             "same_assertion": assertion(row) in assertions,
             "same_code_reference": code_reference(row) in codes_refs,
             "same_support": support(row) in supports} for row in left]


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"No rows for {path}")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def compare(cohort_path, cache, output):
    cohort = read_json(cohort_path)
    output.mkdir(parents=True, exist_ok=True)
    summaries, annotations, evidence, excluded, sources = [], [], Counter(), [], {}

    def load(kind, identifier):
        path = cache / kind / f"{identifier}.json"
        raw = path.read_bytes()
        payload = json.loads(raw)
        if payload["kind"] != kind or str(payload["identifier"]) != str(identifier):
            raise ValueError(f"Unexpected cached source: {path}")
        sources[f"{kind}/{identifier}.json"] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "pages": [{k: page[k] for k in ("url", "retrieved_at", "headers")} for page in payload["pages"]],
        }
        return payload["pages"]

    for pair in cohort["pairs"]:
        entries = {role: load("entries", pair[role])[0]["body"] for role in ("orphan", "counterpart")}
        proteome_pages = load("proteomes", pair["taxon"])
        proteomes = [p for page in proteome_pages for p in page["body"]["results"]
                    if p["taxonomy"]["taxonId"] == pair["taxon"] and p["proteomeType"] == "Reference proteome"]
        reference_ids = {p["id"] for p in proteomes}
        memberships = {
            role: {x["id"] for x in entry["uniProtKBCrossReferences"] if x["database"] == "Proteomes"}
            for role, entry in entries.items()
        }
        if (entries["orphan"]["entryType"] != "UniProtKB reviewed (Swiss-Prot)"
            or any(e["primaryAccession"] != pair[role] or e["organism"]["taxonId"] != pair["taxon"] for role, e in entries.items())
            or pair["reference_proteome"] not in reference_ids
            or pair["reference_proteome"] not in memberships["counterpart"]
            or memberships["orphan"] & reference_ids):
            raise ValueError(f"Curated pair requires membership/taxonomy reassessment: {pair['gene']}")
        rows, counts = {}, {}
        for role in ("orphan", "counterpart"):
            accession = pair[role]
            raw = quickgo_rows(load("quickgo", accession), accession)
            if any(row["taxonId"] != pair["taxon"] for row in raw):
                raise ValueError(f"Unexpected annotation taxon: {accession}")
            counts[role] = len(raw)
            unique = unique_rows(raw)
            rows[role] = [r for r in unique if r["product"] == f"UniProtKB:{accession}"]
            excluded.extend({"gene": pair["gene"], "role": role, **r} for r in unique if r not in rows[role])
        source = compare_rows(rows["orphan"], rows["counterpart"])
        target = compare_rows(rows["counterpart"], rows["orphan"])
        for role, records in (("orphan", source), ("counterpart", target)):
            annotations.extend({"gene": pair["gene"], "orphan": pair["orphan"], "counterpart": pair["counterpart"], "role": role, **r} for r in records)
            for row in records:
                evidence[(row["evidence"], role + "_rows")] += 1
                if role == "orphan":
                    evidence[(row["evidence"], "orphan_support_only")] += not row["same_support"]
                    evidence[(row["evidence"], "orphan_assertion_only")] += not row["same_assertion"]
        summaries.append({
            **{k: pair[k] for k in ("gene", "orphan", "counterpart", "reference_proteome")},
            "orphan_raw_rows": counts["orphan"], "counterpart_raw_rows": counts["counterpart"],
            "orphan_rows": len(source), "counterpart_rows": len(target),
            "orphan_non_iea": sum(r["evidence"] != "IEA" for r in source),
            "orphan_experimental": sum(r["evidence"] in EXPERIMENTAL for r in source),
            "shared_assertions": len({assertion(r) for r in source if r["same_assertion"]}),
            "orphan_only_assertions": len({assertion(r) for r in source if not r["same_assertion"]}),
            "counterpart_only_assertions": len({assertion(r) for r in target if not r["same_assertion"]}),
            "orphan_support_only": sum(not r["same_support"] for r in source),
            "orphan_non_iea_support_only": sum(not r["same_support"] and r["evidence"] != "IEA" for r in source),
            "orphan_experimental_support_only": sum(not r["same_support"] and r["evidence"] in EXPERIMENTAL for r in source),
            "orphan_non_iea_assertion_only_rows": sum(not r["same_assertion"] and r["evidence"] != "IEA" for r in source),
            "orphan_experimental_assertion_only_rows": sum(not r["same_assertion"] and r["evidence"] in EXPERIMENTAL for r in source),
        })
    releases = {page["headers"]["x-uniprot-release"] for source in sources.values()
                for page in source["pages"] if "x-uniprot-release" in page["headers"]}
    if len(releases) != 1:
        raise ValueError(f"Missing/mixed UniProt releases: {releases}")
    evidence_rows = [{"evidence": code, **{column: evidence[(code, column)] for column in (
        "orphan_rows", "counterpart_rows", "orphan_support_only", "orphan_assertion_only"
    )}} for code in sorted({code for code, _ in evidence})]
    dates = sorted(page["retrieved_at"] for source in sources.values() for page in source["pages"])
    metadata = {
        "analysis_module_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cohort_sha256": hashlib.sha256(cohort_path.read_bytes()).hexdigest(),
        "review_revision": cohort["review_revision"], "uniprot_release": next(iter(releases)),
        "retrieved_from": dates[0], "retrieved_to": dates[-1],
        "quickgo_release": None, "quickgo_release_note": "QuickGO responses do not expose a dataset release; retrieval window and complete pages are retained.",
        "pair_count": len(summaries), "excluded_isoform_rows": len(excluded), "sources": sources,
    }
    write_csv(output / "pairs.csv", summaries)
    write_csv(output / "annotations.csv", annotations)
    write_csv(output / "evidence-counts.csv", evidence_rows)
    write_json(output / "excluded-isoforms.json", excluded)
    write_json(output / "provenance.json", metadata)
    (output / "REPORT.md").write_text(render_report(summaries, evidence_rows, annotations, metadata))
    print(f"Compared {len(summaries)} pairs; {len(annotations)} unique canonical support rows; {len(excluded)} isoform rows excluded", flush=True)


def render_report(pairs, evidence, annotations, metadata):
    source = [r for r in annotations if r["role"] == "orphan"]
    lines = ["# GO coverage on curated equivalent records", "",
        f"Retrieved {metadata['retrieved_from']} to {metadata['retrieved_to']}; UniProt release {metadata['uniprot_release']}. QuickGO dataset release unavailable.", "",
        f"Compared **{len(pairs)}** manually assessed equivalent pairs; current Swiss-Prot status, exact taxonomy and reference-proteome membership verified for every pair.", "",
        f"Orphan accessions have **{len(source)}** distinct canonical annotation support rows: **{sum(r['evidence'] != 'IEA' for r in source)} non-IEA**, including **{sum(r['evidence'] in EXPERIMENTAL for r in source)} experimental-code rows**.", "",
        f"**{sum(p['orphan_non_iea_support_only'] for p in pairs)} non-IEA support rows** have no exact support counterpart; **{sum(p['orphan_experimental_support_only'] for p in pairs)}** carry experimental codes. Of these, **{sum(p['orphan_non_iea_assertion_only_rows'] for p in pairs)} non-IEA rows** (**{sum(p['orphan_experimental_assertion_only_rows'] for p in pairs)} experimental**) lack even an exact assertion match, regardless of evidence.", "",
        "## Comparison definitions", "",
        "An assertion matches GO ID, qualifier/relation (including NOT), annotation extension, and ND/no-data status. Evidence support additionally matches GO and ECO evidence codes, reference, WITH/FROM and assigned-by. Accession and date are excluded from cross-record comparisons. Repeated support rows differing only in date collapse to the latest date. Group boundaries in WITH/FROM and extensions are preserved; list order is ignored.", "",
        "This is an exact-match audit, without ontology ancestor/descendant inference. No exact match does not establish missing biological coverage, a curation error, or annotation loss. Non-IEA includes computational and phylogenetic evidence and ND; it is not synonymous with experimental evidence. Same assertions can have different evidence. Different WITH/FROM or assigned-by values also produce support differences; see `same_code_reference` in the annotation table for a less strict evidence comparison.", "",
        f"Isoform annotations are retained separately, not mapped between proteins without an explicit isoform correspondence ({metadata['excluded_isoform_rows']} excluded rows). Fresh QuickGO data is used for both sides; historical mixed-date GOA caches and reviewer-proposed annotations are not inputs. The original manually assessed equivalence is not reassessed by this GO audit, and no annotations are transferred.", "",
        "## Evidence codes", "", "| Code | Orphan rows | Counterpart rows | Orphan support unmatched | Orphan rows without assertion match |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {r['evidence']} | {r['orphan_rows']} | {r['counterpart_rows']} | {r['orphan_support_only']} | {r['orphan_assertion_only']} |" for r in evidence]
    lines += ["", "## Equivalent pairs", "", "| Gene | Preferred Swiss-Prot | Counterpart | Rows (orphan / counterpart) | Shared assertions | Orphan-only assertions | Non-IEA support unmatched | Experimental rows without assertion match |", "|---|---|---|---:|---:|---:|---:|---:|"]
    for p in sorted(pairs, key=lambda p: (-p["orphan_experimental_assertion_only_rows"], -p["orphan_non_iea_support_only"], p["gene"])):
        lines.append(f"| {p['gene']} | [{p['orphan']}](https://www.uniprot.org/uniprotkb/{p['orphan']}/entry) | [{p['counterpart']}](https://www.uniprot.org/uniprotkb/{p['counterpart']}/entry) | {p['orphan_rows']} / {p['counterpart_rows']} | {p['shared_assertions']} | {p['orphan_only_assertions']} | {p['orphan_non_iea_support_only']} | {p['orphan_experimental_assertion_only_rows']} |")
    lines += ["", "## Non-IEA support requiring comparison", "", "These are source database annotations, not new assertions endorsed by this analysis. Repeated term/reference rows may have different WITH/FROM partners; AND groups and OR alternatives remain distinct. Full annotation extensions and assigned-by values are retained in the CSV.", "", "| Gene | GO term | Relation | Evidence | Reference | WITH/FROM | Exact assertion on counterpart? | Same code/reference? |", "|---|---|---|---|---|---|---|---|"]
    for r in source:
        if r["evidence"] == "IEA" or r["same_support"]:
            continue
        ref = r["reference"]
        link = f"[{ref}](https://pubmed.ncbi.nlm.nih.gov/{ref.split(':')[1]}/)" if ref.startswith("PMID:") else ref
        groups = json.loads(r["with_from"])
        with_from = " OR ".join(" AND ".join(f"{x['db']}:{x['id']}" for x in group["connectedXrefs"]) for group in groups) or "—"
        lines.append(f"| {r['gene']} | [{r['go_id']}](https://www.ebi.ac.uk/QuickGO/term/{r['go_id']}) {r['go_name'].replace('|', '/')} | {r['qualifier'].replace('|', ' / ')} | {r['evidence']} | {link} | {with_from} | {'yes' if r['same_assertion'] else 'no'} | {'yes' if r['same_code_reference'] else 'no'} |")
    lines += ["", "[Pair counts](pairs.csv) · [All annotation comparisons](annotations.csv) · [Evidence counts](evidence-counts.csv) · [Provenance and source hashes](provenance.json)", "",
              "API documentation: [QuickGO](https://www.ebi.ac.uk/QuickGO/api/index.html). Raw responses are retained in the sibling `sources/` directory.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--reviews-root", type=Path, required=True)
    prepare_parser.add_argument("--revision", required=True)
    prepare_parser.add_argument("--project", required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    for name in ("fetch", "compare"):
        p = commands.add_parser(name)
        p.add_argument("--cohort", type=Path, required=True)
        p.add_argument("--cache", type=Path, required=True)
        if name == "compare":
            p.add_argument("--output", type=Path, required=True)
        else:
            p.add_argument("--resume", action="store_true", help="Fetch missing files after an interrupted capture; retain earlier retrieval dates")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.reviews_root, args.revision, args.project, args.output)
    elif args.command == "fetch":
        fetch(args.cohort, args.cache, args.resume)
    else:
        compare(args.cohort, args.cache, args.output)


if __name__ == "__main__":
    main()
