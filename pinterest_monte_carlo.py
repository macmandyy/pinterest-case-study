import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.ticker import FuncFormatter
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# STYLE CONFIGURATION
# ============================================================
NAVY = '#0D1B3E'
DARK_BG = '#111827'
BLUE = '#1565C0'
ACCENT = '#42A5F5'
LIGHT_BLUE = '#90CAF9'
GREEN = '#2E7D32'
RED = '#C62828'
GOLD = '#F9A825'
PURPLE = '#7B1FA2'
TEXT = '#C8D6E5'
MUTED = '#5C6B7A'

plt.rcParams.update({
    'figure.facecolor': DARK_BG,
    'axes.facecolor': '#1A2332',
    'axes.edgecolor': '#2A3A4E',
    'axes.labelcolor': TEXT,
    'text.color': TEXT,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'grid.color': '#1E2D3D',
    'grid.alpha': 0.5,
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
})

dollar_fmt = FuncFormatter(lambda x, p: f'${x:,.0f}M')
pct_fmt = FuncFormatter(lambda x, p: f'{x:.0%}')

# ============================================================
# SIMULATION PARAMETERS
# ============================================================
np.random.seed(42)
N_SIMULATIONS = 10000

# Base year (2025 actuals)
BASE_US_REV = 3173
BASE_EU_REV = 775
BASE_ROW_REV = 274
BASE_TOTAL = 4222

# Parameter distributions
params = {
    'us_arpu_growth':   {'mean': 0.03, 'std': 0.06,  'label': 'US ARPU Growth'},
    'eu_arpu_growth':   {'mean': 0.15, 'std': 0.08,  'label': 'Europe ARPU Growth'},
    'row_arpu_growth':  {'mean': 0.25, 'std': 0.10,  'label': 'ROW ARPU Growth'},
    'mau_growth':       {'mean': 0.08, 'std': 0.04,  'label': 'MAU Growth'},
    'engagement_chg':   {'mean': -0.03,'std': 0.07,  'label': 'Engagement Change'},
    'ad_price_chg':     {'mean': -0.10,'std': 0.08,  'label': 'Ad Price Change'},
}

# ============================================================
# RUN SIMULATION
# ============================================================
results = []
all_params = {k: [] for k in params}

for _ in range(N_SIMULATIONS):
    draws = {}
    for k, v in params.items():
        draw = np.random.normal(v['mean'], v['std'])
        draws[k] = draw
        all_params[k].append(draw)
    
    volume_factor = (1 + draws['mau_growth']) * (1 + draws['engagement_chg'])
    us_rev = BASE_US_REV * volume_factor * (1 + draws['us_arpu_growth'])
    eu_rev = BASE_EU_REV * volume_factor * (1 + draws['eu_arpu_growth'])
    row_rev = BASE_ROW_REV * volume_factor * (1 + draws['row_arpu_growth'])
    total = us_rev + eu_rev + row_rev
    
    results.append({
        'total_revenue': total,
        'us_revenue': us_rev,
        'eu_revenue': eu_rev,
        'row_revenue': row_rev,
        **draws
    })

df = pd.DataFrame(results)

# ============================================================
# STATISTICS
# ============================================================
mean_rev = df['total_revenue'].mean()
median_rev = df['total_revenue'].median()
std_rev = df['total_revenue'].std()
p5 = df['total_revenue'].quantile(0.05)
p25 = df['total_revenue'].quantile(0.25)
p75 = df['total_revenue'].quantile(0.75)
p95 = df['total_revenue'].quantile(0.95)
prob_below_4000 = (df['total_revenue'] < 4000).mean()
prob_below_3500 = (df['total_revenue'] < 3500).mean()
prob_above_5000 = (df['total_revenue'] > 5000).mean()
prob_above_5500 = (df['total_revenue'] > 5500).mean()

print("=" * 60)
print("PINTEREST MONTE CARLO SIMULATION RESULTS")
print(f"({N_SIMULATIONS:,} simulations)")
print("=" * 60)
print(f"\n  Mean Revenue:        ${mean_rev:,.0f}M")
print(f"  Median Revenue:      ${median_rev:,.0f}M")
print(f"  Std Deviation:       ${std_rev:,.0f}M")
print(f"\n  5th Percentile:      ${p5:,.0f}M  (downside)")
print(f"  25th Percentile:     ${p25:,.0f}M")
print(f"  75th Percentile:     ${p75:,.0f}M")
print(f"  95th Percentile:     ${p95:,.0f}M  (upside)")
print(f"\n  P(Revenue < $4,000M): {prob_below_4000:.1%}")
print(f"  P(Revenue < $3,500M): {prob_below_3500:.1%}")
print(f"  P(Revenue > $5,000M): {prob_above_5000:.1%}")
print(f"  P(Revenue > $5,500M): {prob_above_5500:.1%}")
print(f"\n  Current Revenue:     ${BASE_TOTAL:,}M")
print(f"  P(Revenue declines): {(df['total_revenue'] < BASE_TOTAL).mean():.1%}")
print("=" * 60)

