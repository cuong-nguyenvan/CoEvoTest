"""
plot_results.py

Visualizes results for the academic paper:
  Fig 1 -- Bar chart: CoEvo vs JCSCE vs Random fitness across datasets
  Fig 2 -- Scatter: num_rules vs CoEvo fitness (complexity analysis)
  Fig 3 -- Bar chart: Improvement of CoEvo over JCSCE (%)
  Fig 4 -- Box plot: Fitness distribution CoEvo vs JCSCE vs Random (AuthzForce)
  Fig 5 -- Line chart: Convergence comparison (Fitness vs Generations)
  Fig 6 -- Line chart: Robustness comparison across mutated policy versions (V0 - V5)
"""

import csv
import os
import zipfile
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

CURRENT_DIR = Path(__file__).parent
ROOT        = CURRENT_DIR.parent
RESULTS_CSV = ROOT / "results" / "results.csv"
SUMMARY_CSV = ROOT / "results" / "summary.csv"
ROBUST_CSV  = ROOT / "results" / "robustness.csv"
HISTORY_DIR = ROOT / "results" / "history"
HISTORY_ZIP = ROOT / "results" / "history.zip"
IMG_DIR     = ROOT / "results" / "figures"
IMG_DIR.mkdir(parents=True, exist_ok=True)

# Auto-extract history.zip if history/ folder does not exist
if not HISTORY_DIR.exists() and HISTORY_ZIP.exists():
    print("Extracting history.zip ...")
    with zipfile.ZipFile(HISTORY_ZIP, "r") as zf:
        zf.extractall(ROOT / "results")
    print(f"Done — {len(list(HISTORY_DIR.iterdir()))} files extracted.")

# ── Helpers ───────────────────────────────────────────────────────────────────

def read_csv(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

rows    = read_csv(RESULTS_CSV)
summary = read_csv(SUMMARY_CSV)
robust  = read_csv(ROBUST_CSV)

if not rows or not summary:
    print("Error: results.csv or summary.csv not found. Run experiments first.")
    exit(1)

datasets   = [s["dataset"]           for s in summary]
ga_fit     = [float(s["avg_ga_fitness"])   for s in summary]
jcsce_fit  = [float(s["avg_jcsce_fitness"]) for s in summary]
rand_fit   = [float(s["avg_rand_fitness"]) for s in summary]
improv     = [float(s["avg_improvement_jcsce"])  for s in summary]
n_policies = [int(s["n_policies"])         for s in summary]

# Mau sac nhat quan
COEVO_COLOR = "#2196F3"   # Xanh duong (CoEvoTest)
JCSCE_COLOR = "#4CAF50"   # Xanh la cay (JCSCE)
RAND_COLOR  = "#FF7043"   # Cam (Random Baseline)
GRID_ALPHA  = 0.3

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "legend.fontsize": 10,
    "figure.dpi": 150,
})

# ── Fig 1: Bar chart CoEvo vs JCSCE vs Random fitness ─────────────────────────

fig, ax = plt.subplots(figsize=(7.5, 5))
x   = np.arange(len(datasets))
w   = 0.25

b1  = ax.bar(x - w,   ga_fit,    w, label="CoEvoTest (AST)", color=COEVO_COLOR,   zorder=3)
b2  = ax.bar(x,       jcsce_fit, w, label="JCSCE (XFG-GA)", color=JCSCE_COLOR,   zorder=3)
b3  = ax.bar(x + w,   rand_fit,  w, label="Random Baseline", color=RAND_COLOR,    zorder=3)

ax.set_xlabel("Dataset")
ax.set_ylabel("Average Fitness Score")
ax.set_title("Fig. 1 - Average Fitness: CoEvoTest vs. JCSCE vs. Random Baseline")
ax.set_xticks(x)
ax.set_xticklabels([f"{d}\n(n={n})" for d, n in zip(datasets, n_policies)])
ax.set_ylim(0.50, 1.02)
ax.yaxis.grid(True, alpha=GRID_ALPHA)
ax.set_axisbelow(True)
ax.legend(loc="lower left")

for bar in b1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=8)
for bar in b2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=8)
for bar in b3:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=8)

plt.tight_layout()
plt.savefig(IMG_DIR / "fig1_fitness_comparison.pdf", bbox_inches="tight")
plt.savefig(IMG_DIR / "fig1_fitness_comparison.png", bbox_inches="tight")
plt.close()
print("Saved fig1_fitness_comparison")

