"""Exploratory composition accounting, interpretable text features, and robustness.

No fitted predictive classifier: CPC memberships and explicit text rules provide
independent descriptive evidence without predicting supplied AIPD labels.
"""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
COMMUNICATIONS = {"H04W", "H04L", "H04B", "H04J", "H04K", "H04M"}
# Explicit phrases. These are exploratory indicators, not validated technology labels.
RULES = {
    "sidelink": r"\bsidelink\b",
    "beam_or_beamforming": r"\bbeam(?:s|forming)?\b",
    "uplink": r"\buplink\b",
    "downlink": r"\bdownlink\b",
    "user_equipment": r"\buser equipment\b",
    "channel_state": r"\bchannel state\b",
    "harq": r"\bharq\b|\bhybrid automatic repeat request\b",
    "random_access": r"\brandom access\b",
    "new_radio_or_5g": r"\bnew radio\b|\b5g\b|\bfifth.generation\b",
    "wireless": r"\bwireless\b",
    "neural_network": r"\bneural(?: network)?s?\b",
    "explicit_machine_or_deep_learning": r"\bmachine learning\b|\bdeep learning\b",
    "explicit_learning_or_neural": r"\bneural(?: network)?s?\b|\bmachine learning\b|\bdeep learning\b",
    "autonomous": r"\bautonomous\b",
    "ray_tracing": r"\bray[ -]?trac\w*\b",
    "rendering": r"\brender\w*\b",
    "perception_and_geometry": r"\bobject detection\b|\bsemantic segmentation\b|\bpose estimation\b|\bdepth estimation\b|\bscene flow\b|\blane(?:s)?\b",
    "precision_or_acceleration": r"\baccelerator(?:s)?\b|\blower precision\b|\blow.precision\b|\bquantiz\w*\b|\btensor(?:s)?\b",
}
LABELS = {
    "H04W": "Wireless communication networks", "H04L": "Digital information transmission",
    "H04B": "Transmission", "H04J": "Multiplex communication", "H04M": "Telephony",
    "G06F": "Digital data processing", "G06T": "Image processing / generation",
    "G06V": "Image / video recognition", "G06N": "Specific computational models",
    "G05D": "Control / navigation", "B60W": "Vehicle drive control", "G09G": "Display control",
    "H04N": "Pictorial communication / video", "Y02D": "ICT climate-mitigation tags",
    "G01S": "Radar / navigation sensing", "H01L": "Semiconductors", "H10D": "Semiconductor devices",
}

def save(d, name):
    d.to_csv(TABLES / (name + ".csv"), index=False)
    return d

def frame_with_features():
    d = pd.read_csv(ROOT / "data" / "enriched_patent_cohorts.csv.gz", dtype={"doc_id": str, "appl_id": str, "application_id": str}, float_precision="round_trip")
    d["title_text"] = d.patent_title.fillna("").str.lower()
    d["abstract_text"] = d.patent_abstract.fillna("").str.lower()
    d["combined_text"] = d.title_text + " " + d.abstract_text
    d["filing_date_parsed"] = pd.to_datetime(d.filing_date, errors="coerce")
    d["filing_year"] = d.filing_date_parsed.dt.year
    d["grant_lag_years"] = (pd.to_datetime(d.pub_dt) - d.filing_date_parsed).dt.days / 365.25
    d["grant_period"] = pd.to_datetime(d.pub_dt).dt.to_period("Q").astype(str)
    for name, pattern in RULES.items():
        for scope in ["title", "combined"]:
            d[f"text_{scope}_{name}"] = d[f"{scope}_text"].str.contains(pattern, regex=True)
    for snapshot, column in [("current", "current_cpc_subclasses"), ("issue", "issue_cpc_subclasses")]:
        codes = d[column].fillna("").map(lambda x: set(filter(None, x.split("|"))))
        d[f"cpc_{snapshot}_communications"] = codes.map(lambda x: bool(x & COMMUNICATIONS))
        d[f"cpc_{snapshot}_wireless"] = codes.map(lambda x: "H04W" in x)
        d[f"cpc_{snapshot}_specific_models"] = codes.map(lambda x: "G06N" in x)
        d[f"cpc_{snapshot}_image_or_vision"] = codes.map(lambda x: bool(x & {"G06T", "G06V"}))
        d[f"cpc_{snapshot}_control_or_navigation"] = codes.map(lambda x: bool(x & {"G05D", "B60W", "G08G", "G01C"}))
        raw_name="current" if snapshot=="current" else "at_issue"
        raw=pd.read_csv(ROOT/"data"/(f"g_cpc_{raw_name}_subset.csv.gz"),dtype=str)
        old_recognition=set(raw.loc[raw.cpc_group.str.startswith("G06K9/"),"patent_id"])
        d[f"cpc_{snapshot}_harmonized_vision"] = d[f"cpc_{snapshot}_image_or_vision"] | d.doc_id.isin(old_recognition)
        inv_comm=set(raw.loc[raw.cpc_subclass.isin(COMMUNICATIONS)&raw.cpc_type.eq("inventional"),"patent_id"])
        d[f"cpc_{snapshot}_inventional_communications"] = d.doc_id.isin(inv_comm)
    d["application_id_normalized"] = d.application_id.fillna("").str.replace(r"[^0-9]", "", regex=True).str.lstrip("0")
    d["original_application_normalized"] = d.appl_id.str.replace(r"[^0-9]", "", regex=True).str.lstrip("0")
    d["application_id_agrees"] = d.application_id_normalized.eq(d.original_application_normalized)
    d.drop(columns=["title_text", "abstract_text", "combined_text", "filing_date_parsed"]).to_csv(ROOT / "data" / "analysis_patent_cohorts.csv.gz", index=False, compression="gzip")
    return d

