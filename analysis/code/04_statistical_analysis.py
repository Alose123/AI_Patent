"""Exploratory annual trend estimates with temporal uncertainty and robustness."""
from common import *
from importlib import import_module
eda=import_module('03_eda')
import matplotlib.pyplot as plt

def fits(a, definition, first=2010, last=2023, lag=2, label='main'):
    rows=[]
    for company in COMPANIES:
        g=a[(a.company==company)&a.year.between(first,last)].sort_values('year')
        result,_,_=trend_fit(g.year,g[definition+'_share'],lag)
        rows.append(dict(company=company,outcome=definition,window=f'{first}-{last}',
                         variant=label,hac_lag=lag,**result))
    return rows

def main():
    args=setup();out=args.output;d=read_clean(out)
    a=pd.read_csv(out/'tables'/'annual_company_metrics.csv')
    primary=pd.DataFrame(fits(a,'predict86_any_ai')+fits(a,'predict86_ml'))
    primary['holm_p_10_tests']=holm(primary.p_value)
    primary['interpretation']='Exploratory, model-based annual trend; not independently confirmed'
    save_table(primary,out,'primary_annual_trends')
    robust=[]
    for outcome in ['any_ai','ml']:
        for t in THRESHOLDS:
            robust+=fits(a,f'predict{t}_{outcome}',label=f'cutoff_{t}')
        robust+=fits(a,f'predict86_{outcome}',lag=1,label='HAC_lag_1')
        robust+=fits(a,f'predict86_{outcome}',lag=3,label='HAC_lag_3')
        robust+=fits(a,f'predict86_{outcome}',last=2021,label='before_2022_2023')
        robust+=fits(a,f'predict86_{outcome}',first=2014,label='later_start_2014')
        robust+=fits(aggregate(d[d.is_reissue==0]),f'predict86_{outcome}',label='exclude_reissues')
        # Remove only small observed entities as a sensitivity; retain both large
        # Microsoft IDs so an administrative assignee transition is not lost.
        entities=d.groupby(['company','assignee_id']).size().reset_index(name='n')
        entities['share']=entities.n/entities.groupby('company').n.transform('sum')
        major_ids=entities.loc[entities.share>=.01,'assignee_id'].tolist()
        robust+=fits(aggregate(d[d.assignee_id.isin(major_ids)]),f'predict86_{outcome}',label='exclude_observed_entities_below_1pct')
    for t in THRESHOLDS:robust+=fits(a,f'nonhardware{t}',label=f'AI_without_hardware_{t}')
    robust=pd.DataFrame(robust)
    robust=robust.drop(columns=['p_value']) # Robustness is not a second significance search.
    save_table(robust,out,'trend_robustness')
    ledger=pd.read_csv(out/'tables'/'analysis_scope_ledger.csv')
    ledger=ledger[ledger.analysis!='small observed entity sensitivity only']
    ledger=pd.concat([ledger,pd.DataFrame([{'analysis':'small observed entity sensitivity only',
        'reason':'omit assignee IDs comprising less than 1% of their company records in this extract',
        'rows_excluded':int((~d.assignee_id.isin(major_ids)).sum()),
        'rows_retained':int(d.assignee_id.isin(major_ids).sum())}])],ignore_index=True)
    save_table(ledger,out,'analysis_scope_ledger')
    bounded=[]
    for outcome in ['any_ai','ml']:
        for company in COMPANIES:
            g=a[(a.company==company)&a.year.between(2010,2023)].sort_values('year')
            count=g[f'predict86_{outcome}'].to_numpy();n=g.total_patents.to_numpy()
            proportion=(count+.5)/(n+1) # Only for this diagnostic transform; source flags unchanged.
            transformed=np.log(proportion/(1-proportion))
            result,pred,_=trend_fit(g.year,transformed)
            b=result['slope_pp_per_year']/100
            predicted=1/(1+np.exp(-pred))
            bounded.append(dict(company=company,outcome=outcome,annual_log_odds_slope=b,
                annual_odds_ratio=np.exp(b),ci_low_odds_ratio=np.exp(result['ci_low']/100),
                ci_high_odds_ratio=np.exp(result['ci_high']/100),
                fitted_2010_share=predicted[0],fitted_2023_share=predicted[-1],
                fitted_average_change_pp_per_year=100*(predicted[-1]-predicted[0])/13,
                method='Unweighted OLS of empirical annual logit; HAC(2); 0.5 correction only in transform'))
    save_table(pd.DataFrame(bounded),out,'empirical_logit_sensitivity')
    # Test shared-year trend differences directly; contemporaneous cross-company
    # covariance remains in the differenced annual series. Secondary estimates,
    # without p-values or claims of simultaneous/confirmatory confidence coverage.
    contrast=[]
    from itertools import combinations
    for outcome in ['any_ai','ml']:
        pivot=a[a.year.between(2010,2023)].pivot(index='year',columns='company',values=f'predict86_{outcome}_share')
        for c1,c2 in combinations(COMPANIES,2):
            f,_,_=trend_fit(pivot.index,pivot[c1]-pivot[c2])
            contrast.append(dict(company_a=c1,company_b=c2,outcome=outcome,
                slope_difference_pp_per_year=f['slope_pp_per_year'],ci_low=f['ci_low'],ci_high=f['ci_high'],
                confidence_note='Pointwise exploratory model-based 95% CI; not simultaneous across 20 contrasts'))
    save_table(pd.DataFrame(contrast),out,'secondary_company_trend_contrasts')
    diagnostics=[];residuals=[]
    for outcome in ['any_ai','ml']:
        for company in COMPANIES:
            g=a[(a.company==company)&a.year.between(2010,2023)].sort_values('year')
            f,pred,e=trend_fit(g.year,g[f'predict86_{outcome}_share'])
            x=g.year.to_numpy(float)-g.year.mean();y=g[f'predict86_{outcome}_share'].to_numpy()
            p2=np.polyfit(x,y,2); pred2=np.polyval(p2,x)
            sst=np.sum((y-y.mean())**2);r2q=1-np.sum((y-pred2)**2)/sst
            diagnostics.append(dict(company=company,outcome=outcome,linear_r2=f['r_squared'],
                quadratic_r2=r2q,quadratic_r2_gain=r2q-f['r_squared'],lag1_residual_corr=f['lag1_residual_corr'],
                fitted_min=f['fitted_min'],fitted_max=f['fitted_max'],
                max_abs_residual_pp=100*abs(e).max(),
                assessment='Inspect curvature; linear slope is only an average time summary' if r2q-f['r_squared']>.20 else 'Linear summary reasonably tracks annual shares; inspect residuals'))
            for year,yy,pp,ee in zip(g.year,y,pred,e):
                residuals.append(dict(company=company,outcome=outcome,year=year,observed_share=yy,
                    fitted_share=pp,residual_pp=100*ee))
    save_table(pd.DataFrame(diagnostics),out,'model_diagnostics')
    save_table(pd.DataFrame(residuals),out,'annual_model_residuals')
    # A meaningful model check against an independent scipy simple-regression slope.
    for row in primary.itertuples():
        g=a[(a.company==row.company)&a.year.between(2010,2023)]
        expected=100*stats.linregress(g.year,g[row.outcome+'_share']).slope
        if not np.isclose(expected,row.slope_pp_per_year,rtol=1e-10,atol=1e-10):
            raise AssertionError('OLS slope failed independent scipy verification')
    eda.style();fig,axes=plt.subplots(1,2,figsize=(12,4.5),sharey=True)
    for ax,outcome,title in zip(axes,['predict86_any_ai','predict86_ml'],['Any AI: average annual share change','Machine learning: average annual share change']):
        for i,company in enumerate(COMPANIES):
            r=primary[(primary.company==company)&(primary.outcome==outcome)].iloc[0]
            ax.errorbar(r.slope_pp_per_year,4-i,xerr=[[r.slope_pp_per_year-r.ci_low],[r.ci_high-r.slope_pp_per_year]],
                fmt='o',color=eda.COLORS[company],capsize=4,markersize=7)
        ax.axvline(0,color='#667085',ls='--',lw=1);ax.set_yticks(range(5),COMPANIES[::-1]);ax.grid(axis='x',alpha=.2)
        ax.set_title(title,loc='left',fontsize=11);ax.set_xlabel('Percentage points per grant year')
    fig.suptitle('Exploratory trends, 2010–2023 | 95% temporal model intervals',fontweight='bold')
    fig.text(.07,-.03,'OLS on 14 annual shares; Newey–West lag 2 and t(12). Intervals omit classifier, family, and coverage uncertainty.',fontsize=9)
    fig.tight_layout();eda.figure(fig,out,'07_annual_trend_intervals')
    fig,axes=plt.subplots(2,5,figsize=(16,6),sharex=True)
    res=pd.DataFrame(residuals)
    for i,outcome in enumerate(['any_ai','ml']):
        for j,company in enumerate(COMPANIES):
            ax=axes[i,j];g=res[(res.company==company)&(res.outcome==outcome)]
            ax.plot(g.year,g.residual_pp,color=eda.COLORS[company],marker='o',ms=3)
            ax.axhline(0,color='#667085',lw=.8);ax.grid(alpha=.2);ax.set_xticks([2010,2016,2023])
            ax.set_title(f'{company} | {"Any AI" if i==0 else "ML"}',fontsize=10)
            if j==0:ax.set_ylabel('Residual (pp)')
            if i==1:ax.set_xlabel('Grant year')
    fig.suptitle('Trend assumptions require caution: acceleration and reversals leave structured residuals',fontweight='bold')
    fig.tight_layout();eda.figure(fig,out,'08_trend_diagnostics')
    log(out,'04','Annual shares show unequal patent denominators and temporal patterns.',
        'There may be systematic annual changes in classifier-defined AI/ML shares.',
        'OLS on annual shares, unweighted years; HAC(2), n/(n-2) correction and t(12) intervals; Holm over all 10 primary tests.',
        'A patent-level binomial test assumes independent documents/families and exaggerates precision; unweighted time units target an average annual portfolio share.',
        'Effect sizes, 95% CIs, adjusted p-values, HC3/leave-one-year-out diagnostics and alternative windows exported.',
        '14 years is a small sample for HAC; model intervals do not include systematic coverage, classifier calibration or unobserved patent-family dependence.')
    log(out,'04','Linear trends can average acceleration or reversals.',
        'A single slope may obscure timing and company-specific portfolio shifts.',
        'Inspect residual serial correlation and quadratic fit improvement; retain observed curves and report window sensitivity.',
        'A linear trend is interpretable, but flexible models could overfit a short annual series; quadratic R2 is a diagnostic, not an optimized final model.',
        'Model diagnostics and residual plots saved; sensitivity p-values intentionally omitted.',
        'Curvature and nonstationarity weaken literal linear-trend inference, especially for hump-shaped series.')
    log(out,'04','IBM and NVIDIA linear ML fits extend below zero at the early endpoint.',
        'A bounded trend summary might change the direction of the descriptive pattern.',
        'Add empirical-logit annual trend sensitivity with (count+0.5)/(n+1), retaining source flags unchanged.',
        'This avoids taking logit(0) and produces bounded fitted shares; alternative binomial GLM would place disproportionate weight on large patent years.',
        'Odds-ratio slopes and fitted endpoint changes exported; no sensitivity significance optimization.',
        'The transformation changes the estimand, and it does not remove curvature, temporal dependence or classifier uncertainty.')
    log(out,'04','Cross-company annual differences may share common year shocks.',
        'Company trend changes may differ even after common-year dependence is considered.',
        'Estimate all pairwise slope differences from annual difference series with HAC intervals, no secondary p-values.',
        'Differencing incorporates contemporaneous covariance; subtracting independent standard errors would not.',
        '20 secondary effect estimates with pointwise, explicitly exploratory intervals exported.',
        'Intervals are not simultaneous and cannot independently confirm data-selected contrasts.')
    print('Statistical analysis completed; all 10 primary trend slopes verified against scipy.')

if __name__=='__main__':main()