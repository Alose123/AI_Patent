"""Shared settings, I/O, and numerical methods for the patent study."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import importlib
import numpy as np
import pandas as pd
from scipy import stats

COMPANIES = ['IBM', 'NVIDIA', 'Qualcomm', 'Google', 'Microsoft']
COMPONENTS = ['ml', 'evo', 'nlp', 'speech', 'vision', 'planning', 'kr', 'hardware']
LABELS = {'ml': 'Machine learning', 'evo': 'Evolutionary computation',
          'nlp': 'Natural language processing', 'speech': 'Speech', 'vision': 'Vision',
          'planning': 'Planning and control', 'kr': 'Knowledge processing',
          'hardware': 'AI hardware'}
THRESHOLDS = [50, 86, 93]
REFERENCE_SOURCE_SHA256 = 'd34cf61d30554b30ddb6d8e7f06f7a3bc130799f643f95aef6c282d53de69e79'
ID_COLS = ['doc_id', 'appl_id', 'patent_id', 'assignee_id', 'location_id']
DOC_COLS = ['doc_id', 'flag_patent', 'pub_dt', 'appl_id'] + [
    c for t in THRESHOLDS for c in [f'predict{t}_any_ai'] +
    [f'predict{t}_{k}' for k in COMPONENTS]] + [f'ai_score_{k}' for k in COMPONENTS]

def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.input = args.input.resolve()
    args.output = args.output.resolve()
    for sub in ['', 'tables', 'figures']:
        (args.output / sub).mkdir(parents=True, exist_ok=True)
    return args

def read_source(path):
    return pd.read_csv(path, dtype={c: 'string' for c in ID_COLS}, low_memory=False, float_precision='round_trip')

def read_clean(out):
    return pd.read_csv(out / 'clean_patent_company.csv.gz',
                       dtype={c: 'string' for c in ID_COLS}, low_memory=False, float_precision='round_trip')

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def dump_json(value, path):
    def encode(o):
        if isinstance(o, np.generic): return o.item()
        if isinstance(o, (Path, pd.Timestamp)): return str(o)
        raise TypeError(type(o).__name__)
    path.write_text(json.dumps(value, indent=2, default=encode), encoding='utf-8')

def save_table(data, out, name):
    data.to_csv(out / 'tables' / f'{name}.csv', index=False, float_format='%.10g')

def log(out, stage, observation, hypothesis, decision, justification, result, limitation):
    record = dict(stage=stage, observation=observation, hypothesis=hypothesis,
                  decision=decision, justification=justification, result=result,
                  limitation=limitation)
    with open(out / 'research_log.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')

def aggregate(d):
    """Full credit per observed company; no pooling of co-assignee rows."""
    counts = [f'predict{t}_{k}' for t in THRESHOLDS for k in ['any_ai'] + COMPONENTS]
    for t in THRESHOLDS:
        counts += [f'nonhardware{t}', f'hardware_only{t}', f'n_components{t}']
    g = d.groupby(['company', 'grant_year'], observed=True)
    a = g[counts].sum()
    a['total_patents'] = g.size()
    a['reissue_patents'] = g['is_reissue'].sum()
    a = a.reset_index().rename(columns={'grant_year': 'year'})
    for col in counts:
        a[col + '_share'] = a[col] / a.total_patents
    for t in THRESHOLDS:
        a[f'mean_components_per_ai{t}'] = a[f'n_components{t}'] / a[f'predict{t}_any_ai'].replace(0, np.nan)
    return a

def trend_fit(year, share, lag=2):
    """OLS on annual proportions; Newey-West/Bartlett HAC with n/(n-k).

    Time (not patents) is the analysis unit. No assumed independent Bernoulli
    trials. Confidence limits use t_(n-2), an approximate small-sample choice.
    """
    x = np.asarray(year, dtype=float)
    y = np.asarray(share, dtype=float)
    X = np.column_stack([np.ones(len(x)), x - x.mean()])
    n, k = X.shape
    bread = np.linalg.inv(X.T @ X)
    beta = bread @ X.T @ y
    e = y - X @ beta
    U = X * e[:, None]
    meat = U.T @ U
    for j in range(1, min(lag, n - 1) + 1):
        cross = U[j:].T @ U[:-j]
        meat += (1 - j / (lag + 1)) * (cross + cross.T)
    cov = bread @ meat @ bread * n / (n-k)
    se = np.sqrt(max(0, cov[1, 1]))
    crit = stats.t.ppf(.975, n-k)
    p = 2 * stats.t.sf(abs(beta[1]/se), n-k) if se else 0.0
    hat = np.sum((X @ bread) * X, axis=1)
    u3 = X * (e / (1 - hat))[:, None]
    cov3 = bread @ (u3.T @ u3) @ bread
    se3 = np.sqrt(max(0, cov3[1, 1]))
    loo = [np.polyfit(np.delete(x, i), np.delete(y, i), 1)[0] for i in range(n)]
    sst = np.sum((y-y.mean())**2)
    out = dict(slope_pp_per_year=100*beta[1], ci_low=100*(beta[1]-crit*se),
               ci_high=100*(beta[1]+crit*se), p_value=p, n_years=n,
               r_squared=1-np.sum(e**2)/sst if sst else np.nan,
               lag1_residual_corr=np.corrcoef(e[1:], e[:-1])[0,1],
               hc3_ci_low=100*(beta[1]-crit*se3), hc3_ci_high=100*(beta[1]+crit*se3),
               loo_slope_min=100*min(loo), loo_slope_max=100*max(loo),
               theil_sen_slope=100*stats.theilslopes(y, x)[0],
               fitted_min=float((X@beta).min()), fitted_max=float((X@beta).max()))
    return out, X @ beta, e

def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adjusted = np.minimum(1, np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    result = np.empty(len(p)); result[order] = adjusted
    return result

def environment():
    result = {'python': platform.python_version()}
    for name in ['pandas', 'numpy', 'scipy', 'matplotlib']:
        result[name] = importlib.import_module(name).__version__
    return result