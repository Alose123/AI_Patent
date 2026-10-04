"""Descriptive analysis, transparent denominators, coverage/anomaly investigation."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from itertools import combinations

COLORS={'IBM':'#2864B4','NVIDIA':'#278649','Qualcomm':'#BF6430','Google':'#8B54B5','Microsoft':'#CB3D64'}

def style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
        'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold',
        'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})

def figure(fig,out,name):
    fig.savefig(out/'figures'/f'{name}.png',dpi=180,bbox_inches='tight')
    fig.savefig(out/'figures'/f'{name}.svg',bbox_inches='tight')
    plt.close(fig)

def main():
    args=setup();out=args.output;d=read_clean(out);style()
    a=aggregate(d).sort_values(['company','year'])
    save_table(a,out,'annual_company_metrics')
    c=d.groupby('company').agg(total_patents=('doc_id','size'), ai86=('predict86_any_ai','sum'),
        ai50=('predict50_any_ai','sum'),ai93=('predict93_any_ai','sum'),ml86=('predict86_ml','sum'),
        reissues=('is_reissue','sum'))
    for t in THRESHOLDS:c[f'ai{t}_share']=c[f'ai{t}']/c.total_patents
    save_table(c.reset_index(),out,'company_summary_full_history')
    recent=d[d.recent_2021_2023==1]; base=d[d.grant_year.between(2014,2016)]
    period=[];profiles=[]
    for label,sub in [('2014-2016',base),('2021-2023',recent)]:
        for company,g in sub.groupby('company'):
            row=dict(company=company,period=label,total_patents=len(g))
            for t in THRESHOLDS:
                row[f'ai{t}']=int(g[f'predict{t}_any_ai'].sum())
                row[f'ai{t}_share']=g[f'predict{t}_any_ai'].mean()
                row[f'ml{t}']=int(g[f'predict{t}_ml'].sum())
                row[f'ml{t}_share']=g[f'predict{t}_ml'].mean()
                row[f'nonhardware{t}_share']=g[f'nonhardware{t}'].mean()
                row[f'hardware_only{t}_share']=g[f'hardware_only{t}'].mean()
                row[f'mean_components_ai{t}']=g.loc[g[f'predict{t}_any_ai']==1,f'n_components{t}'].mean()
                for k in COMPONENTS:
                    profiles.append(dict(company=company,period=label,threshold=t,component=k,
                        total_patents=len(g),count=int(g[f'predict{t}_{k}'].sum()),
                        portfolio_share=g[f'predict{t}_{k}'].mean(),
                        conditional_ai_share=g.loc[g[f'predict{t}_any_ai']==1,f'predict{t}_{k}'].mean()))
            period.append(row)
    period=pd.DataFrame(period);profiles=pd.DataFrame(profiles)
    save_table(period,out,'period_comparison');save_table(profiles,out,'technology_profiles')
    standardized=a[a.year.between(2010,2023)].groupby('company').agg(
        mean_annual_ai86_share=('predict86_any_ai_share','mean'),
        mean_annual_ml86_share=('predict86_ml_share','mean'),
        patents=('total_patents','sum'),ai86=('predict86_any_ai','sum'))
    standardized['patent_weighted_ai86_share']=standardized.ai86/standardized.patents
    save_table(standardized.reset_index(),out,'equal_year_company_comparison')
    # Calendar-month continuity and boundary inspection, not assertions of complete company portfolios.
    monthly=pd.read_csv(out/'tables'/'coverage_company_month.csv')
    q=monthly[monthly.year.between(2010,2023)].groupby(['company','year']).agg(
        observed_months=('month','nunique'),patents=('n','sum'))
    save_table(q.reset_index(),out,'main_period_month_coverage')
    a['total_yoy_pct']=100*a.groupby('company').total_patents.pct_change()
    a['ai86_yoy_pct']=100*a.groupby('company').predict86_any_ai.pct_change()
    anomaly=a[a.year.between(2011,2023)&((a.total_yoy_pct.abs()>=35)|(a.ai86_yoy_pct.abs()>=35))].copy()
    anomaly['action']='Retain; descriptive large-change flag, investigate volume/composition/coverage.'
    save_table(anomaly[['company','year','total_patents','predict86_any_ai','total_yoy_pct','ai86_yoy_pct','action']],out,'annual_anomalies')
    # Exact symmetric count decomposition; it describes changes and does not identify causes.
    decom=[]
    for company,g in a.groupby('company'):
        old=g[g.year==2021].iloc[0];new=g[g.year==2023].iloc[0]
        n0,n1=old.total_patents,new.total_patents
        p0,p1=old.predict86_any_ai_share,new.predict86_any_ai_share
        volume=(p0+p1)/2*(n1-n0);mix=(n0+n1)/2*(p1-p0)
        decom.append(dict(company=company,start_year=2021,end_year=2023,total_2021=n0,total_2023=n1,
            ai86_2021=old.predict86_any_ai,ai86_2023=new.predict86_any_ai,ai_share_2021=p0,ai_share_2023=p1,
            total_change_pct=100*(n1/n0-1),ai_count_change_pct=100*(new.predict86_any_ai/old.predict86_any_ai-1),
            ai_share_change_pp=100*(p1-p0),ai_count_change=new.predict86_any_ai-old.predict86_any_ai,
            volume_component=volume,share_component=mix,reconciliation_error=volume+mix-(new.predict86_any_ai-old.predict86_any_ai)))
    decom=pd.DataFrame(decom);save_table(decom,out,'count_share_decomposition')
    # Co-occurrence among all recent portfolio records, avoiding conditioning on any AI as a collider.
    pairs=[]
    for company,g in recent.groupby('company'):
        for k,l in combinations(COMPONENTS,2):
            x=g[f'predict86_{k}'].to_numpy();y=g[f'predict86_{l}'].to_numpy()
            both=np.sum((x==1)&(y==1));union=np.sum((x==1)|(y==1))
            phi=np.corrcoef(x,y)[0,1] if x.std() and y.std() else np.nan
            pairs.append(dict(company=company,component_a=k,component_b=l,n=len(g),
                a_count=x.sum(),b_count=y.sum(),both_count=both,jaccard=both/union if union else np.nan,phi=phi))
    pairs=pd.DataFrame(pairs);save_table(pairs,out,'recent_component_cooccurrence')
    # Review candidates selected by identifiers and distance to threshold, not significance.
    review=[]
    subsets=[('shared membership',d[d.shared_between_included_companies==1]),
             ('valid reissue',d[d.is_reissue==1]),
             ('earliest observed company grants',d.sort_values('pub_dt').groupby('company').head(5)),
             ('near 86% cutoff',d.assign(distance=(d.max_ai_score-.86).abs()).sort_values('distance').groupby('company').head(10))]
    for reason,sub in subsets:
        for _,r in sub.iterrows():
            review.append({k:r[k] for k in ['source_row_number','doc_id','pub_dt','company',
                'disambig_assignee_organization','predict50_any_ai','predict86_any_ai','predict93_any_ai','max_ai_score']}|
                {'review_reason':reason,'decision':'retain'})
    save_table(pd.DataFrame(review),out,'record_review_candidates')
    # Full history coverage heatmap: zero means absent in extract, not no invention.
    pivot=a.pivot(index='company',columns='year',values='total_patents').reindex(COMPANIES).fillna(0)
    fig,ax=plt.subplots(figsize=(13,3.8))
    im=ax.imshow(np.log10(1+pivot.values),aspect='auto',cmap='Blues')
    ax.set_yticks(range(5),COMPANIES);ticks=np.arange(0,len(pivot.columns),4)
    ax.set_xticks(ticks,pivot.columns[ticks]);ax.set_xlabel('Grant year')
    ax.set_title('Observed coverage differs sharply across company histories',loc='left')
    fig.colorbar(im,ax=ax,label='log10(1 + observed patents)',shrink=.8)
    fig.subplots_adjust(bottom=.25)
    fig.text(.08,.035,'Absent records cannot establish zero corporate activity. Only supplied assignee entities are covered.',fontsize=9)
    figure(fig,out,'01_history_coverage')
    fig,axes=plt.subplots(1,3,figsize=(15,4.5))
    for company in COMPANIES:
        g=a[(a.company==company)&a.year.between(2010,2023)]
        for ax,col in zip(axes,['predict86_any_ai','predict86_any_ai_share','predict86_ml_share']):
            ax.plot(g.year,g[col],label=company,color=COLORS[company],lw=2,marker='o',ms=3)
    axes[0].set_title('AI-classified grant counts');axes[0].set_ylabel('Patents')
    axes[1].set_title('AI share of observed portfolio');axes[2].set_title('Machine-learning share')
    for ax in axes:
        ax.set_xlabel('Grant year');ax.set_xticks([2010,2014,2018,2023]);ax.grid(alpha=.18)
    for ax in axes[1:]:ax.yaxis.set_major_formatter(PercentFormatter(1))
    axes[1].set_ylim(0,.9);axes[2].set_ylim(0,.4)
    fig.legend(*axes[2].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,-.035),ncol=5,fontsize=9,frameon=False)
    fig.suptitle('Counts and portfolio shares answer different questions | 86% score cutoff',x=.07,ha='left',fontweight='bold')
    fig.tight_layout();figure(fig,out,'02_counts_and_shares')
    fig,axes=plt.subplots(2,3,figsize=(13,7),sharex=True,sharey=True)
    for ax,company in zip(axes.flat,COMPANIES):
        g=a[(a.company==company)&a.year.between(2010,2023)]
        for t,ls in [(50,'--'),(86,'-'),(93,':')]:
            ax.plot(g.year,g[f'predict{t}_any_ai_share'],label=f'{t}% cutoff',color=COLORS[company],ls=ls,lw=2)
        ax.set_title(company,loc='left');ax.set_ylim(0,.95);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(alpha=.18)
        ax.set_xticks([2010,2015,2020,2023]);ax.set_xlabel('Grant year')
    axes.flat[0].legend(fontsize=8);axes.flat[-1].axis('off')
    fig.suptitle('Classification cutoff changes levels; robustness must also assess trend direction',fontweight='bold')
    fig.tight_layout();figure(fig,out,'03_threshold_sensitivity')
    mat=profiles[(profiles.period=='2021-2023')&(profiles.threshold==86)].pivot(index='company',columns='component',values='portfolio_share').reindex(index=COMPANIES,columns=COMPONENTS)
    fig,ax=plt.subplots(figsize=(12,4.2));im=ax.imshow(100*mat.values,cmap='YlGnBu',vmin=0,vmax=60,aspect='auto')
    ax.set_xticks(range(8),['ML','Evolutionary','NLP','Speech','Vision','Planning /\ncontrol','Knowledge','AI hardware']);ax.set_yticks(range(5),COMPANIES)
    for i in range(5):
        for j in range(8):ax.text(j,i,f'{100*mat.iloc[i,j]:.1f}%',ha='center',va='center',color='white' if mat.iloc[i,j]>.32 else '#17233C',fontsize=10)
    ax.set_title('Recent technology profiles | share of all observed grants, 2021–2023',loc='left')
    fig.colorbar(im,ax=ax,label='Portfolio share (%)',shrink=.8)
    fig.text(.07,-.035,'86% cutoff. Component labels overlap; rows do not sum to 100%. ML does not isolate generative AI.',fontsize=9)
    figure(fig,out,'04_recent_technology_profile')
    p0=profiles[(profiles.period=='2014-2016')&(profiles.threshold==86)].pivot(index='company',columns='component',values='portfolio_share').reindex(index=COMPANIES,columns=COMPONENTS)
    change=100*(mat-p0)
    fig,ax=plt.subplots(figsize=(12,4));im=ax.imshow(change.values,cmap='RdBu',vmin=-30,vmax=30,aspect='auto')
    ax.set_xticks(range(8),['ML','Evolutionary','NLP','Speech','Vision','Planning /\ncontrol','Knowledge','AI hardware']);ax.set_yticks(range(5),COMPANIES)
    for i in range(5):
        for j in range(8):ax.text(j,i,f'{change.iloc[i,j]:+.1f}',ha='center',va='center',color='white' if abs(change.iloc[i,j])>19 else '#17233C')
    ax.set_title('Technology mix shifts | 2021–2023 minus 2014–2016, percentage points',loc='left')
    fig.colorbar(im,ax=ax,label='Change (pp)',shrink=.8);figure(fig,out,'05_technology_mix_changes')
    fig,axes=plt.subplots(1,2,figsize=(13,4.5))
    for i,company in enumerate(COMPANIES):
        r=decom[decom.company==company].iloc[0]
        axes[0].bar(i-.18,r.volume_component,width=.35,color='#7992B6',label='Portfolio volume component' if i==0 else '')
        axes[0].bar(i+.18,r.share_component,width=.35,color='#E0A64F',label='AI share component' if i==0 else '')
        for j,t in enumerate(THRESHOLDS):
            rr=recent[recent.company==company]
            ai=rr[f'predict{t}_any_ai'].sum();hw=rr[f'hardware_only{t}'].sum()
            axes[1].bar(i+(j-1)*.25,hw/ai if ai else 0,width=.23,color=['#CBD5E1','#6983A9','#29466B'][j],label=f'{t}% cutoff' if i==0 else '')
    for ax in axes:ax.set_xticks(range(5),COMPANIES,rotation=20);ax.axhline(0,color='#667085',lw=.7);ax.legend(fontsize=8)
    axes[0].set_title('AI count change, 2021 to 2023');axes[0].set_ylabel('Patent count contribution')
    axes[1].set_title('Hardware-only share of AI grants, 2021–2023');axes[1].yaxis.set_major_formatter(PercentFormatter(1))
    fig.tight_layout();figure(fig,out,'06_volume_mix_and_hardware')
    unique=d.drop_duplicates('doc_id') # audited invariant metadata; pooled summary only
    dump_json({'unique_patents':len(unique),'ai50_unique':int(unique.predict50_any_ai.sum()),
        'ai86_unique':int(unique.predict86_any_ai.sum()),'ai93_unique':int(unique.predict93_any_ai.sum()),
        'main_period_records':int(d.analysis_2010_2023.sum()),'recent_records':len(recent),
        'main_period_min_company_year_n':int(a[a.year.between(2010,2023)].total_patents.min()),
        'main_period_min_observed_months':int(q.observed_months.min()),
        'borderline86_records':int(d.score_borderline_86.sum())},out/'eda_summary.json')
    log(out,'03','Counts and proportions change differently; several large annual volume jumps occur.',
        'A lower AI count may reflect portfolio contraction rather than declining AI concentration.',
        'Show both metrics and decompose 2021-2023 count changes symmetrically.',
        'Counts measure grant output; shares condition on captured portfolio size; the identity avoids attributing mix effects to volume.',
        'See annual metrics, anomaly flags, and count_share_decomposition.csv; no outlier rows removed.',
        'The decomposition is arithmetic, not causal; changes in capture and patenting strategy remain possible.')
    log(out,'03','Recent technology profiles and early-to-recent contrasts show company differences.',
        'Machine learning share may rise despite a flat broad any-AI share; NVIDIA may shift from hardware/vision toward ML.',
        'Freeze 10 exploratory primary tests: five company slopes for any AI and five for ML at 86%, 2010-2023.',
        'All companies/outcomes are included; thresholds, windows, and exclusions are robustness checks, not extra discovery tests.',
        'Hypotheses recorded before statistical stage; this is post-EDA exploratory analysis, not independent confirmation.',
        'Using the same dataset to form and test hypotheses limits confirmatory interpretation.')
    log(out,'03','Labels co-occur within documents.',
        'ML might overlap strongly with vision or knowledge processing in particular firms.',
        'Report Jaccard and phi on all recent portfolio records, no association p-values.',
        'Jaccard describes overlapping labels; phi describes binary association; conditioning on AI could induce associations.',
        '140 company-component-pair estimates exported for follow-up.',
        'These are classifier associations, with shared text/model errors and confounding, not technological causal links.')
    log(out,'03','IBM 2022 count contraction has a relevant published company explanation.',
        'A selective patenting strategy could contribute to the observed contraction.',
        'Retain the break; cite IBM Research January 2023 and inspect monthly/assignee continuity.',
        'External primary context helps investigate an anomaly; it does not validate every captured patent or identify the effect of strategy.',
        'All main-period company-years span 12 observed months; the drop is not a missing-calendar-month artifact.',
        'Complete months do not prove complete counts; the source merge and entity mapping remain unaudited upstream.')
    print('EDA tables and six figures written.')

if __name__=='__main__':main()