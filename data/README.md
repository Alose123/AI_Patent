# Data files

Large and binary source/derived files are kept out of the Git history. This keeps the repository lightweight and avoids committing an 85 MB raw CSV directly to a public repository.

## Local source files

| File | Size (bytes) | SHA-256 | Purpose |
|---|---:|---|---|
| `five_big_tech_ai_patents.csv` | 85,086,069 | `d34cf61d30554b30ddb6d8e7f06f7a3bc130799f643f95aef6c282d53de69e79` | Main five-company source extract used by the first analysis |
| `analysis_patent_cohorts.csv.gz` | 2,047,827 | `0a77bed1852ab810358762a6b51888f315d5818dbcd385731a408bf12009c540` | Enriched cohort output supplied with the CPC/text extension |

Reference deliverable archives used to prepare this repository:

| Archive | SHA-256 |
|---|---|
| `AI_Patent_Analysis_Complete.zip` | `cd7ad0fdd8d098f72373ca0d5d5dc53303d128d42f52d0b996de991a4b267338` |
| `AI_Patent_CPC_Text_Extension.zip` | `856d2c7c870e2cfe8e04cbf86760ce2494c4c768720fa993eb7c955d09d528cd` |

## Running the main analysis

Place `five_big_tech_ai_patents.csv` somewhere outside Git history and run:

```bash
python analysis/code/run_pipeline.py \
  --input /path/to/five_big_tech_ai_patents.csv \
  --output analysis/outputs
```

The source hash guard in the pipeline prevents the report narrative from being silently attached to a different extract.

## CPC/text enrichment

The extension is designed so its government metadata can be rebuilt from the fixed PatentsView release documented in `cpc_extension/README.md`.

```bash
cd cpc_extension
python run_pipeline.py --refresh-bulk
```

That refresh downloads the large government source tables, validates published checksums, and retains only the required patent metadata.

If you want to version the large local data files later, use Git LFS or an external release/data host rather than normal Git blobs.
