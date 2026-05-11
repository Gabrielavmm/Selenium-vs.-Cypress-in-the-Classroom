"""
Cypress vs Selenium — Wilcoxon Signed-Rank Tests
Group 1: test_case_count, assertion_conformity, interaction_conformity
Group 2: fragile_locator_rate, avg_assertions
Group 3: unsafe_chain, max_lines_per_function, unused_var, hard_coded,
         fixed_wait, await_loop, no_only_test, max_statements
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Helpers ────────────────────────────────────────────────────────────────

def parse_pct(val):
    if pd.isna(val): return np.nan
    s = str(val).strip().replace('%', '').replace(',', '.').rstrip('%').strip()
    try:
        f = float(s)
        return f * 100 if (f <= 1.0 and '.' in s) else f
    except: return np.nan

def parse_num(val):
    try:
        if pd.isna(val): return np.nan
    except: pass
    try: return float(str(val).strip().replace(',', '.'))
    except: return np.nan

def normalize_tool(t):
    t = str(t).strip().lower()
    if 'cypress' in t: return 'Cypress'
    if 'sel' in t:     return 'Selenium'
    return None

def wilcoxon_summary(a, b, label):
    mask = ~(np.isnan(a) | np.isnan(b))
    a, b = a[mask], b[mask]
    stat, p = stats.wilcoxon(a, b, alternative='two-sided', zero_method='wilcox')
    n_eff = int((b - a != 0).sum())
    r = 1 - (2 * stat) / (n_eff * (n_eff + 1))
    mag = 'large' if abs(r) >= 0.5 else 'medium' if abs(r) >= 0.3 else 'small'
    print(f"\n{'─'*55}")
    print(f"  {label}  (n={len(a)})")
    print(f"{'─'*55}")
    print(f"  Cypress   mean={a.mean():.2f}  median={np.median(a):.2f}  std={a.std():.2f}")
    print(f"  Selenium  mean={b.mean():.2f}  median={np.median(b):.2f}  std={b.std():.2f}")
    print(f"  W={stat:.1f},  p={p:.2e},  r={r:.3f}  ({mag} effect)")
    print(f"\n  {'Sem':>4} {'n':>4} {'W':>8} {'p':>10} {'r':>6}")

def wilcoxon_per_sem(pairs, col_cy, col_sel):
    for sem in sorted(pairs['semester'].unique()):
        sub = pairs[pairs['semester'] == sem].dropna(subset=[col_cy, col_sel])
        if len(sub) < 5:
            print(f"  {sem:>4} {len(sub):>4}  — insufficient sample")
            continue
        try:
            s, p = stats.wilcoxon(sub[col_cy], sub[col_sel], alternative='two-sided')
            d = (sub[col_sel] - sub[col_cy]).pipe(lambda x: x[x != 0])
            r_s = 1 - (2 * s) / (len(d) * (len(d) + 1))
            sig = '*' if p < 0.05 else ''
            print(f"  {sem:>4} {len(sub):>4} {s:>8.0f} {p:>10.4f} {r_s:>6.3f} {sig}")
        except Exception as e:
            print(f"  {sem:>4}  error: {e}")

# ── Data Loading ───────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parents[2]

files = {
    'S1': BASE_DIR / 'data/code-analysis-results/S1.csv',
    'S2': BASE_DIR / 'data/code-analysis-results/S2.csv',
    'S3': BASE_DIR / 'data/code-analysis-results/S3.csv',
    'S4': BASE_DIR / 'data/code-analysis-results/S4.csv',
    'S5': BASE_DIR / 'data/code-analysis-results/S5.csv',
}

col_map = {
    'smell_hard_coded':       'hard_coded',
    'eslint_cy_wait_fixo':    'fixed_wait',
    'eslint_unsafe_chain':    'unsafe_chain',
    'eslint_await_loop':      'await_loop',
    'eslint_no_only_test':    'no_only_test',
    'eslint_no_unsed_var':    'unused_var',
    'max-lines-per-function': 'max_lines_per_function',
    'max-statements':         'max_statements',
}

num_cols = ['test_case_count', 'avg_assertions', 'hard_coded', 'fixed_wait',
            'unsafe_chain', 'await_loop', 'no_only_test', 'unused_var',
            'max_lines_per_function', 'max_statements']

records = []
for sem, path in files.items():
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    # Handle duplicate columns (e.g. eslint_unsafe_chain in S5)
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    df = df.rename(columns=col_map)
    df['ID da Dupla'] = df['ID da Dupla'].replace('', np.nan).ffill()
    df['tool_norm'] = df['Ferramenta'].apply(normalize_tool)
    df = df[df['tool_norm'].notna()].copy()
    linhas_col = 'linhas' if 'linhas' in df.columns else 'Linhas'
    df['lines']                  = pd.to_numeric(df[linhas_col], errors='coerce')
    df['total_locators']         = pd.to_numeric(df['total_locators'], errors='coerce')
    df['fragile_locator_rate']   = df['fragile_locator_rate'].apply(parse_pct)
    df['assertion_conformity']   = df['assertion_conformity'].apply(parse_pct)
    df['interaction_conformity'] = df['interaction_conformity'].apply(parse_pct)

    # FLR = 0% when total_locators is known but FLR is missing (no fragile locators)
    df.loc[df['fragile_locator_rate'].isna() & df['total_locators'].notna(),
           'fragile_locator_rate'] = 0.0

    for c in num_cols:
        if c not in df.columns: df[c] = np.nan
        df[c] = df[c].apply(parse_num)
    df['semester'] = sem

    keep = ['ID da Dupla', 'semester', 'tool_norm', 'lines', 'total_locators',
            'fragile_locator_rate', 'assertion_conformity', 'interaction_conformity'] + num_cols
    records.append(df[keep])

all_data = pd.concat(records, ignore_index=True)

# ── Aggregation per pair ───────────────────────────────────────────────────

cy  = all_data[all_data['tool_norm'] == 'Cypress']
sel = all_data[all_data['tool_norm'] == 'Selenium']

def flr_wmean(g):
    # pairs with all locators=0 get FLR=0
    if (g['total_locators'] == 0).all():
        return 0.0
    v = g[g['fragile_locator_rate'].notna() & g['lines'].notna() & (g['lines'] > 0)]
    return np.average(v['fragile_locator_rate'], weights=v['lines']) if len(v) > 0 else np.nan

cy_agg  = cy.groupby(['ID da Dupla','semester']).apply(flr_wmean).reset_index(name='fragile_locator_rate_cy')
sel_agg = sel.groupby(['ID da Dupla','semester']).apply(flr_wmean).reset_index(name='fragile_locator_rate_sel')

simple_metrics = ['test_case_count', 'assertion_conformity', 'interaction_conformity',
                  'avg_assertions', 'hard_coded', 'fixed_wait', 'unsafe_chain',
                  'await_loop', 'no_only_test', 'unused_var',
                  'max_lines_per_function', 'max_statements']

for metric in simple_metrics:
    cy_agg  = cy_agg.merge(
        cy.groupby(['ID da Dupla','semester'])[metric].mean().reset_index(name=f'{metric}_cy'),
        on=['ID da Dupla','semester'], how='left')
    sel_agg = sel_agg.merge(
        sel.groupby(['ID da Dupla','semester'])[metric].mean().reset_index(name=f'{metric}_sel'),
        on=['ID da Dupla','semester'], how='left')

pairs = cy_agg.merge(sel_agg, on=['ID da Dupla','semester'])

# ── Tests ──────────────────────────────────────────────────────────────────

print("=" * 55)
print("  WILCOXON SIGNED-RANK TESTS — Cypress vs Selenium")
print("=" * 55)

groups = [
    ("GROUP 1: Conformance", [
        ('test_case_count_cy',        'test_case_count_sel',        'Test Case Count'),
        ('assertion_conformity_cy',   'assertion_conformity_sel',   'Assertion Conformity (%)'),
        ('interaction_conformity_cy', 'interaction_conformity_sel', 'Interaction Conformity (%)'),
    ]),
    ("GROUP 2: Complexity & Locator Fragility", [
        ('fragile_locator_rate_cy',   'fragile_locator_rate_sel',   'Fragile Locator Rate (%)'),
        ('avg_assertions_cy',         'avg_assertions_sel',         'Avg Assertions per Test'),
    ]),
    ("GROUP 3: Test Smells", [
        ('unsafe_chain_cy',           'unsafe_chain_sel',           'unsafe_chain'),
        ('max_lines_per_function_cy', 'max_lines_per_function_sel', 'max_lines_per_function'),
        ('unused_var_cy',             'unused_var_sel',             'unused_var'),
        ('hard_coded_cy',             'hard_coded_sel',             'hard_coded'),
        ('fixed_wait_cy',             'fixed_wait_sel',             'fixed_wait'),
        ('await_loop_cy',             'await_loop_sel',             'await_loop'),
        ('no_only_test_cy',           'no_only_test_sel',           'no_only_test'),
        ('max_statements_cy',         'max_statements_sel',         'max_statements'),
    ]),
]

for group_label, metrics in groups:
    print(f"\n{'='*55}")
    print(f"  {group_label}")
    print(f"{'='*55}")
    for col_cy, col_sel, label in metrics:
        sub = pairs.dropna(subset=[col_cy, col_sel])
        try:
            wilcoxon_summary(sub[col_cy].values, sub[col_sel].values, label)
            wilcoxon_per_sem(sub, col_cy, col_sel)
        except Exception as e:
            print(f"\n  {label}: could not compute — {e}")