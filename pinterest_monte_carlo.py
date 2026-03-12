"""
Pinterest Monte Carlo Revenue Simulation
=========================================
Runs 10,000 simulations to model the range of Pinterest's 
near-term revenue outcomes under uncertainty.

Data Source: Pinterest 10-K filings (FY2024, FY2025)
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ============================================================
# SETUP
# ============================================================
np.random.seed(42)
N = 10_000

# 2025 actuals from 10-K
BASE_US_REV = 3173   # US & Canada revenue ($M)
BASE_EU_REV = 775    # Europe revenue ($M)
BASE_ROW_REV = 274   # Rest of World revenue ($M)
CURRENT_TOTAL = 4222

# Simulation parameters (mean, std dev)
# Calibrated from 2021-2025 historical trends
params = {
    'us_arpu_growth':  (0.03, 0.06),   # slowing from 14% to 6%
    'eu_arpu_growth':  (0.15, 0.08),   # strong momentum, +21% in 2025
    'row_arpu_growth': (0.25, 0.10),   # fastest growing, +40% in 2025
    'mau_growth':      (0.08, 0.04),   # steady ~11-12% historically
    'engagement_chg':  (-0.03, 0.07),  # slightly negative = AI risk
    'ad_price_chg':    (-0.10, 0.08),  # prices declining 14-22% annually
}

# ============================================================
# RUN SIMULATION
# ============================================================
print(f"Running {N:,} simulations...")

results = []

for i in range(N):
    # Draw random values for each parameter
    us_arpu_g = np.random.normal(*params['us_arpu_growth'])
    eu_arpu_g = np.random.normal(*params['eu_arpu_growth'])
    row_arpu_g = np.random.normal(*params['row_arpu_growth'])
    mau_g = np.random.normal(*params['mau_growth'])
    engage = np.random.normal(*params['engagement_chg'])
    ad_price = np.random.normal(*params['ad_price_chg'])
    
    # Calculate revenue impact
    # Volume factor = more/fewer users * more/less engagement
    volume = (1 + mau_g) * (1 + engage)
    
    us_rev = BASE_US_REV * volume * (1 + us_arpu_g)
    eu_rev = BASE_EU_REV * volume * (1 + eu_arpu_g)
    row_rev = BASE_ROW_REV * volume * (1 + row_arpu_g)
    total = us_rev + eu_rev + row_rev
    
    results.append({
        'total': total,
        'us': us_rev,
        'eu': eu_rev,
        'row': row_rev,
        'mau_growth': mau_g,
        'engagement': engage,
        'us_arpu_growth': us_arpu_g,
    })

df = pd.DataFrame(results)
print("Done!\n")

# ============================================================
# SUMMARY STATISTICS
# ============================================================
print("=" * 50)
print("SIMULATION RESULTS")
print("=" * 50)
print(f"  Mean Revenue:      ${df['total'].mean():,.0f}M")
print(f"  Median Revenue:    ${df['total'].median():,.0f}M")
print(f"  Std Deviation:     ${df['total'].std():,.0f}M")
print(f"  5th Percentile:    ${df['total'].quantile(0.05):,.0f}M")
print(f"  95th Percentile:   ${df['total'].quantile(0.95):,.0f}M")
print()
print(f"  P(Rev < $4,000M):   {(df['total'] < 4000).mean():.1%}")
print(f"  P(Rev < current):   {(df['total'] < CURRENT_TOTAL).mean():.1%}")
print(f"  P(Rev > $5,000M):   {(df['total'] > 5000).mean():.1%}")
print("=" * 50)

# ============================================================
# CHART 1: Revenue Distribution
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

ax.hist(df['total'], bins=50, color='steelblue', edgecolor='white', linewidth=0.3)

# Mark key thresholds
ax.axvline(df['total'].mean(), color='orange', linewidth=2, linestyle='--', 
           label=f"Mean: ${df['total'].mean():,.0f}M")
ax.axvline(CURRENT_TOTAL, color='red', linewidth=1.5, linestyle=':', 
           label=f"Current: ${CURRENT_TOTAL:,}M")

ax.set_xlabel('Projected Revenue ($M)')
ax.set_ylabel('Frequency')
ax.set_title('Monte Carlo Revenue Distribution (10,000 Simulations)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('chart1_distribution.png', dpi=150)
plt.show()
print("Chart 1 saved.")

# ============================================================
# CHART 2: Which variables matter most? (Tornado chart)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

# For each variable, compare revenue when it's low vs high
variables = {
    'Engagement Change': 'engagement',
    'US ARPU Growth': 'us_arpu_growth',
    'MAU Growth': 'mau_growth',
}

spreads = []
labels = []
low_vals = []
high_vals = []

mean_rev = df['total'].mean()

for label, col in variables.items():
    # Revenue when this variable is in its bottom 10% vs top 10%
    low_rev = df.loc[df[col] <= df[col].quantile(0.10), 'total'].mean()
    high_rev = df.loc[df[col] >= df[col].quantile(0.90), 'total'].mean()
    
    labels.append(label)
    low_vals.append(low_rev - mean_rev)
    high_vals.append(high_rev - mean_rev)
    spreads.append(high_rev - low_rev)

# Sort by spread
order = np.argsort(spreads)
labels = [labels[i] for i in order]
low_vals = [low_vals[i] for i in order]
high_vals = [high_vals[i] for i in order]
spreads = [spreads[i] for i in order]

y_pos = range(len(labels))
ax.barh(y_pos, high_vals, color='green', alpha=0.7, label='Upside (90th %ile)')
ax.barh(y_pos, low_vals, color='indianred', alpha=0.7, label='Downside (10th %ile)')
ax.axvline(0, color='gray', linewidth=0.8)

ax.set_yticks(y_pos)
ax.set_yticklabels(labels)
ax.set_xlabel('Revenue Impact vs. Mean ($M)')
ax.set_title('Sensitivity: Which Variables Move Revenue Most?')
ax.legend(loc='lower right')
ax.grid(True, axis='x', alpha=0.3)

# Add spread labels
for i, spread in enumerate(spreads):
    ax.text(max(high_vals) + 20, i, f'${spread:,.0f}M spread', 
            va='center', fontsize=9, color='darkorange')

plt.tight_layout()
plt.savefig('chart2_tornado.png', dpi=150)
plt.show()
print("Chart 2 saved.")

# ============================================================
# CHART 3: Revenue by region (box plot)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

region_data = [df['us'], df['eu'], df['row']]
region_labels = ['US & Canada', 'Europe', 'Rest of World']
actuals = [BASE_US_REV, BASE_EU_REV, BASE_ROW_REV]

bp = ax.boxplot(region_data, labels=region_labels, patch_artist=True,
                boxprops=dict(facecolor='steelblue', alpha=0.6),
                medianprops=dict(color='orange', linewidth=2))

# Plot 2025 actuals as red diamonds
for i, val in enumerate(actuals):
    ax.scatter(i + 1, val, color='red', s=100, marker='D', zorder=5, label='2025 Actual' if i == 0 else '')

ax.set_ylabel('Simulated Revenue ($M)')
ax.set_title('Regional Revenue Distribution')
ax.legend()
ax.grid(True, axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('chart3_regional.png', dpi=150)
plt.show()
print("Chart 3 saved.")

# ============================================================
# CHART 4: Cumulative probability
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))

sorted_rev = np.sort(df['total'])
cumulative = np.arange(1, len(sorted_rev) + 1) / len(sorted_rev)

ax.plot(sorted_rev, cumulative, color='steelblue', linewidth=2)

# Mark key thresholds
thresholds = [
    (4000, 'red', '$4.0B'),
    (CURRENT_TOTAL, 'red', f'Current (${CURRENT_TOTAL/1000:.1f}B)'),
    (5000, 'green', '$5.0B'),
]

for val, color, label in thresholds:
    prob = (df['total'] <= val).mean()
    ax.axvline(val, color=color, linewidth=1, linestyle=':', alpha=0.5)
    ax.scatter(val, prob, color=color, s=60, zorder=5)
    ax.annotate(f'{label}\n({prob:.0%})', xy=(val, prob),
                xytext=(val + 100, prob + 0.06),
                fontsize=9, fontweight='bold', color=color)

ax.set_xlabel('Revenue ($M)')
ax.set_ylabel('Cumulative Probability')
ax.set_title('What Are the Odds? Cumulative Probability Distribution')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('chart4_cumulative.png', dpi=150)
plt.show()
print("Chart 4 saved.")

# ============================================================
# CHART 5: Scatter — engagement vs revenue
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Engagement vs Revenue
ax1 = axes[0]
ax1.scatter(df['engagement'], df['total'], alpha=0.05, s=5, color='steelblue')
z = np.polyfit(df['engagement'], df['total'], 1)
x_line = np.linspace(df['engagement'].min(), df['engagement'].max(), 100)
ax1.plot(x_line, np.poly1d(z)(x_line), color='orange', linewidth=2, linestyle='--')
corr = df['engagement'].corr(df['total'])
ax1.set_xlabel('Engagement Change')
ax1.set_ylabel('Total Revenue ($M)')
ax1.set_title(f'Engagement vs Revenue (r = {corr:.2f})')
ax1.grid(True, alpha=0.3)

# MAU Growth vs Revenue
ax2 = axes[1]
ax2.scatter(df['mau_growth'], df['total'], alpha=0.05, s=5, color='mediumseagreen')
z = np.polyfit(df['mau_growth'], df['total'], 1)
x_line = np.linspace(df['mau_growth'].min(), df['mau_growth'].max(), 100)
ax2.plot(x_line, np.poly1d(z)(x_line), color='orange', linewidth=2, linestyle='--')
corr = df['mau_growth'].corr(df['total'])
ax2.set_xlabel('MAU Growth')
ax2.set_ylabel('Total Revenue ($M)')
ax2.set_title(f'MAU Growth vs Revenue (r = {corr:.2f})')
ax2.grid(True, alpha=0.3)

plt.suptitle('Revenue Sensitivity to Key Drivers', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('chart5_scatter.png', dpi=150)
plt.show()
print("Chart 5 saved.")

print("\n✓ All charts generated. Check the .png files.")
