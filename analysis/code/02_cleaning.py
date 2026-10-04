"""Preserve every source row/column and add explicitly defined variables."""
from common import *

def main():
    args=setup(); out=args.output; d=read_source(args.input)
    audit=json.loads((out/'audit.json').read_text())
    if sha256(args.input)!=audit['source_sha256']: raise ValueError('Source changed after audit')
    d.insert(0,'source_row_number',np.arange(2,len(d)+2)) # CSV header is line 1
    dt=pd.to_datetime(d.pub_dt,format='%Y-%m-%d')
    d['grant_year']=dt.dt.year; d['grant_quarter']=dt.dt.quarter
    d['grant_month']=dt.dt.month
    d['is_reissue']=d.doc_id.str.startswith('RE').astype('int8')
    d['n_included_companies']=d.groupby('doc_id').company.transform('nunique')
    d['shared_between_included_companies']=(d.n_included_companies>1).astype('int8')
    d['within_sample_fraction']=1/d.n_included_companies
    d['analysis_2010_2023']=d.grant_year.between(2010,2023).astype('int8')
    d['recent_2021_2023']=d.grant_year.between(2021,2023).astype('int8')
    d['max_ai_score']=d[[f'ai_score_{c}' for c in COMPONENTS]].max(axis=1)
    d['score_borderline_86']=(abs(d.max_ai_score-.86)<=.05).astype('int8')
    features=[]
    def feature(name,definition): features.append({'variable':name,'definition':definition})
    for t in THRESHOLDS:
        cols=[f'predict{t}_{c}' for c in COMPONENTS]
        d[f'n_components{t}']=d[cols].sum(axis=1).astype('int8')
        d[f'nonhardware{t}']=d[[f'predict{t}_{c}' for c in COMPONENTS if c!='hardware']].max(axis=1).astype('int8')
        d[f'hardware_only{t}']=((d[f'predict{t}_hardware']==1)&(d[f'nonhardware{t}']==0)).astype('int8')
        feature(f'n_components{t}',f'Number of the eight component flags positive at {t}% score cutoff; 0 to 8.')
        feature(f'nonhardware{t}',f'At least one of seven components other than AI hardware at {t}%; robustness definition, not a superior AI ground truth.')
        feature(f'hardware_only{t}',f'AI hardware positive at {t}%, with none of seven other components positive.')
    for name,definition in [
        ('source_row_number','Original CSV data line number, starting at 2; original order retained.'),
        ('grant_year','Calendar year from pub_dt; all flag_patent values are 1, so this is grant/issue year.'),
        ('grant_quarter','Calendar quarter from pub_dt.'),('grant_month','Calendar month from pub_dt.'),
        ('is_reissue','1 for document IDs beginning RE; these are valid patents and retained.'),
        ('n_included_companies','Number of distinct supplied company labels for this document.'),
        ('shared_between_included_companies','1 if more than one of the five selected company labels occurs.'),
        ('within_sample_fraction','1/n_included_companies; sums to one per document across selected firms, not true ownership share.'),
        ('analysis_2010_2023','Main time-trend eligibility; every company has at least 100 records per year in this window.'),
        ('recent_2021_2023','Recent three-year technology-profile window.'),
        ('max_ai_score','Maximum of eight model scores; a diagnostic, not a calibrated probability of any AI.'),
        ('score_borderline_86','Maximum score within +/-0.05 of 0.86; threshold sensitivity review flag, not an exclusion.')]:
        feature(name,definition)
    # No imputations, source-value changes, reissue removals, or company-level deduplication.
    d.to_csv(out/'clean_patent_company.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    save_table(pd.DataFrame(features),out,'derived_variable_dictionary')
    exclusions=pd.DataFrame([
        {'analysis':'clean dataset and full-history EDA','reason':'none','rows_excluded':0,'rows_retained':len(d)},
        {'analysis':'main annual trends and equal-year comparison','reason':'outside calendar grant years 2010-2023','rows_excluded':int((d.analysis_2010_2023==0).sum()),'rows_retained':int(d.analysis_2010_2023.sum())},
        {'analysis':'recent technology profile and co-occurrence','reason':'outside grant years 2021-2023','rows_excluded':int((d.recent_2021_2023==0).sum()),'rows_retained':int(d.recent_2021_2023.sum())},
        {'analysis':'no-reissue sensitivity only','reason':'valid RE patents omitted as a sensitivity','rows_excluded':int(d.is_reissue.sum()),'rows_retained':int((d.is_reissue==0).sum())},
        {'analysis':'pooled unique document summary only','reason':'collapse co-assignee memberships to a single consistent document, retain both in main dataset','rows_excluded':len(d)-d.doc_id.nunique(),'rows_retained':d.doc_id.nunique()}])
    save_table(exclusions,out,'analysis_scope_ledger')
    log(out,'02','Only location_id has missing values; no core outcome/identity missingness.',
        'Geographic missingness need not invalidate company/time analysis.',
        'Do not impute locations or delete their rows; keep all rows and source values.',
        'Location is not required for the selected research estimands; dropping rows creates avoidable selection.',
        f'{len(d):,} rows retained, {len(d.columns)} columns including derived features.',
        'Geographic analysis would require location joins and a separate missingness assessment.')
    log(out,'02','Earliest company records and small annual volumes differ substantially.',
        'Lifetime pooling may confuse company age and portfolio composition with company differences.',
        'Use 2010-2023 annual shares as main comparison, retain full history for coverage EDA.',
        'All five have >=100 documents each year in this window; alternative 2009-2023 or 2014-2023 windows are possible.',
        f'{int(d.analysis_2010_2023.sum()):,} patent-company records in main period.',
        'This is an observed-coverage choice, not evidence that the corporate portfolios are complete.')
    log(out,'02','Classifier supplies eight overlapping technology labels.',
        'A broad any-AI trend could be driven by hardware alone or by multiple technology areas.',
        'Derive nonhardware, hardware-only, component-count and threshold-borderline diagnostics.',
        'These preserve multilabel structure; mutually exclusive categories would discard overlap.',
        'Features defined in derived_variable_dictionary.csv; original flags unchanged.',
        'Knowledge processing/planning/hardware remain broad historical classifier categories; these are not generative-AI labels.')
    print(f'Derived dataset written with all {len(d):,} source rows.')

if __name__=='__main__': main()