def cpc_tables(d):
    rows = []
    groups = []
    for snapshot in ["current", "at_issue"]:
        c = pd.read_csv(ROOT / "data" / (f"g_cpc_{snapshot}_subset.csv.gz"), dtype=str)
        s = c[["patent_id", "cpc_subclass"]].drop_duplicates()
        s["fractional_credit"] = 1 / s.groupby("patent_id").patent_id.transform("size")
        s = s.merge(d[["doc_id", "company", "cohort", "predict86_any_ai", "predict86_ml"]], left_on="patent_id", right_on="doc_id", validate="many_to_one")
        for population in ["all", "non_ai", "ml"]:
            z = s if population == "all" else s.loc[s.predict86_any_ai.eq(0) if population == "non_ai" else s.predict86_ml.eq(1)]
            out = z.groupby(["company", "cohort", "cpc_subclass"]).agg(patents=("patent_id", "nunique"), fractional_credit=("fractional_credit", "sum")).reset_index()
            out["population"] = population
            out["snapshot"] = snapshot
            rows.append(out)
        gr = c[["patent_id", "cpc_group"]].drop_duplicates().merge(d[["doc_id", "company", "cohort", "predict86_any_ai", "predict86_ml"]], left_on="patent_id", right_on="doc_id")
        gr = gr.groupby(["company", "cohort", "cpc_group"]).agg(patents=("patent_id", "nunique"), ml_patents=("predict86_ml", "sum"), non_ai_patents=("predict86_any_ai", lambda x: (x == 0).sum())).reset_index()
        gr["snapshot"] = snapshot
        groups.append(gr)
    result = pd.concat(rows, ignore_index=True)
    result["label"] = result.cpc_subclass.map(LABELS).fillna(result.cpc_subclass)
    save(result, "cpc_subclass_counts")
    save(pd.concat(groups, ignore_index=True), "cpc_group_counts")
    return result

