"""Stream bulk tables, retaining only the 7,813 comparison IDs, then derive a left join.

Raw one-to-many classifications are saved intact. Exact duplicate CPC rows, if any,
are counted rather than silently dropped. Analysis will deduplicate membership only.
"""
import concurrent.futures
import csv
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import time
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ["g_cpc_current", "g_cpc_at_issue", "g_patent", "g_patent_abstract", "g_application"]

def extract(table):
    checkpoint = ROOT / "data" / (table + "_extraction_audit.json")
    if checkpoint.exists() and (ROOT / "data" / (table + "_subset.csv.gz")).exists():
        return json.loads(checkpoint.read_text())
    ids = set(pd.read_csv(ROOT / "data" / "cohort_frame.csv", dtype={"doc_id": str}).doc_id)
    path = ROOT / "cache" / (table + ".tsv.zip")
    result = []
    seen = 0
    started = time.monotonic()
    with zipfile.ZipFile(path) as archive, archive.open(table + ".tsv") as binary:
        text = io.TextIOWrapper(binary, encoding="utf-8", newline="")
        reader = csv.reader(text, delimiter="\t")
        header = next(reader)
        id_index = header.index("patent_id")
        for row in reader:
            if not row:
                continue
            seen += 1
            if row[id_index] in ids:
                if len(row) != len(header):
                    raise ValueError(f"Malformed row for target {row[id_index]} in {table}")
                result.append(row)
            if seen % 5000000 == 0:
                print(f"{table}: scanned {seen:,}; retained {len(result):,}; {time.monotonic()-started:.0f}s", flush=True)
    d = pd.DataFrame(result, columns=header)
    d.to_csv(ROOT / "data" / (table + "_subset.csv.gz"), index=False, compression="gzip")
    print(f"{table}: finished {seen:,} rows, {len(d):,} retained", flush=True)
    audit = {"table": table, "bulk_rows_scanned": seen, "retained_rows": len(d),
            "retained_patents": d.patent_id.nunique(), "exact_duplicate_rows": int(d.duplicated().sum())}
    checkpoint.write_text(json.dumps(audit, indent=2) + "\n")
    return audit

if __name__ == "__main__":
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as executor:
        audits = list(executor.map(extract, TABLES))
    frame = pd.read_csv(ROOT / "data" / "cohort_frame.csv", dtype={"doc_id": str, "appl_id": str}, float_precision="round_trip")
    enriched = frame.copy()
    for table in ["g_patent", "g_patent_abstract", "g_application"]:
        d = pd.read_csv(ROOT / "data" / (table + "_subset.csv.gz"), dtype=str, keep_default_na=False)
        if d.patent_id.duplicated().any():
            raise ValueError(f"Expected one row per grant in {table}; investigate before aggregation")
        enriched = enriched.merge(d, left_on="doc_id", right_on="patent_id", how="left", validate="one_to_one").drop(columns="patent_id")
    for table, column in [("g_cpc_current", "current_cpc_subclasses"), ("g_cpc_at_issue", "issue_cpc_subclasses")]:
        cpc = pd.read_csv(ROOT / "data" / (table + "_subset.csv.gz"), dtype=str)
        subclass = cpc.groupby("patent_id").cpc_subclass.agg(lambda x: "|".join(sorted(set(x.dropna()))))
        enriched[column] = enriched.doc_id.map(subclass).fillna("")
    assert len(enriched) == len(frame) and enriched.doc_id.is_unique
    assert pd.to_datetime(enriched.pub_dt).equals(pd.to_datetime(enriched.patent_date))
    enriched.to_csv(ROOT / "data" / "enriched_patent_cohorts.csv.gz", index=False, compression="gzip")
    with zipfile.ZipFile(ROOT / "cache" / "g_cpc_title.tsv.zip") as z:
        titles = pd.read_csv(z.open("g_cpc_title.tsv"), sep="\t", dtype=str)
    used_subclasses = set()
    for text in enriched.current_cpc_subclasses:
        used_subclasses.update(text.split("|"))
    titles.loc[titles.cpc_subclass.isin(used_subclasses)].to_csv(ROOT / "data" / "cpc_titles_subset.csv.gz", index=False, compression="gzip")
    missing = {col: int(enriched[col].isna().sum() + enriched[col].eq("").sum()) for col in ["patent_title", "patent_abstract", "filing_date"]}
    application_comparison = {"note": "Application ID formatting is compared separately; grant date equality is asserted.",
                              "application_columns": list(enriched.filter(regex="application|filing").columns)}
    audit = {"target_rows": len(frame), "tables": audits, "field_missing": missing,
             "grant_dates_exactly_match": True, "left_join_rows_preserved": True,
             "application_check": application_comparison}
    (ROOT / "outputs" / "enrichment_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    spec = importlib.util.spec_from_file_location("fetch", Path(__file__).with_name("01_fetch_enrichment.py"))
    fetch = importlib.util.module_from_spec(spec); spec.loader.exec_module(fetch)
    sources = []
    for name, (size, checksum) in fetch.FILES.items():
        if (ROOT / "cache" / name).stat().st_size != size or fetch.digest(ROOT / "cache" / name) != checksum:
            raise ValueError(f"Unverified input: {name}")
        sources.append({"file": name, "url": f"https://zenodo.org/api/records/{fetch.RECORD}/files/{name}/content",
                        "bytes": size, "md5": checksum, "release_date": "2024-12-31", "retrieved_utc": "2026-10-04"})
    (ROOT / "data" / "source_manifest.json").write_text(json.dumps(sources, indent=2) + "\n")