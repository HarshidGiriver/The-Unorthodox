"""Generate publication-grade evaluation visualizations for Kintsugi AI.

Scores the official 2,240-row marketing_campaign.csv dataset using
StressDetectionAgent and outputs three 300-DPI dark/fintech-themed charts:
1. assets/distress_distribution.png
2. assets/deal_vs_spend_scatter.png
3. assets/risk_drivers_comparison.png
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple

# Ensure repository root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from backend.config import BASE_DIR, FEATURE_COLUMNS, TIER_1_LOW_RISK_MAX, TIER_2_MODERATE_STRESS_MAX
from backend.data.loader import load_customer_data
from backend.agents.detection_agent import StressDetectionAgent

# Output directory for assets
ASSETS_DIR = BASE_DIR / "assets"

# Cohesive Dark Fintech Theme Palette
PALETTE = {
    "bg_dark": "#0B1120",        # Deep dark blue-black background
    "card_bg": "#111827",        # Slate dark card background
    "grid": "#1F2937",           # Subtle border / grid
    "text_primary": "#F9FAFB",   # Bright white text
    "text_secondary": "#9CA3AF", # Muted gray text
    "tier1": "#10B981",          # Emerald green (Low Risk / Healthy)
    "tier2": "#F59E0B",          # Amber / Orange (Moderate Stress)
    "tier3": "#EF4444",          # Crimson / Red (Severe Anomaly)
    "accent_blue": "#38BDF8",    # Sky blue
    "accent_purple": "#818CF8",  # Indigo / Purple accent
}


def setup_fintech_style():
    """Configure matplotlib global parameters for publication-grade dark fintech theme."""
    plt.rcParams.update({
        "figure.facecolor": PALETTE["bg_dark"],
        "axes.facecolor": PALETTE["card_bg"],
        "axes.edgecolor": PALETTE["grid"],
        "axes.linewidth": 1.2,
        "axes.labelcolor": PALETTE["text_primary"],
        "axes.titlecolor": PALETTE["text_primary"],
        "xtick.color": PALETTE["text_secondary"],
        "ytick.color": PALETTE["text_secondary"],
        "text.color": PALETTE["text_primary"],
        "grid.color": PALETTE["grid"],
        "grid.linestyle": "--",
        "grid.alpha": 0.45,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
    })


def generate_distress_distribution_chart(df_scored: pd.DataFrame, output_path: Path):
    """Generate Chart A: Histogram & KDE curve of continuous stress scores.

    Color-coded by Tier 1 (Low: 1,275), Tier 2 (Moderate: 629), and Tier 3 (Severe Anomaly: 336),
    with a vertical threshold line at the 15% contamination cutoff (score = 0.65).
    """
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)

    # Exact risk tier cohort masks matching portfolio categorization
    t1_mask = df_scored["risk_tier"] == "Tier 1 (Normal / Low Risk)"
    t2_mask = df_scored["risk_tier"] == "Tier 2 (Moderate Stress)"
    t3_mask = df_scored["risk_tier"] == "Tier 3 (High Anomaly / Severe Distress)"

    n_t1 = int(t1_mask.sum())
    n_t2 = int(t2_mask.sum())
    n_t3 = int(t3_mask.sum())
    total = len(df_scored)

    # Binning across continuous range [0.0, 1.0]
    bins = np.linspace(0.0, 1.0, 41)

    # Stacked histogram
    ax.hist(
        [df_scored.loc[t1_mask, "anomaly_score"],
         df_scored.loc[t2_mask, "anomaly_score"],
         df_scored.loc[t3_mask, "anomaly_score"]],
        bins=bins,
        stacked=True,
        color=[PALETTE["tier1"], PALETTE["tier2"], PALETTE["tier3"]],
        label=[
            f"Tier 1: Low Risk (n={n_t1:,} | {n_t1/total*100:.1f}%)",
            f"Tier 2: Moderate Stress (n={n_t2:,} | {n_t2/total*100:.1f}%)",
            f"Tier 3: Severe Anomaly (n={n_t3:,} | {n_t3/total*100:.1f}%)"
        ],
        edgecolor=PALETTE["bg_dark"],
        linewidth=0.8,
        alpha=0.92
    )

    # Overlay overall KDE curve scaled to count density
    kde_ax = ax.twinx()
    sns.kdeplot(
        df_scored["anomaly_score"],
        ax=kde_ax,
        color=PALETTE["accent_blue"],
        linewidth=2.8,
        label="Kernel Density Estimate (KDE)"
    )
    kde_ax.set_yticks([])
    kde_ax.set_ylabel("")
    kde_ax.grid(False)

    # 15% Contamination Cutoff (Threshold = 0.65)
    cutoff = TIER_2_MODERATE_STRESS_MAX
    ax.axvline(
        cutoff,
        color="#F87171",
        linestyle="--",
        linewidth=2.2,
        label=f"15% Contamination Cutoff (s ≥ {cutoff:.2f})"
    )

    # Tier region shaded zones on the background
    ax.axvspan(0.0, TIER_1_LOW_RISK_MAX, color=PALETTE["tier1"], alpha=0.06)
    ax.axvspan(TIER_1_LOW_RISK_MAX, TIER_2_MODERATE_STRESS_MAX, color=PALETTE["tier2"], alpha=0.06)
    ax.axvspan(TIER_2_MODERATE_STRESS_MAX, 1.0, color=PALETTE["tier3"], alpha=0.08)

    # Annotations & Callouts - placed cleanly to avoid legend overlap
    ax.annotate(
        f"Tier 3 Anomaly Frontier\nCutoff: s ≥ {cutoff:.2f} (Top 15%)\nAccounts: n = {n_t3:,}\nIntervention Trigger",
        xy=(cutoff, 65),
        xytext=(cutoff + 0.06, 95),
        arrowprops=dict(
            arrowstyle="->",
            color="#F87171",
            lw=1.6,
            connectionstyle="arc3,rad=-0.15"
        ),
        fontsize=9.5,
        fontweight="bold",
        color=PALETTE["text_primary"],
        bbox=dict(boxstyle="round,pad=0.5", facecolor=PALETTE["card_bg"], edgecolor=PALETTE["tier3"], alpha=0.95)
    )

    # Title and subtitle without overlap
    ax.set_title(
        "Kintsugi AI: Continuous Borrower Distress Score Distribution\n"
        f"Unsupervised Isolation Forest Calibration (N = {total:,} Borrowers | Contamination = 15.0%)",
        fontsize=14,
        fontweight="bold",
        pad=16,
        loc="left",
        color=PALETTE["text_primary"]
    )

    ax.set_xlabel("Calibrated Stress Anomaly Score [0.0 = Benign, 1.0 = Max Distress]", fontsize=11, labelpad=10)
    ax.set_ylabel("Borrower Account Count", fontsize=11, labelpad=10)
    ax.set_xlim(-0.02, 1.02)
    ax.grid(True, linestyle="--", alpha=0.35)

    # Combined Legend
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = kde_ax.get_legend_handles_labels()
    legend = ax.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper right",
        frameon=True,
        facecolor=PALETTE["card_bg"],
        edgecolor=PALETTE["grid"],
        fontsize=9.5
    )
    for text in legend.get_texts():
        text.set_color(PALETTE["text_primary"])

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f" Saved Chart A -> {output_path}")


def generate_deal_vs_spend_scatter_chart(df_scored: pd.DataFrame, output_path: Path):
    """Generate Chart B: Scatter plot mapping deal_reliance_index vs. discretionary_ratio.

    Highlights 336 anomalous accounts in alert amber/red vs. 1,904 normal in blue/green.
    """
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)

    normal_mask = ~df_scored["is_anomaly"]
    anomaly_mask = df_scored["is_anomaly"]

    # 1. Normal Accounts (Tier 1 & 2)
    ax.scatter(
        df_scored.loc[normal_mask, "deal_reliance_index"],
        df_scored.loc[normal_mask, "discretionary_ratio"],
        c=PALETTE["tier1"],
        alpha=0.50,
        s=38,
        edgecolors="none",
        label=f"Normal / Mild Stress Borrowers (n={int(normal_mask.sum()):,})"
    )

    # 2. Anomalous Accounts (Tier 3)
    ax.scatter(
        df_scored.loc[anomaly_mask, "deal_reliance_index"],
        df_scored.loc[anomaly_mask, "discretionary_ratio"],
        c=PALETTE["tier3"],
        alpha=0.90,
        s=68,
        edgecolors="#FCA5A5",
        linewidth=0.8,
        label=f"Severe Stress Anomalies [Tier 3] (n={int(anomaly_mask.sum()):,})"
    )

    deal_mean_anomaly = float(df_scored.loc[anomaly_mask, "deal_reliance_index"].mean())
    deal_mean_normal = float(df_scored.loc[normal_mask, "deal_reliance_index"].mean())
    disc_mean_anomaly = float(df_scored.loc[anomaly_mask, "discretionary_ratio"].mean())

    # Vertical threshold line marking elevated deal reliance
    ax.axvline(0.40, color=PALETTE["tier2"], linestyle=":", linewidth=1.6, alpha=0.85, label="Elevated Deal Reliance Boundary (0.40)")

    # Highlight anomalous cluster
    ax.annotate(
        f"Critical Anomaly Cluster\nMean Deal Reliance: {deal_mean_anomaly:.2f} (Normal: {deal_mean_normal:.2f})\nDescriptive cohort comparison\nGenerated financial proxies",
        xy=(deal_mean_anomaly, disc_mean_anomaly),
        xytext=(0.58, 0.22),
        arrowprops=dict(
            arrowstyle="->",
            color=PALETTE["tier3"],
            lw=1.6,
            connectionstyle="arc3,rad=-0.2"
        ),
        fontsize=9.5,
        fontweight="bold",
        color=PALETTE["text_primary"],
        bbox=dict(boxstyle="round,pad=0.5", facecolor=PALETTE["card_bg"], edgecolor=PALETTE["tier3"], alpha=0.95)
    )

    ax.set_title(
        "Behavioral Distress Separation: Deal Reliance vs. Discretionary Spending\n"
        "Demo anomaly separation; not validated prediction of future default",
        fontsize=13,
        fontweight="bold",
        pad=16,
        loc="left",
        color=PALETTE["text_primary"]
    )

    ax.set_xlabel("Emergency Deal Reliance Index [NumDealsPurchases / Total Purchases]", fontsize=11, labelpad=10)
    ax.set_ylabel("Discretionary Ratio [Wines, Sweets & Gold / Total Expenditure]", fontsize=11, labelpad=10)
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.05)
    ax.grid(True, linestyle="--", alpha=0.35)

    legend = ax.legend(
        loc="upper right",
        frameon=True,
        facecolor=PALETTE["card_bg"],
        edgecolor=PALETTE["grid"],
        fontsize=9.5
    )
    for text in legend.get_texts():
        text.set_color(PALETTE["text_primary"])

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f" Saved Chart B -> {output_path}")


def generate_risk_drivers_comparison_chart(df_scored: pd.DataFrame, output_path: Path):
    """Generate Chart C: Grouped comparison of normal vs. distressed borrowers across key indicators.

    Compares: Deal Reliance, Discretionary Ratio, Spend-to-Income, and Liquidity Runway.
    Uses multi-metric grouped visualization with direct percentage labels.
    """
    fig, axes = plt.subplots(1, 4, figsize=(16, 5.5), dpi=300)

    # Cohorts
    normal = df_scored[~df_scored["is_anomaly"]]
    distressed = df_scored[df_scored["is_anomaly"]]

    metrics = [
        {
            "name": "Deal Reliance Index",
            "col": "deal_reliance_index",
            "unit": "ratio",
            "formatter": "{:.3f}",
            "desc": "Heavy coupon & deal hunting",
            "higher_is_worse": True,
        },
        {
            "name": "Discretionary Ratio",
            "col": "discretionary_ratio",
            "unit": "ratio",
            "formatter": "{:.3f}",
            "desc": "Wines, sweets & luxury share",
            "higher_is_worse": False,
        },
        {
            "name": "Spend-to-Income",
            "col": "spend_to_income_ratio",
            "unit": "ratio",
            "formatter": "{:.4f}",
            "desc": "Monthly expenses / income",
            "higher_is_worse": True,
        },
        {
            "name": "Liquidity Runway",
            "col": "liquidity_runway_months",
            "unit": "months",
            "formatter": "{:.2f} mo",
            "desc": "Emergency savings reserve",
            "higher_is_worse": False,
        },
    ]

    for idx, (ax, m) in enumerate(zip(axes, metrics)):
        col = m["col"]
        mean_norm = float(normal[col].mean())
        mean_dist = float(distressed[col].mean())

        # Bar chart for this indicator
        bars = ax.bar(
            [f"Typical\n(n={len(normal):,})", f"Anomalous\n(n={len(distressed):,})"],
            [mean_norm, mean_dist],
            color=[PALETTE["tier1"], PALETTE["tier3"]],
            width=0.55,
            edgecolor=PALETTE["bg_dark"],
            linewidth=1.2
        )

        # Label values on top of bars
        for bar, val in zip(bars, [mean_norm, mean_dist]):
            height = bar.get_height()
            ax.annotate(
                m["formatter"].format(val),
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10.5,
                fontweight="bold",
                color=PALETTE["text_primary"]
            )

        # Calculate percentage delta
        pct_diff = ((mean_dist - mean_norm) / (mean_norm + 1e-6)) * 100
        delta_str = f"+{pct_diff:.1f}%" if pct_diff > 0 else f"{pct_diff:.1f}%"
        delta_color = PALETTE["tier3"] if (pct_diff > 0 if m["higher_is_worse"] else pct_diff < 0) else PALETTE["tier1"]

        ax.set_title(m["name"], fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel(m["unit"].capitalize() if idx == 0 else "", fontsize=10, labelpad=8)
        ax.grid(True, axis="y", linestyle="--", alpha=0.35)

        # Delta badge below title
        ax.text(
            0.5, 0.90,
            f"Δ {delta_str}",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=delta_color,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=PALETTE["bg_dark"], edgecolor=delta_color, alpha=0.9)
        )

        # Subtext description
        ax.text(
            0.5, -0.22,
            m["desc"],
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=8.5,
            color=PALETTE["text_secondary"],
            style="italic"
        )

        # Expand y-limit slightly for value annotations
        max_val = max(mean_norm, mean_dist)
        ax.set_ylim(0, max_val * 1.25)

    plt.suptitle(
        "Key Financial Risk Driver Comparison: Normal vs. Anomaly Segments",
        fontsize=15,
        fontweight="bold",
        color=PALETTE["text_primary"],
        y=1.02
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f" Saved Chart C -> {output_path}")


def run_pipeline() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Execute complete ingestion, scoring, and visualization pipeline with telemetry."""
    print("=" * 70)
    print("Kintsugi AI: Exploratory Visualization & Anomaly Evaluation Pipeline")
    print("=" * 70)

    # 1. Ingestion
    start_time = time.perf_counter()
    print("\n[1/4] Ingesting customer data via backend.data.loader.load_customer_data()...")
    df = load_customer_data()
    n_rows = len(df)
    n_cols = df.shape[1]
    print(f"      Ingested {n_rows:,} customer records with {n_cols} baseline attributes.")

    # 2. Anomaly Scoring
    print("\n[2/4] Initializing StressDetectionAgent and analyzing portfolio...")
    agent = StressDetectionAgent()
    scoring_start = time.perf_counter()
    df_scored = agent.analyze_portfolio(df)
    latency_sec = time.perf_counter() - scoring_start
    latency_ms = latency_sec * 1000.0

    print(f"      Analyzed {n_rows:,} accounts in {latency_ms:.2f} ms ({latency_ms/n_rows:.3f} ms/account).")

    # 3. Create assets directory
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[3/4] Verified output directory: {ASSETS_DIR}")

    # 4. Generate Visualizations
    setup_fintech_style()
    print("\n[4/4] Rendering 300-DPI publication-grade fintech charts...")

    distress_path = ASSETS_DIR / "distress_distribution.png"
    generate_distress_distribution_chart(df_scored, distress_path)

    scatter_path = ASSETS_DIR / "deal_vs_spend_scatter.png"
    generate_deal_vs_spend_scatter_chart(df_scored, scatter_path)

    drivers_path = ASSETS_DIR / "risk_drivers_comparison.png"
    generate_risk_drivers_comparison_chart(df_scored, drivers_path)

    # Compute Metrics Summary
    n_t1 = int((df_scored["risk_tier"] == "Tier 1 (Normal / Low Risk)").sum())
    n_t2 = int((df_scored["risk_tier"] == "Tier 2 (Moderate Stress)").sum())
    n_t3 = int((df_scored["risk_tier"] == "Tier 3 (High Anomaly / Severe Distress)").sum())
    anom_count = int(df_scored["is_anomaly"].sum())
    contamination = anom_count / n_rows

    total_latency_ms = (time.perf_counter() - start_time) * 1000.0

    metrics = {
        "dataset_rows": n_rows,
        "feature_dimensions": len(FEATURE_COLUMNS),
        "total_columns": df_scored.shape[1],
        "contamination_rate": contamination,
        "anomalies_detected": anom_count,
        "tier1_low_risk": n_t1,
        "tier2_moderate_stress": n_t2,
        "tier3_severe_anomaly": n_t3,
        "scoring_latency_ms": latency_ms,
        "total_latency_ms": total_latency_ms,
    }

    print("\n" + "=" * 70)
    print("Execution & Model Evaluation Summary:")
    print(f"• Dataset Row Count:       {n_rows:,}")
    print(f"• Core Model Features:      {len(FEATURE_COLUMNS)} {FEATURE_COLUMNS}")
    print(f"• Contamination Cutoff:    {contamination*100:.1f}% ({anom_count:,} accounts)")
    print(f"• Tier 1 (Low Risk):       {n_t1:,} accounts ({n_t1/n_rows*100:.1f}%)")
    print(f"• Tier 2 (Moderate):       {n_t2:,} accounts ({n_t2/n_rows*100:.1f}%)")
    print(f"• Tier 3 (Severe Anomaly): {n_t3:,} accounts ({n_t3/n_rows*100:.1f}%)")
    print(f"• Model Scoring Latency:   {latency_ms:.2f} ms")
    print(f"• Total Pipeline Runtime:  {total_latency_ms:.2f} ms")
    print("=" * 70)

    return df_scored, metrics


if __name__ == "__main__":
    run_pipeline()