def text_tables(d):
    rows = []
    for (company, cohort), s in d.groupby(["company", "cohort"]):
        for population in ["all", "non_ai", "ml", "non_ml"]:
            if population == "all": z = s
            elif population == "non_ai": z = s.loc[s.predict86_any_ai.eq(0)]
            elif population == "ml": z = s.loc[s.predict86_ml.eq(1)]
            else: z = s.loc[s.predict86_ml.eq(0)]
            for scope in ["title", "combined"]:
                for theme in RULES:
                    count = int(z[f"text_{scope}_{theme}"].sum())
                    rows.append(dict(company=company, cohort=cohort, population=population, scope=scope, theme=theme, count=count, denominator=len(z), share=count/len(z)))
    save(pd.DataFrame(rows), "text_theme_counts")
    # Data-driven phrase contrasts complement the disclosed expert phrase rules.
    for company, population, early, late in [("Qualcomm", "non_ai", "2021", "2023"), ("NVIDIA", "all", "2014-2016", "2021-2023")]:
        z = d.loc[d.company.eq(company)].copy()
        if population == "non_ai": z = z.loc[z.predict86_any_ai.eq(0)]
        vectorizer = CountVectorizer(ngram_range=(2, 2), min_df=10, binary=True, stop_words="english", token_pattern=r"(?u)\b[a-z][a-z0-9-]+\b")
        matrix = vectorizer.fit_transform(z.combined_text)
        old = z.cohort.eq(early).to_numpy(); new = z.cohort.eq(late).to_numpy()
        a = np.asarray(matrix[old].sum(axis=0)).ravel(); b = np.asarray(matrix[new].sum(axis=0)).ravel()
        out = pd.DataFrame(dict(phrase=vectorizer.get_feature_names_out(), early_count=a, late_count=b, early_share=a/old.sum(), late_share=b/new.sum()))
        out["share_change_pp"] = 100 * (out.late_share-out.early_share)
        out["count_change"] = out.late_count-out.early_count
        save(out.sort_values("share_change_pp", ascending=False), company.lower() + "_phrase_contrasts")