# ── Fig 2: Scatter num_rules vs CoEvo fitness ─────────────────────────────────

fig, ax = plt.subplots(figsize=(7, 4.5))
COLORS = {"authzforce": "#2196F3", "dypol": "#9C27B0", "onap": "#FF7043"}

for ds in datasets:
    sub = [r for r in rows if r["dataset"] == ds]
    if sub:
        xs  = [int(r["num_rules"])    for r in sub]
        ys  = [float(r["ga_fitness"]) for r in sub]
        ax.scatter(xs, ys, alpha=0.6, s=25, color=COLORS.get(ds, "#607D8B"), label=ds, zorder=3)

ax.set_xlabel("Number of Rules in Policy")
ax.set_ylabel("CoEvoTest Fitness Score")
ax.set_title("Fig. 2 - CoEvoTest Fitness vs. Policy Complexity (Number of Rules)")
ax.xaxis.grid(True, alpha=GRID_ALPHA)
ax.yaxis.grid(True, alpha=GRID_ALPHA)
ax.set_axisbelow(True)
ax.legend()

plt.tight_layout()
plt.savefig(IMG_DIR / "fig2_complexity.pdf", bbox_inches="tight")
plt.savefig(IMG_DIR / "fig2_complexity.png", bbox_inches="tight")
plt.close()
print("Saved fig2_complexity")

# ── Fig 3: Improvement CoEvo over JCSCE (%) ────────────────────────────────────

fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(datasets, improv, color=[COLORS.get(d, "#9E9E9E") for d in datasets], zorder=3)
ax.set_xlabel("Dataset")
ax.set_ylabel("Average Improvement over JCSCE (%)")
ax.set_title("Fig. 3 - Fitness Improvement of CoEvoTest over JCSCE Baseline (%)")
ax.yaxis.grid(True, alpha=GRID_ALPHA)
ax.set_axisbelow(True)
ax.axhline(0, color="black", linewidth=0.8)

for bar, val in zip(bars, improv):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f"+{val:.2f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

plt.tight_layout()
plt.savefig(IMG_DIR / "fig3_improvement.pdf", bbox_inches="tight")
plt.savefig(IMG_DIR / "fig3_improvement.png", bbox_inches="tight")
plt.close()
print("Saved fig3_improvement")

# ── Fig 4: Box plot fitness distribution (AuthzForce) ─────────────────────────

af_rows = [r for r in rows if r["dataset"] == "authzforce"]
if af_rows:
    ga_vals    = [float(r["ga_fitness"])    for r in af_rows]
    jcsce_vals = [float(r["jcsce_fitness"]) for r in af_rows]
    rand_vals  = [float(r["rand_fitness"])  for r in af_rows]

    fig, ax = plt.subplots(figsize=(7, 4.8))
    bp = ax.boxplot(
        [ga_vals, jcsce_vals, rand_vals],
        tick_labels=["CoEvoTest (AST)", "JCSCE (XFG-GA)", "Random Baseline"],
        patch_artist=True,
        medianprops=dict(color="black", linewidth=2),
        whiskerprops=dict(linewidth=1.2),
        capprops=dict(linewidth=1.2),
        flierprops=dict(marker="o", markersize=3, alpha=0.4),
    )
    bp["boxes"][0].set_facecolor(COEVO_COLOR)
    bp["boxes"][1].set_facecolor(JCSCE_COLOR)
    bp["boxes"][2].set_facecolor(RAND_COLOR)

    ax.set_ylabel("Fitness Score")
    ax.set_title(f"Fig. 4 - Fitness Distribution on AuthzForce Dataset (n={len(af_rows)})")
    ax.yaxis.grid(True, alpha=GRID_ALPHA)
    ax.set_axisbelow(True)

    ga_patch    = mpatches.Patch(color=COEVO_COLOR,   label=f"CoEvo (mean={np.mean(ga_vals):.3f})")
    jcsce_patch = mpatches.Patch(color=JCSCE_COLOR,   label=f"JCSCE (XFG-GA) (mean={np.mean(jcsce_vals):.3f})")
    rand_patch  = mpatches.Patch(color=RAND_COLOR,    label=f"Rand  (mean={np.mean(rand_vals):.3f})")
    ax.legend(handles=[ga_patch, jcsce_patch, rand_patch], loc="lower left")

    plt.tight_layout()
    plt.savefig(IMG_DIR / "fig4_boxplot.pdf", bbox_inches="tight")
    plt.savefig(IMG_DIR / "fig4_boxplot.png", bbox_inches="tight")
    plt.close()
    print("Saved fig4_boxplot")

