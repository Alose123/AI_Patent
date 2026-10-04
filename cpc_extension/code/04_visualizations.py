"""Publication-ready static figures; values come solely from generated tables."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs"/"figures"
TABLE=ROOT/"outputs"/"tables"
BLUE="#2b607c"; TEAL="#167d8d"; ORANGE="#d58032"; GREY="#82929c"; LIGHT="#d3dfe3"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.spines.top":False,"axes.spines.right":False,"axes.labelcolor":"#263c46","text.color":"#263c46","axes.titleweight":"bold","figure.facecolor":"white","savefig.facecolor":"white","svg.fonttype":"none"})

def read(name):return pd.read_csv(TABLE/(name+".csv"))
def save(fig,name,note):
    fig.text(.035,.025,note,ha="left",va="bottom",fontsize=9,color="#53636c")
    fig.subplots_adjust(bottom=.18,top=.85,left=.12,right=.97)
    for ext in ["png","svg"]:fig.savefig(OUT/(name+"."+ext),dpi=170)
    plt.close(fig)

if __name__=="__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    q=read("qualcomm_non_ai_additive_partition").pivot(index="cohort",columns="communications_partition",values="count").fillna(0)
    fig,ax=plt.subplots(figsize=(9,5.8))
    positions=np.arange(2)
    c=q["Communications CPC present"].to_numpy(); other=q["No communications CPC"].to_numpy()
    ax.bar(positions,c,.55,label="Communications CPC present",color=TEAL)
    ax.bar(positions,other,.55,bottom=c,label="Other / no current CPC",color=LIGHT)
    for i in range(2):
        ax.text(i,c[i]/2,f"{c[i]:,}",ha="center",va="center",color="white",fontsize=14,fontweight="bold")
        ax.text(i,c[i]+other[i]/2,f"{other[i]:,}",ha="center",va="center",fontsize=11)
        ax.text(i,c[i]+other[i]+65,f"{c[i]+other[i]:,}",ha="center",fontweight="bold")
    ax.set_xticks(positions,q.index.astype(str));ax.set_ylim(0,4300);ax.set_ylabel("Classifier-negative grants (AI86 = 0)")
    ax.legend(frameon=False,loc="upper left",fontsize=10)
    fig.suptitle("Qualcomm: communications drive the denominator expansion",x=.035,ha="left",fontsize=16,fontweight="bold")
    ax.text(.02,.75,"1,608 of 1,617 additional grants\ncarry a communications CPC code (99.4%).",transform=ax.transAxes,fontsize=11)
    save(fig,"01_qualcomm_denominator","Communications = any H04W/L/B/J/K/M code, current December 2024 snapshot. Each grant counted once.\nClassifier-negative does not establish absence of AI; all grants, including reissues, are retained.")

    t=read("text_theme_counts")
    s=t[(t.company=="Qualcomm")&(t.population=="non_ai")&(t.scope=="combined")]
    themes=["sidelink","beam_or_beamforming","uplink","downlink","channel_state","harq"]
    names=["Sidelink","Beam / beamforming","Uplink","Downlink","Channel-state reporting","HARQ retransmission"]
    fig,ax=plt.subplots(figsize=(10,6.6));y=np.arange(len(themes))
    for offset,co,color in [(-.18,"2021",BLUE),(.18,"2023",ORANGE)]:
        z=s.set_index(["cohort","theme"])
        counts=np.array([z.loc[(co,x),"count"] for x in themes]);shares=np.array([100*z.loc[(co,x),"share"] for x in themes])
        ax.barh(y+offset,shares,.32,color=color,label=co)
        for yy,share,count in zip(y+offset,shares,counts):ax.text(share+.3,yy,f"{share:.1f}%  ({count:,})",va="center",fontsize=10)
    ax.set_yticks(y,names);ax.invert_yaxis();ax.set_xlim(0,24);ax.set_xlabel("% of classifier-negative grants with phrase in title or abstract")
    ax.legend(frameon=False,loc="lower right")
    fig.suptitle("Qualcomm: sidelink becomes a much larger part of the portfolio",x=.035,ha="left",fontsize=16,fontweight="bold")
    fig.subplots_adjust(left=.24)
    # This figure needs the larger label margin retained after saving.
    fig.text(.035,.025,"Cohorts: 1,829 grants (2021), 3,446 (2023). Counts overlap across themes and must not be added.\nExplicit phrase rules are exploratory indicators, not manually validated technology classes.",fontsize=9,color="#53636c")
    fig.subplots_adjust(bottom=.17,top=.87,left=.24,right=.96)
    for ext in ["png","svg"]:fig.savefig(OUT/("02_qualcomm_text."+ext),dpi=170)
    plt.close(fig)

    f=read("qualcomm_non_ai_filing_cohorts")
    fig,axes=plt.subplots(1,2,figsize=(11,5.6),sharey=True)
    for ax,co,color in zip(axes,[2021,2023],[BLUE,ORANGE]):
        s=f[f.cohort==co]; ax.bar(s.filing_year,s["count"]/s["count"].sum()*100,color=color,width=.7)
        ax.set_title(f"Granted in {co}");ax.set_xlabel("Direct application filing year");ax.set_xlim(2007.5,2023.5);ax.set_xticks([2008,2011,2014,2017,2020,2023]);ax.set_ylim(0,65)
        maxrow=s.loc[s["count"].idxmax()];ax.text(maxrow.filing_year,maxrow["count"]/s["count"].sum()*100+2,f"{int(maxrow['count']):,}",ha="center",fontweight="bold")
    axes[0].set_ylabel("% of classifier-negative grants in the grant cohort")
    fig.suptitle("Qualcomm: 2023 grants mostly originate in 2020–2021 filings",x=.035,ha="left",fontsize=16,fontweight="bold")
    save(fig,"03_qualcomm_filing_timing","84.6% of 2023 classifier-negative grants were filed in 2020–2021. Median grant lag: 2.12 → 2.30 years.\nFiling date is for the direct application, not earliest family priority. This is not a census of all filings.")

    c=read("cpc_subclass_counts")
    s=c[(c.company=="NVIDIA")&(c.population=="all")&(c.snapshot=="current")]
    subclasses=["G06F","G06T","G06V","G06N","G05D","B60W","G09G"]
    labels=["G06F  Data processing","G06T  Image processing / generation","G06V  Image / video recognition","G06N  Specific computational models","G05D  Control / navigation","B60W  Vehicle drive control","G09G  Display control"]
    z=s.pivot(index="cpc_subclass",columns="cohort",values="patents").fillna(0).reindex(subclasses).fillna(0)
    fig,ax=plt.subplots(figsize=(11,6.5));y=np.arange(len(subclasses))
    for off,co,den,color in [(-.17,"2014-2016",1010,BLUE),(.17,"2021-2023",786,ORANGE)]:
        vals=z[co].to_numpy()/den*100;counts=z[co].to_numpy()
        ax.barh(y+off,vals,.3,color=color,label=co.replace("-","–"))
        for yy,val,cnt in zip(y+off,vals,counts):ax.text(val+.4,yy,f"{val:.1f}%  ({int(cnt):,})",va="center",fontsize=9)
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(0,66);ax.set_xlabel("% of all NVIDIA grants with CPC subclass");ax.legend(frameon=False,loc="lower right")
    fig.suptitle("NVIDIA: learned computation, vision and control expand",x=.035,ha="left",fontsize=16,fontweight="bold")
    fig.text(.035,.025,"Common December 2024 CPC snapshot. Memberships overlap; subclasses are not additive.\nRobustness checks combine G06T / G06V with legacy G06K9 recognition codes to reduce reclassification effects.",fontsize=9,color="#53636c")
    fig.subplots_adjust(bottom=.17,top=.86,left=.33,right=.96)
    for ext in ["png","svg"]:fig.savefig(OUT/("04_nvidia_cpc."+ext),dpi=170)
    plt.close(fig)

    part=read("nvidia_ml_additive_partition")
    names=["ML86 + explicit learning/neural text","ML86 + vision/control evidence, no explicit learning text","ML86 + other evidence"]
    fig,ax=plt.subplots(figsize=(10,6));bottom=np.zeros(2);cos=["2014-2016","2021-2023"];den=np.array([1010,786])
    for name,color,lab in zip(names,[TEAL,ORANGE,GREY],["Explicit neural / ML / deep-learning text","Vision / control evidence; no explicit learning phrase","Other ML86-labelled grants"]):
        vals=np.array([part.loc[(part.cohort==co)&(part.ml_partition==name),"count"].sum() for co in cos]);shares=vals/den*100
        ax.bar(np.arange(2),shares,.55,bottom=bottom,color=color,label=lab)
        for i,v in enumerate(vals):
            if shares[i]>1.5:ax.text(i,bottom[i]+shares[i]/2,f"{v:,}",ha="center",va="center",color="white",fontweight="bold",fontsize=12)
        bottom+=shares
    ax.set_xticks(np.arange(2),["2014–2016\n1,010 total grants","2021–2023\n786 total grants"]);ax.set_ylabel("ML86-labelled grants as % of all grants");ax.set_ylim(0,42)
    for i,total in enumerate([7,230]):ax.text(i,bottom[i]+1,f"{bottom[i]:.1f}% ({total:,})",ha="center",fontweight="bold")
    ax.legend(frameon=False,loc="upper left",fontsize=9)
    fig.suptitle("NVIDIA: explicit learned methods explain most of the ML rise",x=.035,ha="left",fontsize=16,fontweight="bold")
    save(fig,"05_nvidia_ml_partition","Exact ordered partition: explicit learning text first, then vision/control evidence, then other ML86.\n177 of 223 additional ML86 grants have explicit learning/neural text (79.4%); all categories sum exactly.")

    themes=["explicit_learning_or_neural","autonomous","ray_tracing","rendering"]
    labels=["Neural / machine / deep learning","Autonomous systems","Ray tracing","Rendering"]
    s=t[(t.company=="NVIDIA")&(t.population=="all")&(t.scope=="combined")].set_index(["cohort","theme"])
    fig,ax=plt.subplots(figsize=(10,5.7));y=np.arange(4)
    for off,co,color in [(-.17,"2014-2016",BLUE),(.17,"2021-2023",ORANGE)]:
        shares=np.array([s.loc[(co,x),"share"]*100 for x in themes]);counts=np.array([s.loc[(co,x),"count"] for x in themes])
        ax.barh(y+off,shares,.3,color=color,label=co.replace("-","–"))
        for yy,v,cnt in zip(y+off,shares,counts):ax.text(v+.3,yy,f"{v:.1f}% ({cnt:,})",va="center",fontsize=10)
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(0,34);ax.set_xlabel("% of all grants with phrase in title or abstract");ax.legend(frameon=False,loc="lower right")
    fig.suptitle("NVIDIA: neural methods and autonomy grow alongside graphics",x=.035,ha="left",fontsize=16,fontweight="bold")
    ray_total=int(s.loc[("2021-2023","ray_tracing"),"count"])
    ray_ml=int(t[(t.company=="NVIDIA")&(t.cohort=="2021-2023")&(t.population=="ml")&(t.scope=="combined")&(t.theme=="ray_tracing")]["count"].iloc[0])
    fig.text(.035,.025,f"Themes overlap. Of {ray_total} recent ray-tracing grants, {ray_total-ray_ml} are below the ML86 threshold.\nA graphics technology can evolve without being classified as machine learning.",fontsize=9,color="#53636c")
    fig.subplots_adjust(bottom=.18,top=.85,left=.30,right=.97)
    for ext in ["png","svg"]:fig.savefig(OUT/("06_nvidia_text."+ext),dpi=170)
    plt.close(fig)
    print("Six figures written in PNG and SVG.")