def accounting_and_sensitivity(d):
    summaries = []
    for (company, cohort), s in d.groupby(["company", "cohort"]):
        summaries.append(dict(company=company,cohort=cohort,total=len(s), ai86=int(s.predict86_any_ai.sum()),non_ai86=int(s.predict86_any_ai.eq(0).sum()),ml86=int(s.predict86_ml.sum()),ml_share=s.predict86_ml.mean(),filing_median=s.filing_year.median(),lag_median=s.grant_lag_years.median()))
    save(pd.DataFrame(summaries), "cohort_summary")
    decompositions=[]
    for company,early,late,flag in [("Qualcomm","2021","2023","predict86_any_ai"),("NVIDIA","2014-2016","2021-2023","predict86_ml")]:
        z=d.loc[d.company.eq(company)]
        a=z.loc[z.cohort.eq(early)];b=z.loc[z.cohort.eq(late)]
        p0=int(a[flag].sum());p1=int(b[flag].sum());n0=len(a)-p0;n1=len(b)-p1
        share=lambda p,n:p/(p+n)
        positive=0.5*((share(p1,n0)-share(p0,n0))+(share(p1,n1)-share(p0,n1)))
        negative=0.5*((share(p0,n1)-share(p0,n0))+(share(p1,n1)-share(p1,n0)))
        total=share(p1,n1)-share(p0,n0)
        assert abs(positive+negative-total)<1e-12
        decompositions.append(dict(company=company,flag=flag,early_positive=p0,late_positive=p1,early_negative=n0,late_negative=n1,share_change_pp=100*total,positive_count_contribution_pp=100*positive,negative_count_contribution_pp=100*negative,method="Two-factor Shapley accounting: average both update orders; not a causal effect"))
    save(pd.DataFrame(decompositions),"share_change_accounting")
    sensitivity = []
    for threshold in [50,86,93]:
        q = d.loc[d.company.eq("Qualcomm") & d[f"predict{threshold}_any_ai"].eq(0)]
        for snapshot in ["current", "issue"]:
            early=q.loc[q.cohort.eq("2021")];late=q.loc[q.cohort.eq("2023")]
            for code_type in ["any","inventional"]:
                comm=f"cpc_{snapshot}_communications" if code_type=="any" else f"cpc_{snapshot}_inventional_communications"
                delta=len(late)-len(early)
                cdelta=int(late[comm].sum()-early[comm].sum())
                sensitivity.append(dict(company="Qualcomm",threshold=threshold,snapshot=snapshot,code_type=code_type,early_total=len(early),late_total=len(late),delta_total=delta,early_communications=int(early[comm].sum()),late_communications=int(late[comm].sum()),delta_communications=cdelta,communications_fraction_of_net_increase=cdelta/delta))
    save(pd.DataFrame(sensitivity), "qualcomm_growth_sensitivity")
    rows=[]
    for threshold in [50,86,93]:
        n=d.loc[d.company.eq("NVIDIA")]
        for co,s in n.groupby("cohort"):
            ml=s[f"predict{threshold}_ml"].eq(1)
            for feature in ["cpc_current_specific_models", "cpc_current_image_or_vision", "cpc_current_harmonized_vision", "cpc_issue_harmonized_vision", "cpc_issue_specific_models", "text_combined_explicit_learning_or_neural", "text_combined_autonomous", "text_combined_ray_tracing", "text_combined_rendering"]:
                rows.append(dict(cohort=co,threshold=threshold,feature=feature,total=len(s),ml_count=int(ml.sum()),feature_count=int(s[feature].sum()),ml_feature_overlap=int((ml & s[feature]).sum()),ml_share=float(ml.mean()),feature_share=float(s[feature].mean())))
    save(pd.DataFrame(rows), "nvidia_shift_sensitivity")
    n=d.loc[d.company.eq("NVIDIA")].copy()
    pairs=n.current_cpc_subclasses.fillna("").ne("") & n.issue_cpc_subclasses.fillna("").ne("")
    paired=[]
    for co,s in n.loc[pairs].groupby("cohort"):
        for snapshot in ["current","issue"]:
            for feature in ["specific_models","harmonized_vision","control_or_navigation"]:
                count=int(s[f"cpc_{snapshot}_{feature}"].sum())
                paired.append(dict(cohort=co,snapshot=snapshot,feature=feature,count=count,denominator=len(s),share=count/len(s),scope="Current and at-issue CPC both available; main analysis retains all grants"))
    save(pd.DataFrame(paired),"nvidia_paired_cpc_sensitivity")
    # Exact additive ML partition; intersection labels are ordered and nonoverlapping.
    neural=n.text_combined_explicit_learning_or_neural
    perception=n.cpc_current_image_or_vision | n.text_combined_perception_and_geometry | n.text_combined_autonomous
    n["ml_partition"] = np.select([n.predict86_ml.eq(0), neural, perception], ["Not ML86", "ML86 + explicit learning/neural text", "ML86 + vision/control evidence, no explicit learning text"], default="ML86 + other evidence")
    save(n.groupby(["cohort","ml_partition"]).size().rename("count").reset_index(), "nvidia_ml_additive_partition")
    q=d.loc[d.company.eq("Qualcomm") & d.predict86_any_ai.eq(0)].copy()
    q["communications_partition"] = np.where(q.cpc_current_communications,"Communications CPC present","No communications CPC")
    save(q.groupby(["cohort","communications_partition"]).size().rename("count").reset_index(),"qualcomm_non_ai_additive_partition")
    # More specific nonexclusive neural/ML evidence and technical component intersections.
    save(n.groupby("cohort").apply(lambda x: pd.Series({"explicit_learning":int(x.text_combined_explicit_learning_or_neural.sum()),"ml_and_explicit_learning":int((x.predict86_ml.eq(1)&x.text_combined_explicit_learning_or_neural).sum()),"neural":int(x.text_combined_neural_network.sum()),"autonomous":int(x.text_combined_autonomous.sum()),"ml_autonomous":int((x.predict86_ml.eq(1)&x.text_combined_autonomous).sum()),"ml_neural_autonomous":int((x.predict86_ml.eq(1)&x.text_combined_neural_network&x.text_combined_autonomous).sum())}),include_groups=False).reset_index(),"nvidia_key_intersections")
    # Leave-one-quarter-out ranges are sensitivity summaries, not confidence intervals.
    ranges=[]
    for company,early,late,feature,population in [("Qualcomm","2021","2023","text_combined_sidelink","non_ai"),("NVIDIA","2014-2016","2021-2023","text_combined_explicit_learning_or_neural","all")]:
        z=d.loc[d.company.eq(company)].copy()
        if population=="non_ai":z=z.loc[z.predict86_any_ai.eq(0)]
        values=[]
        for period in z.grant_period.unique():
            s=z.loc[z.grant_period.ne(period)]
            values.append(100*(s.loc[s.cohort.eq(late),feature].mean()-s.loc[s.cohort.eq(early),feature].mean()))
        ranges.append(dict(company=company,feature=feature,full_change_pp=100*(z.loc[z.cohort.eq(late),feature].mean()-z.loc[z.cohort.eq(early),feature].mean()),leave_one_quarter_min_pp=min(values),leave_one_quarter_max_pp=max(values)))
    save(pd.DataFrame(ranges),"leave_one_quarter_out")

