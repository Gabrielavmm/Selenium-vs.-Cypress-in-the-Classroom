import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def parse_pct(val):
    if pd.isna(val): return np.nan
    s = str(val).strip().replace('%', '').replace(',', '.').rstrip('%').strip()
    try:
        f = float(s)
        return f * 100 if (f <= 1.0 and '.' in s) else f
    except:
        return np.nan

def normalize_tool(t):
    t = str(t).strip().lower()
    if 'cypress' in t: return 'Cypress'
    if 'sel' in t:     return 'Selenium'
    return None

files = {
    'S1': '../../data/code-analysis-results/S1.csv',
    'S2': '../../data/code-analysis-results/S2.csv',
    'S3': '../../data/code-analysis-results/S3.csv',
    'S4': '../../data/code-analysis-results/S4.csv',
    'S5': '../../data/code-analysis-results/S5.csv',
}

records = []
for sem, path in files.items():
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df['ID da Dupla'] = df['ID da Dupla'].replace('', np.nan).ffill()
    df['tool_norm'] = df['Ferramenta'].apply(normalize_tool)
    df = df[df['tool_norm'].notna()].copy()
    df['flr'] = df['fragile_locator_rate'].apply(parse_pct)
    linhas_col = 'linhas' if 'linhas' in df.columns else 'Linhas'
    df['lines'] = pd.to_numeric(df[linhas_col], errors='coerce')
    df['semester'] = sem
    records.append(df[['ID da Dupla', 'semester', 'tool_norm', 'flr', 'lines']])

all_data = pd.concat(records, ignore_index=True)


def weighted_mean(group):
    g = group[group['flr'].notna() & group['lines'].notna() & (group['lines'] > 0)]
    return np.average(g['flr'], weights=g['lines']) if len(g) > 0 else np.nan

cy_agg  = all_data[all_data['tool_norm'] == 'Cypress'].groupby(['ID da Dupla','semester']).apply(weighted_mean).reset_index(name='flr_cy')
sel_agg = all_data[all_data['tool_norm'] == 'Selenium'].groupby(['ID da Dupla','semester']).apply(weighted_mean).reset_index(name='flr_sel')

pairs = cy_agg.merge(sel_agg, on=['ID da Dupla','semester']).dropna(subset=['flr_cy','flr_sel'])

print(f"Valid pairs: {len(pairs)}\n")
print(f"{'':10} {'Mean':>8} {'Median':>8} {'Std':>8}")
print(f"{'Cypress':10} {pairs['flr_cy'].mean():>7.1f}% {pairs['flr_cy'].median():>7.1f}% {pairs['flr_cy'].std():>7.1f}%")
print(f"{'Selenium':10} {pairs['flr_sel'].mean():>7.1f}% {pairs['flr_sel'].median():>7.1f}% {pairs['flr_sel'].std():>7.1f}%")


stat, p_val = stats.wilcoxon(pairs['flr_cy'], pairs['flr_sel'], alternative='two-sided', zero_method='wilcox')
n_eff = len((pairs['flr_sel'] - pairs['flr_cy']).pipe(lambda d: d[d != 0]))
r = 1 - (2 * stat) / (n_eff * (n_eff + 1))

print(f"\n── Overall (Wilcoxon Signed-Rank) ──")
print(f"W = {stat:.1f},  p = {p_val:.2e},  r = {r:.3f}  ({'large' if abs(r)>=0.5 else 'medium' if abs(r)>=0.3 else 'small'} effect)")


print(f"\n── Per Semester ──")
print(f"{'Sem':>4} {'n':>4} {'W':>8} {'p':>10} {'r':>6}")
for sem in sorted(pairs['semester'].unique()):
    sub = pairs[pairs['semester'] == sem]
    s, p = stats.wilcoxon(sub['flr_cy'], sub['flr_sel'], alternative='two-sided')
    d = (sub['flr_sel'] - sub['flr_cy']).pipe(lambda x: x[x != 0])
    r_s = 1 - (2 * s) / (len(d) * (len(d) + 1))
    sig = '*' if p < 0.05 else ''
    print(f"{sem:>4} {len(sub):>4} {s:>8.0f} {p:>10.4f} {r_s:>6.3f} {sig}")