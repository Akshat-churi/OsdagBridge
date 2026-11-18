"""
Visualization module for OsdagBridge Report Generator.
Programmatically generates publication-quality Utilization Ratio (Demand / Capacity)
summary bar charts for Steel Plate Girders and Concrete Deck Slab.
"""

import os
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


def extract_ur_data(output_dict: dict) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """
    Extract utilization ratios (demand / capacity) for Steel Plate Girders
    and Concrete Deck Slab from output_dict.
    
    Returns:
        (girder_checks, deck_checks): lists of (check_label, ur_value)
    """
    from osdagbridge.core.utils.common import (
        KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT,
        KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP,
        KEY_DD_M_ULS_OH, KEY_DD_MU_OH,
        KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA,
        KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC,
        KEY_DD_WK_LIMIT, KEY_DD_WK_BOT, KEY_DD_WK_TOP, KEY_DD_WK_OH,
        KEY_UTIL_FLEXURE, KEY_UTIL_SHEAR,
    )

    girder_checks = []
    deck_checks = []

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Steel Plate Girders
    # ─────────────────────────────────────────────────────────────────────────
    pg_results = (output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}

    # Helper to find maximum DCR across all non-edge-beam girders for given check IDs
    def _max_dcr(check_ids):
        best = None
        for g, gd in pg_results.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in check_ids or chk.get("id") in check_ids:
                    val = chk.get("dcr")
                    try:
                        d = float(val) if val is not None else None
                    except (TypeError, ValueError):
                        d = None
                    if d is not None and (best is None or d > best):
                        best = d
            for _lc, _ld in (gd.get("per_lc") or {}).items():
                if str(_lc).lower().startswith("envelope"):
                    continue
                for chk in (_ld.get("checks") or []):
                    if chk.get("id") in check_ids or chk.get("check_id") in check_ids:
                        val = chk.get("dcr")
                        try:
                            d = float(val) if val is not None else None
                        except (TypeError, ValueError):
                            d = None
                        if d is not None and (best is None or d > best):
                            best = d
        return best

    # Extract primary checks
    moment_ur = _max_dcr({1, "flexure", "flexure_capacity", "moment_capacity"})
    if moment_ur is None and output_dict.get(KEY_UTIL_FLEXURE):
        try:
            moment_ur = float(output_dict[KEY_UTIL_FLEXURE]) / 100.0
        except (TypeError, ValueError):
            pass

    shear_ur = _max_dcr({2, "shear", "shear_capacity"})
    if shear_ur is None and output_dict.get(KEY_UTIL_SHEAR):
        try:
            shear_ur = float(output_dict[KEY_UTIL_SHEAR]) / 100.0
        except (TypeError, ValueError):
            pass

    ltb_ur = _max_dcr({5, "ltb", "ltb_capacity", "lateral_torsional_buckling"})
    deflection_ur = _max_dcr({13, 14, "deflection", "live_load_deflection", "total_deflection"})
    stress_ur = _max_dcr({11, "stress", "stress_limitation", "maximum_stress"})
    fatigue_ur = _max_dcr({8, 9, "fatigue", "fatigue_assessment", "normal_fatigue", "shear_fatigue"})
    stiffener_ur = _max_dcr({3, 4, 6, "stiffener", "web_buckling", "intermediate_stiffener", "bearing_stiffener"})

    if moment_ur is not None:
        girder_checks.append(("Moment Capacity ($M_u / M_d$)", moment_ur))
    if shear_ur is not None:
        girder_checks.append(("Shear Capacity ($V_u / V_d$)", shear_ur))
    if ltb_ur is not None:
        girder_checks.append(("Lateral-Torsional Buckling", ltb_ur))
    if deflection_ur is not None:
        girder_checks.append(("Deflection Control ($\delta / \delta_{lim}$)", deflection_ur))
    if stress_ur is not None:
        girder_checks.append(("Service Stress Limit ($\sigma / f_{lim}$)", stress_ur))
    if fatigue_ur is not None:
        girder_checks.append(("Fatigue Assessment ($\Delta\sigma / f_{fd}$)", fatigue_ur))
    if stiffener_ur is not None:
        girder_checks.append(("Stiffener / Web Buckling", stiffener_ur))

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Concrete Deck Slab
    # ─────────────────────────────────────────────────────────────────────────
    deck_res = output_dict.get("deck_design_results", {}) or {}
    
    def _dkv(k):
        v = output_dict.get(k)
        if v is None:
            v = deck_res.get(k)
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    # Transverse Flexure - Sagging (Bottom)
    m_sag = _dkv(KEY_DD_M_ULS_SAG)
    mu_bot = _dkv(KEY_DD_MU_BOT)
    if m_sag is not None and mu_bot and mu_bot > 0:
        deck_checks.append(("Transverse Flexure (Bottom / Sagging)", m_sag / mu_bot))
    elif deck_res.get("ur_bot_uls") is not None:
        deck_checks.append(("Transverse Flexure (Bottom / Sagging)", float(deck_res["ur_bot_uls"])))

    # Transverse Flexure - Hogging (Top)
    m_hog = _dkv(KEY_DD_M_ULS_HOG)
    mu_top = _dkv(KEY_DD_MU_TOP)
    if m_hog is not None and mu_top and mu_top > 0:
        deck_checks.append(("Transverse Flexure (Top / Hogging)", m_hog / mu_top))
    elif deck_res.get("ur_top_uls") is not None:
        deck_checks.append(("Transverse Flexure (Top / Hogging)", float(deck_res["ur_top_uls"])))

    # Cantilever Overhang (if present)
    m_oh = _dkv(KEY_DD_M_ULS_OH)
    mu_oh = _dkv(KEY_DD_MU_OH)
    if m_oh is not None and mu_oh and mu_oh > 0:
        deck_checks.append(("Cantilever Overhang Flexure", m_oh / mu_oh))

    # Punching Shear
    v_punch = _dkv(KEY_DD_PUNCH_VED)
    vrd_c = _dkv(KEY_DD_VRD_C_MPA)
    if v_punch is not None and vrd_c and vrd_c > 0:
        deck_checks.append(("Punching Shear ($V_{Ed} / V_{Rd,c}$)", v_punch / vrd_c))

    # One-Way Beam Shear
    v_shear = _dkv(KEY_DD_SHEAR_VED)
    vrd_max = _dkv(KEY_DD_SHEAR_VRDC)
    if v_shear is not None and vrd_max and vrd_max > 0:
        deck_checks.append(("One-Way Beam Shear ($V_{Ed} / V_{Rd}$)", v_shear / vrd_max))

    # Crack Width Check
    wk_lim = _dkv(KEY_DD_WK_LIMIT)
    wks = [_dkv(k) for k in [KEY_DD_WK_BOT, KEY_DD_WK_TOP, KEY_DD_WK_OH]]
    valid_wks = [w for w in wks if w is not None]
    if valid_wks and wk_lim and wk_lim > 0:
        deck_checks.append(("Crack Width ($w_k / w_{k,lim}$)", max(valid_wks) / wk_lim))
    elif deck_res.get("ur_bot_crack") is not None:
        deck_checks.append(("Crack Width ($w_k / w_{k,lim}$)", float(deck_res["ur_bot_crack"])))

    # Composite / Transverse Shear
    if deck_res.get("ur_composite_trans_shear") is not None:
        deck_checks.append(("Transverse Interface Shear", float(deck_res["ur_composite_trans_shear"])))

    return girder_checks, deck_checks


