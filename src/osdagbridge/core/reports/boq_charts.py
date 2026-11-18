"""
Visualization module for OsdagBridge Material Take-off & Quantity Summary (Chapter 7).
Programmatically generates charts for:
  (a) Structural steel tonnage (Plate Girders, Cross Bracing, End Diaphragms)
  (b) Concrete volume (m3) vs reinforcement weight (MT)
"""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if s in ("", "N.A.", "None", "nan", "NaN"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def generate_boq_charts(input_dict: dict, output_dir: str) -> Dict[str, str]:
    """
    Generate material quantity charts for Chapter 7.
    
    Args:
        input_dict: Dictionary containing calculated BOQ quantities.
        output_dir: Directory where chart image files will be saved.
        
    Returns:
        Dict mapping chart keys ('boq_steel_tonnage', 'boq_concrete_rebar') to file paths.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)
    generated = {}

    # =========================================================================
    # 1. Structural Steel Tonnage Breakdown
    #    (Girders, Cross Bracing, End Diaphragms)
    # =========================================================================
    try:
        girder_wt = _safe_float(input_dict.get("steel_girders_wt_total"))
        
        # Check cross bracing components
        cb_top = _safe_float(input_dict.get("bracing_top_wt_total"))
        cb_bot = _safe_float(input_dict.get("bracing_bot_wt_total"))
        cb_diag = _safe_float(input_dict.get("bracing_diag_wt_total"))
        cb_total = _safe_float(input_dict.get("steel_bracing_wt_total"))
        
        if cb_top is not None or cb_bot is not None or cb_diag is not None:
            cb_wt = sum(v for v in (cb_top, cb_bot, cb_diag) if v is not None)
        elif cb_total is not None:
            cb_wt = cb_total
        else:
            cb_wt = None

        # Check end diaphragms
        ed_wt = _safe_float(input_dict.get("end_diaphragm_wt_total") or input_dict.get("ed_wt_total"))

        labels = ["Plate Girders\n(IS 2062)", "Cross Bracing\n(Secondary)", "End Diaphragms\n(End Support)"]
        values = [girder_wt, cb_wt, ed_wt]

        fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=300)

        x_pos = range(len(labels))
        bar_heights = [v if v is not None else 0.0 for v in values]
        max_val = max([v for v in values if v is not None] + [10.0])

        bars = []
        for i, (val, h) in enumerate(zip(values, bar_heights)):
            if val is not None and val > 0:
                bar = ax.bar(i, h, width=0.48, color="#1b5e20" if i == 0 else "#2e7d32",
                             edgecolor="#1a252f", linewidth=0.8, zorder=3)
                bars.append(bar)
                ax.text(i, h + max_val * 0.025, f"{val:.2f} MT",
                        ha="center", va="bottom", fontsize=10.5, fontweight="bold", color="#1a252f")
            else:
                # Safe visual representation for N.A. entries
                bar = ax.bar(i, max_val * 0.05, width=0.48, color="#eceff1",
                             edgecolor="#78909c", linewidth=0.8, linestyle="--", hatch="//", zorder=3)
                bars.append(bar)
                ax.text(i, max_val * 0.07, "N.A.*",
                        ha="center", va="bottom", fontsize=10.5, fontweight="bold", color="#546e7a")

        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, fontsize=10.0, fontweight="bold", color="#263238")
        ax.set_ylabel("Weight (MT)", fontsize=10.5, fontweight="bold", color="#263238")
        ax.set_title("Structural Steel Tonnage Breakdown by Component", fontsize=11.5, fontweight="bold", pad=12, color="#1a252f")

        ax.set_ylim(0, max_val * 1.25)
        ax.grid(axis="y", linestyle=":", alpha=0.6, color="#90a4ae", zorder=0)
        ax.set_axisbelow(True)

        # Footnote for N.A. elements
        has_na = any(v is None for v in values)
        if has_na:
            ax.text(0.5, -0.18, "*Note: Cross bracing / end diaphragm tonnages are N.A. (pending transverse design run).",
                    ha="center", va="top", transform=ax.transAxes, fontsize=8.5, fontstyle="italic", color="#546e7a")

        plt.tight_layout()
        steel_chart_path = os.path.join(output_dir, "boq_steel_tonnage_chart.png").replace("\\", "/")
        plt.savefig(steel_chart_path, bbox_inches="tight", dpi=300)
        plt.close(fig)
        generated["boq_steel_tonnage"] = steel_chart_path
        logger.info("Generated BOQ structural steel tonnage chart: %s", steel_chart_path)
    except Exception as exc:
        logger.warning("Failed to generate BOQ steel tonnage chart: %s", exc)

    # =========================================================================
    # 2. Concrete Volume (m3) vs. Reinforcement Weight (MT)
    # =========================================================================
    try:
        concrete_vol = _safe_float(input_dict.get("concrete_deck_vol_total"))
        rebar_wt = _safe_float(input_dict.get("rebar_deck_wt_total"))

        if concrete_vol is not None or rebar_wt is not None:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.8, 4.2), dpi=300)

            # Subplot 1: Concrete Volume
            c_val = concrete_vol if concrete_vol is not None else 0.0
            b1 = ax1.bar([0], [c_val], width=0.42, color="#455a64", edgecolor="#263238", linewidth=0.8, zorder=3)
            ax1.set_xticks([0])
            ax1.set_xticklabels(["Concrete Deck Slab\n(M40 Grade)"], fontsize=10.0, fontweight="bold", color="#263238")
            ax1.set_ylabel(r"Volume ($\text{m}^3$)", fontsize=10.5, fontweight="bold", color="#263238")
            ax1.set_title("Deck Concrete Volume", fontsize=11.0, fontweight="bold", pad=10, color="#1a252f")
            ax1.set_ylim(0, max(c_val * 1.25, 10.0))
            ax1.grid(axis="y", linestyle=":", alpha=0.6, color="#90a4ae", zorder=0)
            ax1.set_axisbelow(True)
            if concrete_vol is not None:
                ax1.text(0, c_val + max(c_val * 0.03, 0.5), f"{c_val:.2f} m³",
                         ha="center", va="bottom", fontsize=10.5, fontweight="bold", color="#1a252f")
            else:
                ax1.text(0, 1.0, "N.A.", ha="center", va="bottom", fontsize=10.5, fontweight="bold", color="#546e7a")

            # Subplot 2: Reinforcement Steel Weight
            r_val = rebar_wt if rebar_wt is not None else 0.0
            b2 = ax2.bar([0], [r_val], width=0.42, color="#0277bd", edgecolor="#01579b", linewidth=0.8, zorder=3)
            ax2.set_xticks([0])
            ax2.set_xticklabels(["Deck Reinforcement\n(Fe 500 Grade)"], fontsize=10.0, fontweight="bold", color="#263238")
            ax2.set_ylabel("Weight (MT)", fontsize=10.5, fontweight="bold", color="#263238")
            ax2.set_title("Deck Reinforcement Weight", fontsize=11.0, fontweight="bold", pad=10, color="#1a252f")
            ax2.set_ylim(0, max(r_val * 1.25, 2.0))
            ax2.grid(axis="y", linestyle=":", alpha=0.6, color="#90a4ae", zorder=0)
            ax2.set_axisbelow(True)
            if rebar_wt is not None:
                ax2.text(0, r_val + max(r_val * 0.03, 0.1), f"{r_val:.2f} MT",
                         ha="center", va="bottom", fontsize=10.5, fontweight="bold", color="#1a252f")
            else:
                ax2.text(0, 0.5, "N.A.", ha="center", va="bottom", fontsize=10.5, fontweight="bold", color="#546e7a")

            # Ratio note across both subplots
            if concrete_vol and rebar_wt and concrete_vol > 0:
                rebar_ratio = (rebar_wt * 1000.0) / concrete_vol
                fig.text(0.5, -0.04, f"Reinforcement Ratio: {rebar_ratio:.1f} kg/m³ of concrete (nominal slab rebar allowance)",
                         ha="center", va="top", fontsize=8.5, fontstyle="italic", color="#455a64")

            plt.tight_layout()
            rebar_chart_path = os.path.join(output_dir, "boq_concrete_rebar_chart.png").replace("\\", "/")
            plt.savefig(rebar_chart_path, bbox_inches="tight", dpi=300)
            plt.close(fig)
            generated["boq_concrete_rebar"] = rebar_chart_path
            logger.info("Generated BOQ concrete vs rebar chart: %s", rebar_chart_path)
    except Exception as exc:
        logger.warning("Failed to generate BOQ concrete vs rebar chart: %s", exc)

    return generated