# ── Fig 5: Convergence Line Chart ─────────────────────────────────────────────

def plot_convergence():
    # Tim tat ca cac file lich su
    ga_files = list(HISTORY_DIR.glob("history_ga_*.csv"))
    if not ga_files:
        print("No history files found for convergence plot.")
        return

    # Doc va tinh trung binh
    gens = 15
    ga_runs = []
    jcsce_runs = []

    for f_ga in ga_files:
        pid = f_ga.name[11:] # bo qua history_ga_
        f_jcsce = HISTORY_DIR / f"history_jcsce_{pid}"
        if f_jcsce.exists():
            rows_ga = read_csv(f_ga)
            rows_jc = read_csv(f_jcsce)
            if len(rows_ga) >= gens and len(rows_jc) >= gens:
                ga_runs.append([float(r["best_test_fit"]) for r in rows_ga[:gens]])
                jcsce_runs.append([float(r["best_test_fit"]) for r in rows_jc[:gens]])

    if not ga_runs:
        print("No paired history files found.")
        return

    ga_mean = np.mean(ga_runs, axis=0)
    jcsce_mean = np.mean(jcsce_runs, axis=0)
    x = np.arange(1, gens + 1)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(x, ga_mean, marker="o", color=COEVO_COLOR, label="CoEvoTest (AST, Co-evolution)", linewidth=2)
    ax.plot(x, jcsce_mean, marker="s", color=JCSCE_COLOR, label="JCSCE (XFG-GA)", linewidth=2)
    
    ax.set_xlabel("Generations")
    ax.set_ylabel("Average Best Fitness")
    ax.set_title("Fig. 5 - Convergence Curves (Fitness vs. Generations)")
    ax.set_xticks(x)
    ax.grid(True, alpha=GRID_ALPHA)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(IMG_DIR / "fig5_convergence.pdf", bbox_inches="tight")
    plt.savefig(IMG_DIR / "fig5_convergence.png", bbox_inches="tight")
    plt.close()
    print("Saved fig5_convergence")

plot_convergence()

# ── Fig 6: Robustness Regression Chart (Mutated Versions) ──────────────────────

def plot_robustness():
    if not robust:
        print("No robustness data found. Skipping fig6.")
        return

    # Tinh trung binh theo phien ban (V0, V1, V2, V3, V4, V5)
    versions = ["V0 (Original)", "V1", "V2", "V3", "V4", "V5"]
    ga_covs = {v: [] for v in versions}
    jcsce_covs = {v: [] for v in versions}

    for r in robust:
        version_full = r["version"]
        version_short = version_full.split()[0] # Lay V0, V1, etc.
        # Map V0 (Original) -> V0 (Original)
        if "V0" in version_short:
            v_key = "V0 (Original)"
        else:
            v_key = version_short
        
        if v_key in ga_covs:
            ga_covs[v_key].append(float(r["ga_coverage"]))
            jcsce_covs[v_key].append(float(r["jcsce_coverage"]))

    x_labels = versions
    y_ga = [np.mean(ga_covs[v]) if ga_covs[v] else 1.0 for v in versions]
    y_jcsce = [np.mean(jcsce_covs[v]) if jcsce_covs[v] else 1.0 for v in versions]

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(x_labels, y_ga, marker="o", color=COEVO_COLOR, label="CoEvoTest (AST)", linewidth=2.5, markersize=8)
    ax.plot(x_labels, y_jcsce, marker="x", color=JCSCE_COLOR, label="JCSCE (XFG-GA)", linewidth=2.5, markersize=8, linestyle="--")

    ax.set_xlabel("Policy Mutation Version")
    ax.set_ylabel("Average Rule Coverage (Cov)")
    ax.set_title("Fig. 6 - Test Suite Robustness in Dynamic Regression Testing")
    ax.set_ylim(0.40, 1.05)
    ax.grid(True, alpha=GRID_ALPHA)
    ax.legend(loc="lower left")

    plt.tight_layout()
    plt.savefig(IMG_DIR / "fig6_robustness.pdf", bbox_inches="tight")
    plt.savefig(IMG_DIR / "fig6_robustness.png", bbox_inches="tight")
    plt.close()
    print("Saved fig6_robustness")

plot_robustness()

print(f"\nAll updated figures saved to: {IMG_DIR}")