# ============================================================
# CHART 1: Revenue Distribution Histogram
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))

n, bins, patches = ax.hist(df['total_revenue'], bins=60, color=ACCENT, alpha=0.7, edgecolor='none')
for patch, left_edge in zip(patches, bins[:-1]):
    if left_edge < BASE_TOTAL:
        patch.set_facecolor(RED)
        patch.set_alpha(0.6)
    elif left_edge > 5000:
        patch.set_facecolor(GREEN)
        patch.set_alpha(0.6)

ax.axvline(mean_rev, color=GOLD, linewidth=2, linestyle='--', label=f'Mean: ${mean_rev:,.0f}M')
ax.axvline(BASE_TOTAL, color='white', linewidth=1.5, linestyle=':', alpha=0.7, label=f'Current: ${BASE_TOTAL:,}M')
ax.axvline(p5, color=RED, linewidth=1.5, linestyle='--', alpha=0.7, label=f'5th %ile: ${p5:,.0f}M')
ax.axvline(p95, color=GREEN, linewidth=1.5, linestyle='--', alpha=0.7, label=f'95th %ile: ${p95:,.0f}M')

ax.set_xlabel('Projected Revenue ($M)', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.set_title('Monte Carlo Revenue Distribution — 10,000 Simulations', fontsize=16, pad=15)
ax.xaxis.set_major_formatter(dollar_fmt)
ax.legend(fontsize=10, loc='upper right', facecolor='#1A2332', edgecolor='#2A3A4E', labelcolor=TEXT)
ax.grid(True, axis='y', alpha=0.3)

# Add probability annotations
ax.annotate(f'{prob_below_4000:.0%} chance\nbelow $4B', 
            xy=(3800, max(n)*0.5), fontsize=11, color=RED, fontweight='bold', ha='center')
ax.annotate(f'{prob_above_5000:.0%} chance\nabove $5B', 
            xy=(5300, max(n)*0.3), fontsize=11, color=GREEN, fontweight='bold', ha='center')

plt.tight_layout()
plt.savefig('/home/claude/chart1_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 1 saved")

# ============================================================
# CHART 2: Tornado / Sensitivity Chart
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))

sensitivities = {}
for param_name, param_info in params.items():
    col = df[param_name]
    low_mask = col <= col.quantile(0.10)
    high_mask = col >= col.quantile(0.90)
    low_rev = df.loc[low_mask, 'total_revenue'].mean()
    high_rev = df.loc[high_mask, 'total_revenue'].mean()
    sensitivities[param_info['label']] = {'low': low_rev, 'high': high_rev, 'spread': high_rev - low_rev}

sorted_sens = sorted(sensitivities.items(), key=lambda x: x[1]['spread'], reverse=True)

labels = [s[0] for s in sorted_sens]
low_vals = [s[1]['low'] - mean_rev for s in sorted_sens]
high_vals = [s[1]['high'] - mean_rev for s in sorted_sens]
y_pos = range(len(labels))

ax.barh(y_pos, high_vals, height=0.6, color=GREEN, alpha=0.7, label='High scenario (90th %ile)')
ax.barh(y_pos, low_vals, height=0.6, color=RED, alpha=0.7, label='Low scenario (10th %ile)')
ax.axvline(0, color='white', linewidth=1, alpha=0.5)

ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=11)
ax.set_xlabel('Revenue Impact vs. Mean ($M)', fontsize=12)
ax.set_title('Tornado Chart — Which Variables Move the Needle Most?', fontsize=16, pad=15)
ax.xaxis.set_major_formatter(dollar_fmt)
ax.legend(fontsize=10, loc='lower right', facecolor='#1A2332', edgecolor='#2A3A4E', labelcolor=TEXT)
ax.grid(True, axis='x', alpha=0.3)

for i, (label, vals) in enumerate(sorted_sens):
    spread = vals['spread']
    ax.annotate(f'${spread:,.0f}M spread', xy=(max(high_vals) + 30, i), 
                fontsize=9, color=GOLD, va='center')

plt.tight_layout()
plt.savefig('/home/claude/chart2_tornado.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 2 saved")

# ============================================================
# CHART 3: Regional Revenue Distribution (Violin + Box)
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))

plot_data = pd.melt(df[['us_revenue', 'eu_revenue', 'row_revenue']], 
                     var_name='Region', value_name='Revenue')
plot_data['Region'] = plot_data['Region'].map({
    'us_revenue': 'US & Canada',
    'eu_revenue': 'Europe', 
    'row_revenue': 'Rest of World'
})

palette = {'US & Canada': BLUE, 'Europe': ACCENT, 'Rest of World': LIGHT_BLUE}
parts = ax.violinplot([df['us_revenue'], df['eu_revenue'], df['row_revenue']], 
                       positions=[1, 2, 3], showmedians=True, showextrema=False)

colors = [BLUE, ACCENT, LIGHT_BLUE]
for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(colors[i])
    pc.set_alpha(0.6)
parts['cmedians'].set_color(GOLD)
parts['cmedians'].set_linewidth(2)

