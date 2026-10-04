"""Meaningful data/conservation checks, data dictionary, and a self-contained archive."""
from pathlib import Path
import csv
import hashlib
import json
import zipfile
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs"

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(4*1024**2),b""):h.update(block)
    return h.hexdigest()

def verify():
    checks=[]
    source=pd.read_csv(ROOT/"data"/"cohort_frame.csv",dtype={"doc_id":str,"appl_id":str},float_precision="round_trip")
    d=pd.read_csv(ROOT/"data"/"analysis_patent_cohorts.csv.gz",dtype={"doc_id":str,"appl_id":str,"application_id":str},float_precision="round_trip")
    pd.testing.assert_frame_equal(source,d[source.columns],check_dtype=False,check_exact=True)
    assert d.doc_id.is_unique and len(d)==7813
    checks.append("All selected original fields and all 7,813 rows exactly preserved in the enriched analysis dataset.")
    assert pd.to_datetime(d.pub_dt).equals(pd.to_datetime(d.patent_date))
    assert d.application_id_agrees.all()
    checks.append("Dates and normalized application identifiers exactly agree with the official metadata.")
    for threshold in [50,86,93]:
        assert d[f"predict{threshold}_ml"].eq(d.ai_score_ml.ge(threshold/100).astype(int)).all()
    assert d.ai_score_ml.between(0,1).all()
    assert (d.predict50_any_ai>=d.predict86_any_ai).all() and (d.predict86_any_ai>=d.predict93_any_ai).all()
    checks.append("Retained ML flags agree with original scores and cutoff definitions; any-AI flags are nested.")
    assert d.patent_title.notna().all() and d.patent_abstract.notna().all() and d.filing_date.notna().all()
    assert d.grant_lag_years.notna().all() and d.grant_lag_years.ge(0).all()
    missing=d.current_cpc_subclasses.fillna("").eq("")
    assert missing.sum()==6 and d.loc[missing,"is_reissue"].eq(1).all()
    checks.append("No missing title/abstract/filing dates or invalid lags; six current-CPC absences are retained reissues.")
    c=pd.read_csv(OUT/"tables"/"cpc_subclass_counts.csv")
    for snapshot,column in [("current","current_cpc_subclasses"),("at_issue","issue_cpc_subclasses")]:
        for (company,cohort),s in d.groupby(["company","cohort"]):
            for population in ["all","non_ai","ml"]:
                z=s if population=="all" else s.loc[s.predict86_any_ai.eq(0) if population=="non_ai" else s.predict86_ml.eq(1)]
                expected=z[column].fillna("").ne("").sum()
                actual=c.loc[(c.company==company)&(c.cohort==cohort)&(c.population==population)&(c.snapshot==snapshot),"fractional_credit"].sum()
                assert np.isclose(actual,expected,atol=1e-8)
    checks.append("Fractional CPC credits conserve classified-patent totals in every cohort, population and snapshot.")
    for name,company,col in [("qualcomm_non_ai_additive_partition","Qualcomm","predict86_any_ai"),("nvidia_ml_additive_partition","NVIDIA","predict86_ml")]:
        p=pd.read_csv(OUT/"tables"/(name+".csv"))
        for co,s in d.loc[d.company.eq(company)].groupby("cohort"):
            expected=s[col].eq(0).sum() if company=="Qualcomm" else len(s)
            assert p.loc[p.cohort.astype(str).eq(co),"count"].sum()==expected
    a=pd.read_csv(OUT/"tables"/"share_change_accounting.csv")
    assert np.allclose(a.positive_count_contribution_pp+a.negative_count_contribution_pp,a.share_change_pp)
    checks.append("Additive technology partitions and two-factor share decompositions reconcile exactly.")
    pairs=pd.read_csv(OUT/"tables"/"nvidia_paired_cpc_sensitivity.csv")
    assert set(pairs.denominator)=={742,784}
    checks.append("At-issue sensitivity excludes only recorded missing-snapshot cases; main cohorts retain all observations.")
    report=(OUT/"technology_report.html").read_text()
    assert report.count('src="data:image/png;base64,')==6
    assert "company/merge-completeness" not in report and "various examples" not in report
    checks.append("Focused HTML contains six embedded figures and no company/merge-completeness section.")
    provenance=json.loads((ROOT/"data"/"cohort_provenance.json").read_text())
    assert sha(ROOT/"data"/"cohort_frame.csv")==provenance["cohort_frame_sha256"]
    case=json.loads((ROOT/"data"/"case_study_manifest.json").read_text())
    assert sha(ROOT/"data"/"US11847550.pdf")==case["sha256"]
    checks.append("Cohort source and manually reviewed primary patent PDF hashes unchanged.")
    (OUT/"verification.json").write_text(json.dumps({"status":"passed","checks":checks},indent=2)+"\n")
    return d,checks

