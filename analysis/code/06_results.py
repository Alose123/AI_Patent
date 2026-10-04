"""Reconcile results, preserve source values, and generate standalone reports."""
from common import *
import base64
import html

SOURCE_URLS={
    'USPTO dataset and release notes':'https://www.uspto.gov/ip-policy/economic-research/research-datasets/artificial-intelligence-patent-dataset',
    'USPTO AIPD 2023 methodology, especially appendices D–E':'https://www.uspto.gov/sites/default/files/documents/oce-aipd-2023.pdf',
    'IBM Research, How do you measure innovation?, 9 January 2023':'https://research.ibm.com/blog/Ibm-innovation-2022',
    'Original patent US7355601, front page and continuation/text disclosures':'https://patentimages.storage.googleapis.com/0b/8e/3c/ca176069e305fb/US7355601.pdf'}

def fmt_pct(x):return f'{100*x:.1f}%'
def md_table(d):
    cols=[str(c) for c in d.columns]
    def escape(v):return str(v).replace('|','\\|').replace('\n',' ')
    lines=['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
    for row in d.itertuples(index=False,name=None):lines.append('| '+' | '.join(escape(v) for v in row)+' |')
    return '\n'.join(lines)

class Report:
    def __init__(self,title,out):
        self.title=title;self.out=out;self.md=[];self.htm=[]
        self.heading(title,1)
    def heading(self,text,level=2):
        self.md.append('#'*level+' '+text)
        self.htm.append(f'<h{level}>{html.escape(text)}</h{level}>')
    def p(self,text):
        self.md.append(text);self.htm.append('<p>'+html.escape(text)+'</p>')
    def bullets(self,items):
        self.md.append('\n'.join('- '+x for x in items))
        self.htm.append('<ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in items)+'</ul>')
    def table(self,d):
        self.md.append(md_table(d));self.htm.append('<div class="table-wrap">'+d.to_html(index=False,escape=True,border=0)+'</div>')
    def fig(self,name,caption):
        self.md.append(f'![{caption}](figures/{name}.png)\n\n{caption}')
        encoded=base64.b64encode((self.out/'figures'/f'{name}.png').read_bytes()).decode()
        self.htm.append(f'<figure><img src="data:image/png;base64,{encoded}" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}</figcaption></figure>')
    def code(self,text):
        self.md.append('```bash\n'+text+'\n```');self.htm.append('<pre><code>'+html.escape(text)+'</code></pre>')
    def links(self,links):
        self.md.append('\n'.join(f'- [{name}]({url})' for name,url in links.items()))
        self.htm.append('<ul>'+''.join(f'<li><a href="{html.escape(url)}">{html.escape(name)}</a></li>' for name,url in links.items())+'</ul>')
    def write(self,stem,standalone_html=False):
        (self.out/(stem+'.md')).write_text('\n\n'.join(self.md)+'\n',encoding='utf-8')
        if standalone_html:
            css='''body{margin:0;background:#edf1f5;color:#182b43;font-family:system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.65}main{max-width:1120px;margin:36px auto;background:white;padding:48px 56px;border-radius:12px;box-shadow:0 4px 28px #162b4310}h1{font-size:38px;line-height:1.2;letter-spacing:-.8px;margin-top:0}h2{font-size:25px;color:#245b91;margin-top:48px;border-top:1px solid #dae3eb;padding-top:20px}h3{font-size:18px}p,li{font-size:15px}.table-wrap{overflow:auto;margin:24px 0}table{border-collapse:collapse;width:100%;font-size:13px}th{background:#213f60;color:white;text-align:left;padding:10px}td{padding:9px;border-bottom:1px solid #e1e8ef}tr:nth-child(even){background:#f5f8fb}figure{margin:30px -20px}img{width:100%;height:auto}figcaption{color:#576579;font-size:13px;padding:8px 20px}a{color:#245b91}pre{overflow:auto;padding:18px;background:#f1f5f8;border-radius:8px;font-size:13px}footer{margin-top:38px;color:#66758a;font-size:13px}@media(max-width:700px){main{padding:24px 18px;margin:0;border-radius:0}h1{font-size:28px}figure{margin:24px 0}td,th{font-size:12px;padding:7px}}@media print{body{background:white}main{box-shadow:none;margin:0;padding:16px}figure,table{break-inside:avoid}h2{break-after:avoid}}'''
            page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+html.escape(self.title)+'</title><style>'+css+'</style></head><body><main>'+''.join(self.htm)+'<footer>Independent exploratory analysis • source data preserved • all substantive estimates are conditional on this extract.</footer></main></body></html>'
            (self.out/(stem+'.html')).write_text(page,encoding='utf-8')

def main():
    args=setup();out=args.output
    if sha256(args.input)!=REFERENCE_SOURCE_SHA256:
        raise ValueError('Reference-specific report requires the supplied source file. Adapt the report builder for a new extract.')
    source=read_source(args.input);clean=read_clean(out)
    audit=json.loads((out/'audit.json').read_text());es=json.loads((out/'eda_summary.json').read_text())
    def table(name):return pd.read_csv(out/'tables'/f'{name}.csv')
    annual=table('annual_company_metrics');period=table('period_comparison')
    primary=table('primary_annual_trends');robust=table('trend_robustness');diagnostics=table('model_diagnostics')
    decomp=table('count_share_decomposition');coverage=table('company_coverage')
    # Meaningful conservation checks for this analysis rather than implementation-mirroring tests.
    pd.testing.assert_frame_equal(clean[source.columns],source,check_dtype=False,check_exact=True)
    assert sha256(args.input)==audit['source_sha256'],'Source bytes changed'
    assert annual.total_patents.sum()==len(source),'Annual denominators do not reconcile'
    for t in THRESHOLDS:
        assert annual[f'predict{t}_any_ai'].sum()==source[f'predict{t}_any_ai'].sum()
        assert np.array_equal(clean[f'predict{t}_any_ai'],clean[f'nonhardware{t}']+clean[f'hardware_only{t}'])
    assert np.allclose(decomp.reconciliation_error,0,atol=1e-8)
    assert clean.groupby('doc_id').within_sample_fraction.sum().eq(1).all()
    assert len(primary)==10 and primary.n_years.eq(14).all()
    assert annual[annual.year.between(2010,2023)].groupby('company').size().eq(14).all()
    checks=dict(source_bytes_unchanged=True,all_source_rows_columns_values_preserved=True,
        annual_denominators_reconciled=True,all_threshold_counts_reconciled=True,
        nonhardware_hardware_partition_reconciled=True,count_decomposition_reconciled=True,
        within_sample_fraction_conserves_documents=True,ten_primary_tests_have_14_years=True)
    dump_json(checks,out/'verification.json')
    case=clean[clean.doc_id.isin(['7355601','6862027'])][['doc_id','appl_id','pub_dt','company','ai_score_hardware','predict86_any_ai']].copy()
    case['external_review']='Patent US7355601 front page confirms IBM/Microsoft assignees and a continuation chain to US6862027; retained as documents.'
    save_table(case,out,'externally_reviewed_patent_case')
    log(out,'06','The original US7355601 patent lists both companies and a continuation chain to US6862027.',
        'The shared row is legitimate, and unique application IDs may still represent related patent documents.',
        'Verify the original patent front page and text; retain all observed grants and their labels.',
        'A document-level anomaly can be investigated with a targeted primary record instead of deleting duplicate IDs.',
        'Co-assignment is corroborated; the related Microsoft document appears under another application number. Case rows exported.',
        'No complete family reconstruction or human AI ground truth is supplied; broad graphics hardware may be classified as AI hardware.')
    log(out,'06','Deliverables must reconcile with the source and with each other.',
        'A coding or serialization error could alter conclusions despite passing the first audit.',
        'Check all original values exactly after round-trip parsing, source hash, aggregate counts, partitions and decomposition.',
        'These directly validate conservation and provenance; no extra modelling or significance search is needed.',
        'All checks passed; primary OLS slopes also independently matched scipy in stage 04.',
        'Internal consistency does not prove upstream completeness or real-world AI classification accuracy.')
    q=Report('Data-quality report: five-company patent extract',out)
    q.p(f'Audit outcome: no hard internal integrity failures. The source contains {len(source):,} rows, {audit["columns"]} columns and {audit["unique_patents"]:,} distinct granted patent documents. No rows are excluded from the derived master dataset. This is a conditional pass for internal structure; source-level merge recall and corporate-group coverage cannot be established.')
    q.table(pd.DataFrame([
        ('Document/patent key equality','0 mismatches'),('Identifier syntax','All IDs valid; 143 valid RE reissues'),
        ('Application identifiers','All 8-character strings; leading zeros preserved'),
        ('Exact duplicate rows','0'),('Duplicate patent-company memberships','0'),
        ('Shared patent','7355601, IBM and Microsoft; document metadata identical'),
        ('AI classification rules','All 24 component/cutoff checks pass; all 3 any-AI OR checks pass'),
        ('Score range / nested flags','All scores within [0,1]; all flags binary and nested'),
        ('Missing values','Only location_id: 230 rows (0.0847%); no imputation'),
        ('Publication dates','1976-01-06 through 2023-12-26; all Tuesday grants'),
        ('Comparable window','2010-2023: 14 years per company, >=156 grants/year, all 12 months observed'),
        ('Unmatched source records','Not observable; no upstream tables or merge manifest supplied'),
        ('Assignee coverage','10 observed IDs; Google has 1, the other firms have 2 or 3')],columns=['Check','Result']))
    q.heading('Observed company coverage');q.table(coverage)
    q.p('Assignee names are disambiguated entity names. Google has one supplied GOOGLE LLC ID, and Microsoft has two major IDs with a historical name/entity transition. These facts do not prove omissions, and names alone cannot establish full subsidiary, acquired-portfolio or current-ownership coverage. The supplied denominators are captured patent portfolios, not certified corporate totals.')
    q.p('The supplied predict93 fields agree with score >=0.93. Therefore the older 89.93% threshold problem described in USPTO release notes is not present in these flags. This verifies the cutoff behavior, not the file release provenance.')
    q.p('Targeted external check: the original US7355601 front page confirms the IBM/Microsoft assignees and 2008 issue date. Its continuation chain identifies US6862027, also captured here under Microsoft with a different application ID. Family dependence is therefore a concrete feature, not only a hypothetical concern.')
    q.heading('Transformations and exclusions');q.table(table('analysis_scope_ledger'))
    q.p('Every original column and row is retained in clean_patent_company.csv.gz. IDs remain strings; dates supply calendar features; overlapping component counts, hardware-only/nonhardware indicators, within-sample membership weights and analysis eligibility flags are added. Missing locations and reissues are retained. Each sensitivity restriction is confined to that analysis and recorded in the scope ledger. source_row_number maps derived rows back to the original CSV line.')
    q.heading('Verification and unresolved checks');q.bullets([
        'All source values survive exact dataframe round-trip comparison; the original file SHA-256 remains unchanged.',
        'Annual totals, all AI thresholds, component partitions, fractional membership sums and count-change decomposition reconcile.',
        'Still needed for a source merge audit: original assignee and AIPD tables, versions, company mapping, left/anti-join counts, and unmatched ID examples.',
        'Still needed for family counting: reissue parents, continuation relationships and patent-family IDs; these are absent.',
        'Still needed for substantive validation: patent text/claims and a stratified, independently reviewed label sample.'])
    q.p('Original CSV SHA-256: '+audit['source_sha256']);q.links(SOURCE_URLS);q.write('data_quality_report')
    s=Report('Statistical analysis: exploratory annual portfolio trends',out)
    s.p('All tests are exploratory: hypotheses were formed after examining this same dataset. There is no held-out validation sample, preregistration, independent confirmation or causal identification. Deterministic descriptive counts/shares need no sampling intervals; the intervals below describe uncertainty under a hypothetical annual-process model.')
    s.p('The primary family contains ten two-sided zero-slope tests: any-AI and machine-learning share for each company at the 86% score cutoff, 2010-2023. Annual shares receive equal weight. The estimand is the average linear change in a calendar year’s observed portfolio share, not the probability that a randomly sampled patent is AI. Newey-West/Bartlett HAC lag 2 allows short serial dependence; covariance includes n/(n-2), and intervals/p-values use t with 12 degrees of freedom. Holm correction covers all ten primary p-values. Marginal 95% confidence intervals are not simultaneous intervals.')
    statdisplay=pd.DataFrame([{'Company':r.company,'Outcome':'Any AI' if 'any_ai' in r.outcome else 'ML',
        'Slope (pp/year)':f'{r.slope_pp_per_year:+.2f}', '95% CI':f'[{r.ci_low:+.2f}, {r.ci_high:+.2f}]',
        'Holm p (10 tests)':f'{r.holm_p_10_tests:.4g}'} for r in primary.itertuples()])
    s.table(statdisplay);s.fig('07_annual_trend_intervals','Annual linear-projection slopes with temporal model-based intervals. These omit classification and coverage uncertainty.')
    s.p('The strongest positive average trends are IBM and NVIDIA for broad AI and ML, plus Qualcomm for ML from a very low starting level. These survive the ten-test Holm correction under this model. Microsoft’s ML slope has a positive marginal interval, but its Holm-adjusted p-value is about 0.171; it is not a multiple-testing-confirmed result. Google’s full-window ML slope is near zero because a decline is followed by a recovery. A weak long-window slope does not establish that a company lacks technological progress.')
    s.heading('Assumption checks and robustness')
    s.p('There are only 14 observations per company. Annual residual correlations are about 0.49-0.85. Quadratic descriptive fits improve R-squared substantially in eight of ten series, so literal constant-slope assumptions are weak for those series. The linear ML fits for IBM and NVIDIA have negative fitted shares at the early endpoint; they are linear projection summaries, not valid probability forecasts. Empirical-logit sensitivity uses (count+0.5)/(denominator+1) for the transform only and yields bounded fitted shares. This correction is not written into the clean outcomes.')
    s.table(diagnostics[['company','outcome','linear_r2','quadratic_r2_gain','lag1_residual_corr','fitted_min']].round(3))
    s.fig('08_trend_diagnostics','Residual patterns reveal acceleration and reversals; confidence intervals require a cautious model-based reading.')
    s.bullets([
        'Classification cutoffs: repeat all slopes at 50%, 86% and 93%; no sensitivity p-values are used to select a conclusion.',
        'Temporal specifications: HAC lags 1 and 3, HC3 intervals, leave-one-year-out slope ranges, and a Theil-Sen point estimate.',
        'Time windows: repeat 2010-2021 and 2014-2023. The latter describes a different estimand, not a replacement chosen for significance.',
        'Portfolio definitions: exclude valid reissues only as sensitivity; exclude observed entities below 1% of a company’s captured records; use any component other than hardware.',
        'Twenty secondary company-pair effects are fitted to annual difference series, retaining cross-company year covariance. Their pointwise intervals are exploratory and not simultaneous.'])
    s.p('IBM and NVIDIA keep positive AI/ML point slopes across the checked definitions and windows. Google’s direction depends on the time window; Qualcomm’s broad AI reverses after its mid/late-2010s peak, and its short-window ML interval includes zero. Excluding reissues changes the largest primary slope by less than 0.01 pp/year. Removing the smallest captured entities changes the largest primary slope by about 0.01 pp/year. These checks address specific observed choices, not unknown subsidiaries or family dependence.')
    s.p('Classification scores are model outputs, not externally calibrated ground-truth probabilities for these five portfolios. Patent-level bootstrap or binomial intervals would ignore family/common-process dependence. None of the intervals include classifier error, entity-resolution error, unmatched merges or technological changes in score calibration. No causal effects or predictions beyond 2023 are asserted.')
    s.write('statistical_analysis')
    r=Report('AI-related patent activity: five technology companies',out)
    r.p('Independent exploratory study of the supplied U.S. patent extract • grant years 1976–2023 • main comparative period 2010–2023 • main classification cutoff 86%. Analysis prepared 3 October 2026. The findings describe observed patents and classifier labels, not current 2026 activity, AI capability or innovation quality.')
    r.heading('Major findings')
    r.bullets([
        'NVIDIA’s captured portfolio shifts toward machine learning: 7 of 1,010 grants (0.7%) in 2014-2016 versus 230 of 786 (29.3%) in 2021-2023. The +28.6 percentage-point change is visible at all three score cutoffs. Its recent profile is especially concentrated in vision and hardware.',
        'IBM remains the largest captured AI grant producer. From 2021 to 2023 its AI-classified grant count falls from 5,416 to 2,526 (-53.4%), while AI share rises from 62.4% to 69.1%. A contracting portfolio and an increasing AI share coexist.',
        'Qualcomm’s AI counts and AI concentration diverge: 318 to 424 AI-classified grants from 2021 to 2023 (+33.3%), but portfolio share drops from 14.8% to 11.0%. Its broad AI share peaks in 2017 within the main window and then falls.',
        'Google and Microsoft have high recent broad AI shares, about 71.7% and 71.5%, but their long-window average trends mask declines and later recovery. Google has the highest recent NLP and speech shares among these captured entities.',
        'Company conclusions depend on the denominator, time window and AI definition. A lifetime patent-count ranking would confound company history, assignee coverage and portfolio size. The dataset alone cannot rank company AI capability.'])
    r.fig('02_counts_and_shares','Observed grant counts, broad AI portfolio shares and machine-learning shares. All three panels use the same 86% score cutoff.')
    r.heading('1. Dataset audit and population')
    r.p(f'The source has {audit["rows"]:,} patent-company rows, {audit["unique_patents"]:,} unique patents and {audit["columns"]} columns. It is not an AI-only dataset: {es["ai86_unique"]:,} unique patents ({100*es["ai86_unique"]/es["unique_patents"]:.1f}%) meet the 86% any-AI rule. All flag_patent values equal 1. Publication date therefore measures grant/issue date, not application date or invention date. Non-AI-classified records supply the captured-portfolio denominator.')
    r.p('Every document ID equals its patent merge ID; all identifiers follow utility/reissue formats; application IDs preserve leading zeros. There are no exact duplicates and no repeated patent-company memberships. Patent 7355601 is assigned to both IBM and Microsoft with identical document/classifier fields; both membership rows are retained, while pooled totals count it once. There are 143 valid reissue records. Only location_id is missing, in 230 records; no missing values are imputed.')
    r.p('All binary classification flags are nested across cutoffs, every score is in [0,1], every component flag agrees with its score cutoff, and each any-AI flag is the logical OR of eight component flags. The 93% flags use the corrected cutoff behavior. These are strong internal consistency checks; they do not measure merge recall or classification accuracy.')
    r.table(coverage[['company','rows','first_date','last_date','assignee_ids','missing_location']])
    r.p('The extract covers 10 assignee IDs. Google is represented by one GOOGLE LLC ID; IBM, Microsoft, NVIDIA and Qualcomm have multiple captured entity IDs. Assignee disambiguation, historical aliases, subsidiaries and acquisitions can alter corporate attribution. The upstream tables, release versions, company-selection code and unmatched rows are absent. Therefore internal key agreement cannot establish complete company coverage. All company shares are conditional on the supplied entity selection.')
    r.fig('01_history_coverage','Coverage begins in different years. Zero cells represent no captured records, rather than proven absence of company invention.')
    r.heading('2. Analytical design and transformations')
    r.p('The primary threshold is 86%, selected from USPTO’s methodology as a midpoint calibrated to historical aggregate prediction volumes. This is not a demonstrated 86% precision or a guarantee that an individual patent truly contains AI. The 50% and 93% flags provide sensitivity analyses. The dataset uses broad, overlapping technology categories; these are not labels for modern generative AI.')
    r.p('The main window is 2010-2023: all five companies have at least 156 grants per year and records in all 12 months. It removes severe early-company sparsity from the main trend comparison without deleting those rows from the dataset. Calendar completeness is a useful audit but cannot certify all company counts. Recent profiles use 2021-2023, compared descriptively with 2014-2016. The full source remains unchanged; the clean dataset retains all original rows and columns plus documented features.')
    r.bullets([
        'AI count: number of captured company grants whose any-AI flag is 1.',
        'AI/ML portfolio share: classifier-positive grant count divided by all captured grants for that company and year/period.',
        'Hardware-only: AI hardware positive and none of the other seven components positive. Nonhardware: at least one other component positive.',
        'Component breadth: number of positive component labels, allowing overlap. This measures classifier label breadth, not invention quality.',
        'Within-sample fraction: 1 divided by the number of included company labels for a document. This conserves selected-sample totals and is not a full ownership weight.',
        'Main estimates give each calendar year equal weight; a separate equal-year table contrasts this with patent-weighted pooling.'])
    r.table(table('analysis_scope_ledger'))
    r.heading('3. Company activity and technology differences')
    latest=annual[annual.year==2023].set_index('company').reindex(COMPANIES).reset_index()
    latest_display=pd.DataFrame({'Company':latest.company,'All grants, 2023':latest.total_patents.map(lambda x:f'{int(x):,}'),
        'AI grants, 86%':latest.predict86_any_ai.map(lambda x:f'{int(x):,}'),
        'AI share':latest.predict86_any_ai_share.map(fmt_pct),'ML share':latest.predict86_ml_share.map(fmt_pct)})
    r.table(latest_display)
    r.p('In 2023 IBM has 2,526 captured AI-classified grants, exceeding the other individual companies, despite its recent contraction. NVIDIA has only 252; its important finding is a technology-mix shift, not absolute grant leadership. Google and Microsoft have similar broad AI shares, while their component profiles differ. Qualcomm’s denominator is mostly non-AI under this classifier, so its low share does not establish low technological sophistication.')
    r.fig('04_recent_technology_profile','Recent component shares use all captured grants as their denominator. Categories overlap; values do not sum to 100%.')
    r.p('During 2021-2023 NVIDIA’s vision share is 38.5% and AI-hardware share 47.2%, versus 11.4% and 40.1% for IBM. Google’s NLP share is 29.7% and speech share 17.7%, above the other captured firms. NVIDIA’s ML share is 29.3%, IBM’s 25.5%, Google’s 24.5%, Microsoft’s 23.2%, and Qualcomm’s 2.1%. These are observed portfolio composition effects, not classifier-adjusted measures of true invention.')
    r.fig('05_technology_mix_changes','Descriptive change from 2014–2016 to 2021–2023, in percentage points. Periods are post-EDA research choices and not independent confirmatory samples.')
    r.p('The early-to-recent ML share changes are +28.6 pp for NVIDIA, +19.1 pp for IBM, +12.5 pp for Microsoft, +8.6 pp for Google and +0.6 pp for Qualcomm at 86%. Counts also matter: NVIDIA’s ML count rises from 7 to 230 despite a smaller three-year total portfolio; IBM rises from 1,467 to 4,271; Microsoft from 817 to 1,406; Google changes from 1,316 to 1,198 while its ML share rises as the denominator contracts. This distinction prevents equating concentration with output.')
    r.p('Component co-occurrence is descriptive. For NVIDIA, ML and vision overlap in 173 of 786 recent grants, Jaccard 0.481 and phi 0.485. IBM’s ML/NLP phi is 0.460, and Microsoft’s is 0.452. These relationships can reflect complementary technologies, shared text or classifier error; no causal conclusion is justified. All 140 company/component pairs are exported, including less striking ones.')
    r.heading('4. Exploratory statistical evidence')
    r.p('After EDA, ten primary tests were frozen: any-AI and ML annual-share slopes for every company, 2010-2023, at 86%. OLS estimates a transparent average linear projection of annual shares; HAC lag 2 and t(12) provide approximate temporal model intervals. Holm adjusts all ten primary p-values. Inferences are exploratory because the same data generated the hypotheses. No patent-level independence is assumed for these standard errors.')
    r.table(statdisplay)
    r.fig('07_annual_trend_intervals','Effect sizes and marginal 95% intervals, in pp/year. Holm adjustment applies to the ten p-values, not the confidence intervals.')
    r.p('IBM and NVIDIA have positive long-window AI and ML average trends under the model. Qualcomm has a much smaller positive ML slope, +0.162 pp/year (95% CI +0.101 to +0.223); the effect is modest in portfolio terms despite its small adjusted p-value. Microsoft’s positive ML marginal interval does not survive the primary multiplicity correction. Google’s net full-window ML trend is inconclusive; its later recovery is visible descriptively and in the later-window sensitivity.')
    r.p('The linear assumptions are imperfect: residual serial structure and strong curvature occur in most series. Early ML fits extend below zero for IBM and NVIDIA, which rules out treating the linear fit as a probability forecast. Bounded empirical-logit sensitivity is included; it does not fix unknown classifier or capture error. With 14 years, HAC intervals remain approximate. The full statistical report supplies diagnostics, alternative methods and all effects.')
    r.heading('5. Uncertainty and robustness')
    r.fig('03_threshold_sensitivity','Threshold sensitivity changes portfolio-share levels materially; trend direction must be assessed separately.')
    r.p('Overall unique-patent AI counts are 151,407 at 50%, 125,981 at 86%, and 114,949 at 93%. Raising the cutoff from 50% to 93% reduces the count by 24.1%. This is definition sensitivity, not a confidence interval and not an estimated classifier-error rate. The observed high/low company-share separation persists, while precise levels depend on the chosen cutoff.')
    r.p('IBM and NVIDIA keep positive primary point slopes at all three cutoffs, with or without the 2022-2023 endpoint years, and after excluding hardware-only labels from the AI definition. Excluding reissues or small captured entities has minimal effect on primary slopes. Microsoft’s broad AI slope changes sign when the recent two years are omitted. Google’s ML slope changes from about -0.13 pp/year in 2010-2023 to +1.24 in 2014-2023. Qualcomm’s broad AI slope is about +0.22 over 2010-2023 but -0.75 over 2014-2023, confirming that one line masks a rise followed by a fall.')
    r.p('These sensitivity results are reported as alternative estimands, not selected for statistical significance. No confidence interval includes upstream omissions, unknown corporate-group mapping, family duplication or classifier calibration uncertainty. Dates reflect grant timing and patenting strategy; changes cannot be assigned to invention timing or corporate AI investment.')
    r.heading('6. Anomalies investigated and retained')
    r.bullets([
        'IBM’s 2022 portfolio drops from 8,680 to 4,398 grants (-49.3%). Every month remains represented, and the principal observed assignee entity persists. IBM Research’s January 2023 account states that IBM had moved toward more selective patenting. This supports a plausible strategy interpretation, but is not a causal test and cannot rule out capture changes.',
        'NVIDIA’s total grants jump from 212 in 2022 to 369 in 2023 (+74.1%). Its 86% AI share is nearly unchanged (67.9% to 68.3%), so that one-year AI-count increase mostly reflects grant volume rather than another large mix shift. Application/grant lags, families and corporate mapping need external records to investigate further.',
        'Qualcomm’s portfolio expands substantially from 2021 to 2023. Absolute AI growth accompanies falling broad AI share; inspect whether non-AI communication-related grants account for the denominator growth using CPC/text data before interpreting strategy.',
        'Patent 7355601 is a valid IBM/Microsoft co-assignment within this extract. It is retained for company portfolios and collapsed only for pooled document totals.',
        'All 143 RE identifiers are valid reissues and retained. A sensitivity removes them; parent links are unavailable, so the main file is a grant-document dataset rather than a distinct-invention-family dataset.',
        'The 230 missing location IDs are retained. No geographic inference is attempted.',
        'Threshold-borderline examples and earliest company documents are exported for manual review. None is deleted because of a suspicious appearance.'])
    r.p('A targeted primary-document check corroborates US7355601’s two assignees. It identifies a chain to US6862027, which is also captured under Microsoft, confirming related documents despite distinct application IDs. The shared document concerns graphics and processor data movement, with AI mentioned in game tasks; its hardware score is about 0.999. This illustrates the broad classifier category and warrants label review, rather than automatic reclassification. See the original patent and externally_reviewed_patent_case.csv.')
    r.fig('06_volume_mix_and_hardware','Left: exact symmetric arithmetic decomposition of 2021–2023 AI-count changes. Right: hardware-only share among AI-classified grants; both definitions need explicit denominators.')
    r.p('For IBM, the 2,890-grant AI decline decomposes into -3,300.7 grants from portfolio volume and +410.7 from the share change. For Qualcomm, the +106 AI grants decompose into +222.0 from volume and -116.0 from the share change. This explains the accounting identity; it does not identify causes. NVIDIA’s hardware-only share among AI grants declines from 55.5% in 2014-2016 to 22.5% in 2021-2023 at 86%, consistent with a broader mix of classifier labels.')
    r.heading('7. Modelling decision')
    r.p('The statistical trend models already contribute to the research objective. No additional ML prediction model is fitted: there is no independent target for innovation, impact or future activity. Predicting AI flags from supplied scores would reproduce their deterministic construction and leak the outcome. A random patent split would ignore time and unknown families. Forecasting through 2026 or assessing generative-AI capability is unsupported by this file, which ends in 2023.')
    r.heading('8. Methodological limitations')
    r.bullets([
        'Merge completeness is unidentifiable: all observed matches can be correct even if many relevant records are missing.',
        'Assignee coverage is conditional and uneven; a full corporate group may include subsidiaries, acquisitions, aliases and assignment changes absent here.',
        'All documents are grants. Rejected, abandoned, pending or unpublished applications are absent; publication date is not an invention date. Recent application cohorts have unresolved grant outcomes even when calendar grant years are complete.',
        'Classifier labels are imperfect broad definitions. Score meaning and classification error can differ by company, component and technological era. The single extract is internally rule-consistent; that does not prove historical calibration invariance.',
        'One invention can generate related grants, continuations or reissues. Unique application numbers do not guarantee independent invention families.',
        'Only five selected companies are covered. These shares are within captured portfolios, not U.S. AI-patent market shares.',
        'Statistical hypotheses are post-EDA; multiplicity control does not turn them into independent confirmation. Strong curvature and 14-year temporal samples limit trend inference.',
        'Patent numbers/labels do not establish novelty, quality, scientific leadership, revenue, investment or causality. No current 2026 trend is measured.'])
    r.heading('9. Recommendations for further analysis')
    r.bullets([
        'First audit the original merge with a left join and anti-join counts by company/year. Preserve versions, mapping rules and unmatched IDs; this is the highest-priority unresolved validity check.',
        'Build an explicit corporate-entity mapping with effective dates and a sensitivity comparing core legal entities with an expanded group. Validate individual boundary cases rather than assuming all affiliates belong.',
        'Add filing dates, application status and family/reissue-parent links. Separate grant-output trends from filing-cohort trends and distinct invention families.',
        'Manually inspect a stratified sample across company, year, component and score band. Independent labels can estimate company/era-specific error and make classification uncertainty measurable.',
        'Use CPC subclasses and patent text/claims to investigate Qualcomm’s denominator expansion and NVIDIA’s ML/vision shift. Add fixed-window forward citations only if studying impact.',
        'Confirm the strongest exploratory patterns in a separate later data release or an independently assembled patent sample, with hypotheses and sensitivity rules specified before inspection.',
        'If forecasting is later requested, use time-separated validation and stable entity definitions. Do not forecast by training on deterministic label fields.'])
    r.heading('10. Reproducibility and deliverables')
    r.p('The bundle includes clean_patent_company.csv.gz; six numbered Python stages plus shared methods and a runner; eight PNG/SVG figures; all audit, EDA, statistical and robustness tables; separate data-quality and statistical reports; a modelling decision; a research log in JSONL and Markdown; a scope ledger; a feature dictionary; and source/environment verification records. The supplied original CSV is not copied into the bundle, remains unchanged, and is identified by SHA-256.')
    r.code('python -m pip install -r requirements.txt\npython code/run_pipeline.py --input /path/to/five_big_tech_ai_patents.csv --output outputs')
    r.p('All source values were checked exactly after round-trip parsing, and all count summaries reconcile. No network is required to run the analysis once the four dependencies are installed. Reports embed their plots in the standalone HTML; SVGs are included for editing/export. All random-free stages are deterministic apart from incidental file metadata. Original CSV SHA-256: '+audit['source_sha256'])
    r.heading('Sources and interpretation of external context');r.links(SOURCE_URLS)
    r.p('The primary methodology reference is Pairolero et al., The artificial intelligence patent dataset (AIPD) 2023 update, Journal of Technology Transfer (2025), doi:10.1007/s10961-025-10189-8. Source pages were reviewed on 3 October 2026. USPTO documentation supplies field/cutoff meanings and release-note context; IBM’s account supplies possible strategic context. All numerical company results in this report are calculated from the supplied CSV.')
    r.write('analysis_report',standalone_html=True)
    records=[json.loads(x) for x in (out/'research_log.jsonl').read_text().splitlines()]
    research=Report('Research log: observations, decisions and limitations',out)
    for i,rec in enumerate(records,1):
        research.heading(f'{i:02d} — Stage {rec["stage"]}')
        for key in ['observation','hypothesis','decision','justification','result','limitation']:
            research.p(key.capitalize()+': '+rec[key])
    research.write('research_log')
    print('All conservation/provenance checks passed; reports generated.')

if __name__=='__main__':main()