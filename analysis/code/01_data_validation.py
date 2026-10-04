"""Audit the supplied extract, never infer source merge recall from matched rows."""
from common import *

def main():
    args = setup(); out = args.output
    (out/'research_log.jsonl').write_text('', encoding='utf-8')
    d = read_source(args.input)
    required = set(DOC_COLS + ['patent_id','company','assignee_id','assignee_sequence',
                               'disambig_assignee_organization','assignee_type','location_id'])
    absent = required-set(d.columns)
    if absent: raise ValueError(f'Missing required columns: {sorted(absent)}')
    dates = pd.to_datetime(d.pub_dt, errors='coerce', format='%Y-%m-%d')
    checks = {
        'missing_required_identity': int(d[['doc_id','patent_id','appl_id','company','assignee_id']].isna().any(axis=1).sum()),
        'doc_patent_id_mismatch': int((d.doc_id != d.patent_id).fillna(True).sum()),
        'malformed_patent_id': int((~d.doc_id.str.fullmatch(r'(?:[0-9]{7,8}|RE[0-9]{5})')).fillna(True).sum()),
        'malformed_application_id': int((~d.appl_id.str.fullmatch(r'[0-9]{8}')).fillna(True).sum()),
        'unparsable_date': int(dates.isna().sum()),
        'unexpected_company': int((~d.company.isin(COMPANIES)).sum()),
        'unexpected_document_type': int((d.flag_patent != 1).sum()),
        'exact_duplicate_rows': int(d.duplicated().sum()),
        'duplicate_patent_company_rows': int(d.duplicated(['patent_id','company']).sum()),
        'duplicate_patent_assignee_sequence': int(d.duplicated(['patent_id','assignee_sequence']).sum()),
        'assignee_id_multiple_company_labels': int((d.groupby('assignee_id').company.nunique()>1).sum()),
        'negative_assignee_sequence': int((d.assignee_sequence<0).sum()),
        'nonintegral_assignee_sequence': int((d.assignee_sequence%1!=0).sum())
    }
    duplicate_docs = d[d.duplicated('doc_id', keep=False)]
    conflicts = duplicate_docs.groupby('doc_id')[DOC_COLS[1:]].nunique(dropna=False)
    checks['shared_document_metadata_conflicts'] = int(conflicts.gt(1).any(axis=1).sum())
    thresholds = []
    for t in THRESHOLDS:
        flags = d[[f'predict{t}_{k}' for k in COMPONENTS]]
        for k in COMPONENTS:
            s = d[f'ai_score_{k}']; f = d[f'predict{t}_{k}']
            thresholds.append(dict(threshold=t, component=k,
                invalid_flags=int((~f.isin([0,1])).sum()),
                missing_scores=int(s.isna().sum()), invalid_scores=int((~s.between(0,1)).sum()),
                threshold_mismatches=int((f != s.ge(t/100).astype(int)).sum()),
                largest_negative_score=s[f==0].max(), smallest_positive_score=s[f==1].min()))
        checks[f'any_ai_or_mismatch_{t}'] = int((d[f'predict{t}_any_ai'] != flags.max(axis=1)).sum())
        checks[f'any_ai_invalid_flag_{t}'] = int((~d[f'predict{t}_any_ai'].isin([0,1])).sum())
    for k in ['any_ai']+COMPONENTS:
        checks[f'non_nested_thresholds_{k}'] = int(((d[f'predict93_{k}']>d[f'predict86_{k}'])|
                                                   (d[f'predict86_{k}']>d[f'predict50_{k}'])).sum())
    audit = dict(source_name=args.input.name, source_sha256=sha256(args.input),
                 source_bytes=args.input.stat().st_size, rows=len(d), columns=len(d.columns),
                 unique_patents=d.patent_id.nunique(), unique_applications=d.appl_id.nunique(),
                 date_min=d.pub_dt.min(), date_max=d.pub_dt.max(),
                 reissue_rows=int(d.doc_id.str.startswith('RE').sum()),
                 shared_between_selected_companies=int((d.groupby('doc_id').company.nunique()>1).sum()),
                 date_weekdays=dates.dt.day_name().value_counts().to_dict(), checks=checks,
                 environment=environment(), merge_recall='Not identifiable from a matched extract alone',
                 population='Observed patent-company memberships for the supplied assignee entities')
    dump_json(audit, out/'audit.json')
    save_table(pd.DataFrame(thresholds), out, 'classification_validation')
    save_table(pd.DataFrame({'column':d.columns,'dtype':d.dtypes.astype(str).values,
                            'missing':d.isna().sum().values,
                            'missing_pct':100*d.isna().mean().values}), out, 'schema_missingness')
    save_table(duplicate_docs, out, 'shared_patent_records')
    company = d.assign(year=dates.dt.year).groupby('company').agg(
        rows=('doc_id','size'), unique_patents=('doc_id','nunique'), first_date=('pub_dt','min'),
        last_date=('pub_dt','max'), assignee_ids=('assignee_id','nunique'),
        missing_location=('location_id',lambda x:x.isna().sum()))
    save_table(company.reset_index(), out, 'company_coverage')
    d['year']=dates.dt.year; d['month']=dates.dt.month
    save_table(d.groupby(['company','year']).size().rename('n').reset_index(),out,'coverage_company_year')
    save_table(d.groupby(['company','year','month']).size().rename('n').reset_index(),out,'coverage_company_month')
    save_table(d.groupby(['company','disambig_assignee_organization','assignee_id','year']).size().rename('n').reset_index(),out,'assignee_year')
    save_table(d[d.location_id.isna()].groupby(['company','year']).size().rename('missing_locations').reset_index(),out,'missing_location_by_year')
    save_table(pd.DataFrame([{'check':k,'failures':v} for k,v in checks.items()]),out,'integrity_checks')
    failures = sum(checks.values()) + sum(r['invalid_flags']+r['invalid_scores']+r['threshold_mismatches'] for r in thresholds)
    log(out,'01','271k-scale extract contains both AI and non-AI granted documents.',
        'Matched company portfolios may permit an AI share denominator.',
        'Validate keys, flag-score rules, dates, and assignee mappings before deriving features.',
        'Loading successfully is insufficient; denominator coverage and one-to-many joins are separate concerns.',
        f'{len(d):,} rows; {audit["unique_patents"]:,} patents; {failures} hard integrity failures.',
        'Cannot calculate unmatched rates or corporate-group completeness without upstream inputs and merge code.')
    log(out,'01','A patent has IBM and Microsoft assignee records; RE identifiers appear.',
        'Repeated document and nonnumeric IDs may be legitimate rather than corrupt.',
        'Retain shared memberships and valid reissues; check document metadata consistency.',
        'Blind patent-ID deduplication would remove an ownership observation; removing RE would discard valid grants.',
        f'{audit["shared_between_selected_companies"]} shared patent; {audit["reissue_rows"]} reissue rows.',
        'Parent patents and full co-assignee lists are unavailable; within-sample fractional weights are not full ownership fractions.')
    log(out,'01','USPTO corrected an earlier predict93 threshold issue in January 2025.',
        'This extract might contain the older 89.93% cutoff.',
        'Compare every supplied flag with the score-based 50%, 86%, and 93% cutoffs.',
        'A version anomaly can be diagnosed internally without replacing the dataset.',
        f'Total threshold disagreements: {sum(r["threshold_mismatches"] for r in thresholds)}.',
        'Passing rules does not authenticate the source release or assess classification accuracy.')
    if failures: raise ValueError('Audit found hard integrity failures; inspect audit.json before proceeding.')
    print(f'Audit passed: {len(d):,} rows, {d.doc_id.nunique():,} documents.')

if __name__=='__main__': main()