def timing(d):
    q=d.loc[d.company.eq("Qualcomm") & d.predict86_any_ai.eq(0)].copy()
    invalid=q.grant_lag_years.isna() | q.grant_lag_years.lt(0) | q.grant_lag_years.gt(30)
    save(q.loc[invalid,["doc_id","cohort","filing_date","pub_dt","grant_lag_years"]],"timing_anomalies")
    save(q.groupby(["cohort","filing_year"]).size().rename("count").reset_index(),"qualcomm_non_ai_filing_cohorts")
    save(q.groupby("cohort").grant_lag_years.agg(["count","median","mean","min","max"]).reset_index(),"qualcomm_grant_lag")
    save(q.groupby(["cohort","grant_quarter"]).size().rename("count").reset_index(),"qualcomm_non_ai_quarters")
    save(d.groupby(["company","cohort"]).application_id_agrees.agg(["sum","count"]).reset_index(),"application_id_internal_check")

def illustrative_records(d):
    definitions = [("Qualcomm","2023","sidelink",None),("Qualcomm","2023","beam_or_beamforming",None),("NVIDIA","2021-2023","neural_network",1),("NVIDIA","2021-2023","autonomous",1),("NVIDIA","2021-2023","ray_tracing",0),("NVIDIA","2021-2023","precision_or_acceleration",1)]
    selected=[]
    for company,cohort,theme,ml in definitions:
        s=d.loc[d.company.eq(company)&d.cohort.eq(cohort)&d[f"text_combined_{theme}"]].copy()
        if company=="Qualcomm":s=s.loc[s.predict86_any_ai.eq(0)]
        if ml is not None:s=s.loc[s.predict86_ml.eq(ml)]
        # Prefer a title match so the connection is visible; then lowest numeric patent ID.
        s=s.sort_values([f"text_title_{theme}","doc_id"],ascending=[False,True])
        x=s.iloc[0]
        selected.append(dict(theme=theme,company=company,doc_id=x.doc_id,title=x.patent_title,abstract=x.patent_abstract,date=x.pub_dt,current_cpc=x.current_cpc_subclasses,ai86=x.predict86_any_ai,ml86=x.predict86_ml,url=f"https://patents.google.com/patent/US{x.doc_id}{x.wipo_kind}/en"))
    save(pd.DataFrame(selected),"illustrative_patents")
    # All discordances are retained for review rather than relabeled or deleted.
    n=d.loc[d.company.eq("NVIDIA") & d.cohort.eq("2021-2023")]
    discord=n.loc[n.text_combined_explicit_learning_or_neural & n.predict86_ml.eq(0),["doc_id","patent_title","ai_score_ml","predict50_ml","predict86_ml","predict93_ml","current_cpc_subclasses"]]
    save(discord,"nvidia_explicit_learning_below_ml86")
    save(d.loc[d.current_cpc_subclasses.fillna("").eq(""),["doc_id","company","cohort","patent_title","is_reissue"]],"patents_without_current_cpc")
    accelerator = d.loc[d.patent_title.eq("Sparse convolutional neural network accelerator"),["doc_id","patent_title","patent_abstract","filing_date","pub_dt","ai_score_ml","predict86_ml","predict86_any_ai","predict86_hardware","current_cpc_subclasses"]]
    save(accelerator,"accelerator_classifier_anomaly")
    a=accelerator.set_index("doc_id")
    assert a.loc["10891538","patent_abstract"] == a.loc["11847550","patent_abstract"]

if __name__ == "__main__":
    TABLES.mkdir(parents=True,exist_ok=True)
    d=frame_with_features()
    cpc_tables(d)
    text_tables(d)
    accounting_and_sensitivity(d)
    timing(d)
    illustrative_records(d)
    (ROOT/"data"/"text_rules.json").write_text(json.dumps({"rules":RULES,"note":"Exploratory; literal title/abstract indicators; overlapping; not ground truth."},indent=2)+"\n")
    print("Technology tables and enriched analysis dataset written.")