def generate_ur_charts(output_dict: dict, output_dir: str) -> Dict[str, str]:
    """
    Generate publication-quality Utilization Ratio bar charts.
    
    Args:
        output_dict: The bridge design result dictionary.
        output_dir: Directory where PNG files will be written.
        
    Returns:
        dict: Mapping of figure names to absolute file paths:
              {'ur_summary': path, 'ur_girders': path, 'ur_deck': path}
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    girder_checks, deck_checks = extract_ur_data(output_dict)
    generated = {}

    if not girder_checks and not deck_checks:
        logger.info("No utilization ratio data found; skipping UR chart generation.")
        return generated

    os.makedirs(output_dir, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Combined Summary Chart (Side-by-Side 2 panels)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.0), dpi=300)

        chart_configs = [
            (ax1, girder_checks, "Steel Plate Girders (IRC 22 / IS 800)"),
            (ax2, deck_checks, "Concrete Deck Slab (IRC 112 / IRC 22)"),
        ]

        for ax, checks, title in chart_configs:
            if not checks:
                ax.text(0.5, 0.5, "No checks available", ha="center", va="center", transform=ax.transAxes)
                ax.set_title(title, fontsize=11, fontweight="bold", color="#2c3e50")
                continue

            labels = [c[0] for c in checks]
            values = [c[1] for c in checks]
            y_pos = np.arange(len(labels))

            # Color gradient: Green <= 0.85, Amber <= 1.0, Crimson > 1.0
            colors = [
                "#2e7d32" if v <= 0.85 else "#e65100" if v <= 1.0 else "#c62828"
                for v in values
            ]

            bars = ax.barh(y_pos, values, color=colors, height=0.55, edgecolor="#37474f", linewidth=0.6)

            # Capacity Threshold Line (UR = 1.0)
            ax.axvline(1.0, color="#b71c1c", linestyle="--", linewidth=1.5, alpha=0.9, label="Limit (1.00)")

            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=8.5, color="#1a252f")
            ax.invert_yaxis()  # Top-down order
            ax.set_xlabel("Utilization Ratio = Demand / Capacity", fontsize=9, fontweight="bold", color="#2c3e50")
            ax.set_title(title, fontsize=10.5, fontweight="bold", pad=12, color="#1b5e20" if "Steel" in title else "#0d47a1")
            
            x_max = max(max(values) * 1.25, 1.30)
            ax.set_xlim(0, x_max)
            ax.grid(axis="x", linestyle=":", alpha=0.6, color="#90a4ae")
            ax.set_axisbelow(True)

            # Value labels on bars
            for bar, val in zip(bars, values):
                w = bar.get_width()
                tag = f" {val:.2f} (FAIL)" if val > 1.0 else f" {val:.2f} (PASS)"
                text_color = "#b71c1c" if val > 1.0 else "#1b5e20"
                ax.text(
                    w + 0.02,
                    bar.get_y() + bar.get_height() / 2,
                    tag,
                    va="center",
                    ha="left",
                    fontsize=8.0,
                    fontweight="bold",
                    color=text_color,
                )

            # Clean borders
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
            ax.spines["left"].set_color("#78909c")
            ax.spines["bottom"].set_color("#78909c")

        plt.suptitle("Overall Primary Element Utilization Ratio Summary", fontsize=12.5, fontweight="bold", y=1.02, color="#212121")
        plt.tight_layout()

        combined_path = os.path.join(output_dir, "ur_summary_chart.png").replace("\\", "/")
        plt.savefig(combined_path, bbox_inches="tight", dpi=300)
        plt.close(fig)
        generated["ur_summary"] = combined_path
        logger.info("Generated combined UR summary chart: %s", combined_path)

    except Exception as exc:
        logger.warning("Failed to generate combined UR chart: %s", exc, exc_info=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Individual Girder UR Chart
    # ─────────────────────────────────────────────────────────────────────────
    if girder_checks:
        try:
            fig, ax = plt.subplots(figsize=(8.0, 4.2), dpi=300)
            labels = [c[0] for c in girder_checks]
            values = [c[1] for c in girder_checks]
            y_pos = np.arange(len(labels))
            colors = ["#2e7d32" if v <= 0.85 else "#e65100" if v <= 1.0 else "#c62828" for v in values]

            bars = ax.barh(y_pos, values, color=colors, height=0.52, edgecolor="#37474f", linewidth=0.6)
            ax.axvline(1.0, color="#b71c1c", linestyle="--", linewidth=1.5, alpha=0.9, label="Limit (1.00)")
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=9.0, color="#1a252f")
            ax.invert_yaxis()
            ax.set_xlabel("Utilization Ratio = Demand / Capacity", fontsize=9.5, fontweight="bold", color="#2c3e50")
            ax.set_title("Steel Plate Girders — Utilization Ratio Summary (IRC 22 / IS 800)", fontsize=11, fontweight="bold", pad=12, color="#1b5e20")
            ax.set_xlim(0, max(max(values) * 1.25, 1.30))
            ax.grid(axis="x", linestyle=":", alpha=0.6, color="#90a4ae")
            ax.set_axisbelow(True)

            for bar, val in zip(bars, values):
                w = bar.get_width()
                tag = f" {val:.2f} (FAIL)" if val > 1.0 else f" {val:.2f} (PASS)"
                text_color = "#b71c1c" if val > 1.0 else "#1b5e20"
                ax.text(w + 0.02, bar.get_y() + bar.get_height() / 2, tag, va="center", ha="left", fontsize=8.5, fontweight="bold", color=text_color)

            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
            ax.spines["left"].set_color("#78909c")
            ax.spines["bottom"].set_color("#78909c")

            plt.tight_layout()
            girder_path = os.path.join(output_dir, "ur_girders_chart.png").replace("\\", "/")
            plt.savefig(girder_path, bbox_inches="tight", dpi=300)
            plt.close(fig)
            generated["ur_girders"] = girder_path
            logger.info("Generated Girder UR chart: %s", girder_path)
        except Exception as exc:
            logger.warning("Failed to generate girder UR chart: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # Individual Deck Slab UR Chart
    # ─────────────────────────────────────────────────────────────────────────
    if deck_checks:
        try:
            fig, ax = plt.subplots(figsize=(8.0, 4.2), dpi=300)
            labels = [c[0] for c in deck_checks]
            values = [c[1] for c in deck_checks]
            y_pos = np.arange(len(labels))
            colors = ["#2e7d32" if v <= 0.85 else "#e65100" if v <= 1.0 else "#c62828" for v in values]

            bars = ax.barh(y_pos, values, color=colors, height=0.52, edgecolor="#37474f", linewidth=0.6)
            ax.axvline(1.0, color="#b71c1c", linestyle="--", linewidth=1.5, alpha=0.9, label="Limit (1.00)")
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=9.0, color="#1a252f")
            ax.invert_yaxis()
            ax.set_xlabel("Utilization Ratio = Demand / Capacity", fontsize=9.5, fontweight="bold", color="#2c3e50")
            ax.set_title("Concrete Deck Slab — Utilization Ratio Summary (IRC 112 / IRC 22)", fontsize=11, fontweight="bold", pad=12, color="#0d47a1")
            ax.set_xlim(0, max(max(values) * 1.25, 1.30))
            ax.grid(axis="x", linestyle=":", alpha=0.6, color="#90a4ae")
            ax.set_axisbelow(True)

            for bar, val in zip(bars, values):
                w = bar.get_width()
                tag = f" {val:.2f} (FAIL)" if val > 1.0 else f" {val:.2f} (PASS)"
                text_color = "#b71c1c" if val > 1.0 else "#1b5e20"
                ax.text(w + 0.02, bar.get_y() + bar.get_height() / 2, tag, va="center", ha="left", fontsize=8.5, fontweight="bold", color=text_color)

            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
            ax.spines["left"].set_color("#78909c")
            ax.spines["bottom"].set_color("#78909c")

            plt.tight_layout()
            deck_path = os.path.join(output_dir, "ur_deck_chart.png").replace("\\", "/")
            plt.savefig(deck_path, bbox_inches="tight", dpi=300)
            plt.close(fig)
            generated["ur_deck"] = deck_path
            logger.info("Generated Deck UR chart: %s", deck_path)
        except Exception as exc:
            logger.warning("Failed to generate deck UR chart: %s", exc)

    return generated
