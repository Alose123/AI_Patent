"""Optional: reconstruct the supplied comparison frame from the prior clean dataset."""
import argparse
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("clean_dataset", help="Path to clean_patent_company.csv.gz from the initial analysis")
    parser.add_argument("--output",type=Path,default=ROOT/"data"/"cohort_frame.csv")
    args = parser.parse_args()
    d = pd.read_csv(args.clean_dataset, dtype={"doc_id": str, "appl_id": str, "patent_id":str}, float_precision="round_trip")
    year = pd.to_datetime(d.pub_dt).dt.year
    q = d.company.eq("Qualcomm") & year.isin([2021, 2023])
    n = d.company.eq("NVIDIA") & (year.between(2014, 2016) | year.between(2021, 2023))
    d = d.loc[q | n].copy()
    d["grant_year"] = pd.to_datetime(d.pub_dt).dt.year
    d["grant_quarter"] = pd.to_datetime(d.pub_dt).dt.quarter
    d["cohort"] = d.grant_year.astype(str)
    d.loc[d.company.eq("NVIDIA") & d.grant_year.le(2016), "cohort"] = "2014-2016"
    d.loc[d.company.eq("NVIDIA") & d.grant_year.ge(2021), "cohort"] = "2021-2023"
    # Reproduce the shipped frame's stable company order and textual-ID order.
    d["company_order"] = d.company.map({"Qualcomm":0,"NVIDIA":1})
    d = d.sort_values(["company_order","doc_id"],kind="stable")
    cols = ["doc_id", "appl_id", "pub_dt", "company", "cohort", "grant_year", "grant_quarter",
            "predict50_any_ai", "predict86_any_ai", "predict93_any_ai", "predict50_ml", "predict86_ml",
            "predict93_ml", "ai_score_ml", "predict86_vision", "predict86_hardware", "is_reissue"]
    d[cols].to_csv(args.output, index=False)