def dictionary(d):
    records=[]
    definitions={"doc_id":"Original USPTO grant identifier; kept as text, including RE prefixes.","appl_id":"Original application identifier; kept as text.","pub_dt":"Original grant-publication date, not first pre-grant publication or innovation date.","company":"Original company label.","cohort":"Comparison period; Qualcomm single-year, NVIDIA equal three-year periods.","grant_year":"Year of original grant publication.","grant_quarter":"Quarter-of-year, 1–4.","is_reissue":"Original RE indicator; no reissue observations deleted.","ai_score_ml":"Supplied AIPD ML classification score; not a validated probability of technical truth.","patent_title":"Official PatentsView title.","patent_abstract":"Official PatentsView grant abstract; not full claims/specification.","filing_date":"Direct application filing date; not earliest patent-family priority.","filing_year":"Year of direct application filing.","grant_lag_years":"(Grant date minus direct filing date)/365.25.","current_cpc_subclasses":"Unique sorted pipe-separated CPC subclasses in December 2024 snapshot; empty means unavailable.","issue_cpc_subclasses":"Unique sorted pipe-separated CPC subclasses at grant; empty means unavailable.","grant_period":"Year-quarter for influence checks.","application_id_agrees":"Internal normalized application-ID agreement; not a company coverage measure."}
    rules=json.loads((ROOT/"data"/"text_rules.json").read_text())["rules"]
    for col in d.columns:
        description=definitions.get(col,"Official metadata or derived internal field; see stage code for exact derivation.")
        if col.startswith("predict"):
            description="Original supplied AIPD binary flag at the named cutoff/component. The 86 cutoff is a score threshold, not 86% precision."
        elif col.startswith("text_"):
            scope="combined title and abstract" if col.startswith("text_combined_") else "title only"
            theme=col.removeprefix("text_combined_").removeprefix("text_title_")
            description=f"Exploratory literal-rule match in {scope}; regex: {rules.get(theme,'see text_rules.json')}. Themes overlap, not ground-truth labels."
        elif col.startswith("cpc_"):
            description="Derived patent-level CPC membership. Communications: H04W/L/B/J/K/M; image/vision: G06T/V; harmonized vision adds legacy G06K9/ groups; control/navigation: G05D/B60W/G08G/G01C. Inventional-only columns restrict CPC type. Missing CPC yields False, interpreted with missing-code columns, not as technology absence."
        records.append(dict(column=col,dtype=str(d[col].dtype),description=description))
    pd.DataFrame(records).to_csv(ROOT/"data"/"data_dictionary.csv",index=False)

def package():
    included=[p for p in sorted(ROOT.rglob("*")) if p.is_file() and "cache" not in p.parts and "__pycache__" not in p.parts and p.suffix!=".pyc" and p.name not in ["file_manifest.json"] and not p.name.endswith("_text.txt")]
    manifest={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in included}
    (ROOT/"file_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    archive=ROOT.parent/"AI_Patent_CPC_Text_Extension.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in included+[ROOT/"file_manifest.json"]:z.write(p,arcname="cpc_extension/"+str(p.relative_to(ROOT)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for path,record in manifest.items():assert hashlib.sha256(z.read("cpc_extension/"+path)).hexdigest()==record["sha256"]
    print(f"Archive verified: {archive.name}, {archive.stat().st_size:,} bytes, {len(included)+1} files.")

if __name__=="__main__":
    d,checks=verify();dictionary(d);package();print(f"{len(checks)} conservation and provenance checks passed.")