# Add current revenue markers
current = [BASE_US_REV, BASE_EU_REV, BASE_ROW_REV]
for i, val in enumerate(current):
    ax.scatter(i+1, val, color='white', s=80, zorder=5, marker='D', edgecolors=GOLD, linewidths=1.5)

ax.set_xticks([1, 2, 3])
ax.set_xticklabels(['US & Canada', 'Europe', 'Rest of World'], fontsize=12)
ax.set_ylabel('Revenue ($M)', fontsize=12)
ax.set_title('Regional Revenue Distribution — Where Does Risk Live?', fontsize=16, pad=15)
ax.yaxis.set_major_formatter(dollar_fmt)
ax.grid(True, axis='y', alpha=0.3)

diamond = plt.scatter([], [], color='white', s=80, marker='D', edgecolors=GOLD, linewidths=1.5, label='2025 Actual')
ax.legend(handles=[diamond], fontsize=10, loc='upper right', facecolor='#1A2332', edgecolor='#2A3A4E', labelcolor=TEXT)

plt.tight_layout()
plt.savefig('/home/claude/chart3_violin.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 3 saved")

# ============================================================
# CHART 4: Cumulative Probability (S-Curve)
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))

sorted_rev = np.sort(df['total_revenue'])
cumprob = np.arange(1, len(sorted_rev) + 1) / len(sorted_rev)

ax.plot(sorted_rev, cumprob, color=ACCENT, linewidth=2.5)
ax.fill_between(sorted_rev, cumprob, alpha=0.1, color=ACCENT)

# Key thresholds
for threshold, label, color in [
    (3500, '$3.5B', RED), (4000, '$4.0B', RED), 
    (4222, 'Current\n($4.2B)', 'white'),
    (5000, '$5.0B', GREEN), (5500, '$5.5B', GREEN)
]:
    prob = (df['total_revenue'] <= threshold).mean()
    ax.axvline(threshold, color=color, linewidth=1, linestyle=':', alpha=0.5)
    ax.scatter(threshold, prob, color=color, s=50, zorder=5)
    ax.annotate(f'{label}\n{prob:.0%}', xy=(threshold, prob), xytext=(threshold+80, prob+0.05),
                fontsize=9, color=color, fontweight='bold', ha='left',
                arrowprops=dict(arrowstyle='->', color=color, lw=1) if threshold == 4222 else None)

ax.set_xlabel('Revenue ($M)', fontsize=12)
ax.set_ylabel('Cumulative Probability', fontsize=12)
ax.set_title('Cumulative Probability Distribution — What Are the Odds?', fontsize=16, pad=15)
ax.xaxis.set_major_formatter(dollar_fmt)
ax.yaxis.set_major_formatter(pct_fmt)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/home/claude/chart4_cdf.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 4 saved")

# ============================================================
# CHART 5: Parameter Correlation Heatmap
# ============================================================
fig, ax = plt.subplots(figsize=(10, 8))

param_cols = list(params.keys())
param_labels = [params[k]['label'] for k in param_cols]
corr_with_rev = df[param_cols + ['total_revenue']].corr()['total_revenue'][param_cols]

corr_matrix = df[param_cols].corr()
corr_matrix.index = param_labels
corr_matrix.columns = param_labels

sns.heatmap(corr_matrix, annot=True, fmt='.2f', center=0,
            cmap='RdBu_r', ax=ax, linewidths=0.5,
            cbar_kws={'label': 'Correlation', 'shrink': 0.8},
            annot_kws={'size': 11, 'color': 'white'})

ax.set_title('Parameter Correlation Matrix', fontsize=16, pad=15)
plt.tight_layout()
plt.savefig('/home/claude/chart5_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 5 saved")

# ============================================================
# CHART 6: Scatter — Revenue vs Key Driver
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

scatter_params = [
    ('mau_growth', 'MAU Growth', BLUE),
    ('us_arpu_growth', 'US ARPU Growth', ACCENT),
    ('engagement_chg', 'Engagement Change', PURPLE)
]

for ax, (param, label, color) in zip(axes, scatter_params):
    ax.scatter(df[param], df['total_revenue'], alpha=0.08, s=8, color=color)
    
    # Trend line
    z = np.polyfit(df[param], df['total_revenue'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df[param].min(), df[param].max(), 100)
    ax.plot(x_line, p(x_line), color=GOLD, linewidth=2, linestyle='--')
    
    ax.set_xlabel(label, fontsize=11)
    ax.set_ylabel('Total Revenue ($M)' if ax == axes[0] else '', fontsize=11)
    ax.xaxis.set_major_formatter(pct_fmt)
    ax.yaxis.set_major_formatter(dollar_fmt)
    ax.grid(True, alpha=0.3)
    
    corr = df[param].corr(df['total_revenue'])
    ax.set_title(f'{label}\nr = {corr:.3f}', fontsize=12, pad=10)

fig.suptitle('Revenue Sensitivity to Key Drivers', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('/home/claude/chart6_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 6 saved")

print("\nAll charts generated successfully.")
