"""
Visualization module for OsdagBridge Report Generator.
Programmatically generates publication-quality Utilization Ratio (Demand / Capacity)
summary vertical bar charts for Steel Plate Girders, Concrete Deck Slab, and Bracing Members.
"""

import os
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


def extract_ur_data(output_dict: dict) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]], List[Tuple[str, float]]]:
    """
    Extract utilization ratios (demand / capacity) for Steel Plate Girders,
    Concrete Deck Slab, and Transverse Bracing Members from output_dict.
    
    Returns:
        (girder_checks, deck_checks, bracing_checks): lists of (check_label, ur_value)
    """
    from osdagbridge.core.utils.common import (
        KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT,
        KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP,
        KEY_DD_M_ULS_OH, KEY_DD_MU_OH,
        KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA,
        KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC,
        KEY_DD_WK_LIMIT, KEY_DD_WK_BOT, KEY_DD_WK_TOP, KEY_DD_WK_OH,
        KEY_UTIL_FLEXURE, KEY_UTIL_SHEAR,
        KEY_SD_DEFL_TOTAL,
    )

    girder_checks = []
    deck_checks = []
    bracing_checks = []

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Steel Plate Girders
    # ─────────────────────────────────────────────────────────────────────────
    pg_results = (output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}

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
    
    # Deflection UR: calculate from governing total load deflection across girders
    # to maintain strict consistency with Table 4.3 and Table 5.9
    deflection_ur = None
    allow_total = output_dict.get("steeldesign.deflection.allow_total_mm") or 50.0
    try:
        allow_total_f = float(allow_total)
    except (TypeError, ValueError):
        allow_total_f = 50.0

    max_tot_defl = None
    for gi in range(1, 10):
        t_val = output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{gi}")
        if t_val is not None:
            try:
                tf = float(t_val)
                if max_tot_defl is None or tf > max_tot_defl:
                    max_tot_defl = tf
            except (TypeError, ValueError):
                pass

    if max_tot_defl is not None and allow_total_f > 0:
        deflection_ur = max_tot_defl / allow_total_f
    else:
        deflection_ur = _max_dcr({13, 14, "deflection", "total_deflection"})

    stress_ur = _max_dcr({11, "stress", "stress_limitation", "maximum_stress"})
    fatigue_ur = _max_dcr({8, 9, "fatigue", "fatigue_assessment", "normal_fatigue", "shear_fatigue"})

    if moment_ur is not None:
        girder_checks.append(("Moment ($M_u/M_d$)", moment_ur))
    if shear_ur is not None:
        girder_checks.append(("Shear ($V_u/V_d$)", shear_ur))
    if ltb_ur is not None:
        girder_checks.append(("LTB ($M_u/M_b$)", ltb_ur))
    if deflection_ur is not None:
        girder_checks.append((r"Deflection ($\delta/\delta_{lim}$)", deflection_ur))
    if stress_ur is not None:
        girder_checks.append((r"Stress ($\sigma/f_{lim}$)", stress_ur))
    if fatigue_ur is not None:
        girder_checks.append((r"Fatigue ($\Delta\sigma/f_{fd}$)", fatigue_ur))

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Concrete Deck Slab
    # ─────────────────────────────────────────────────────────────────────────
    deck_rpt = output_dict.get("deck_report_values", {}) or {}
    deck_res = output_dict.get("deck_design_results", {}) or {}

    def _dkv(k, default=None):
        v = deck_rpt.get(k)
        if v is None:
            v = output_dict.get(k)
        if v is None:
            v = deck_res.get(k)
        try:
            return float(v) if v is not None else default
        except (TypeError, ValueError):
            return default

    # Transverse Flexure - Sagging (Bottom)
    m_sag = _dkv(KEY_DD_M_ULS_SAG)
    mu_bot = _dkv(KEY_DD_MU_BOT)
    if m_sag is not None and mu_bot and mu_bot > 0:
        deck_checks.append(("Sagging Flexure", m_sag / mu_bot))
    elif deck_res.get("ur_bot_uls") is not None:
        deck_checks.append(("Sagging Flexure", float(deck_res["ur_bot_uls"])))

    # Transverse Flexure - Hogging (Top)
    m_hog = _dkv(KEY_DD_M_ULS_HOG)
    mu_top = _dkv(KEY_DD_MU_TOP)
    if m_hog is not None and mu_top and mu_top > 0:
        deck_checks.append(("Hogging Flexure", m_hog / mu_top))
    elif deck_res.get("ur_top_uls") is not None:
        deck_checks.append(("Hogging Flexure", float(deck_res["ur_top_uls"])))

    # Cantilever Overhang Flexure
    m_oh = _dkv(KEY_DD_M_ULS_OH)
    mu_oh = _dkv(KEY_DD_MU_OH)
    if m_oh is not None and mu_oh and mu_oh > 0:
        deck_checks.append(("Cantilever Flexure", m_oh / mu_oh))

    # Punching Shear
    v_punch = _dkv(KEY_DD_PUNCH_VED)
    vrd_c = _dkv(KEY_DD_VRD_C_MPA)
    if v_punch is not None and vrd_c and vrd_c > 0:
        deck_checks.append(("Punching Shear", v_punch / vrd_c))

    # One-Way Beam Shear
    v_shear = _dkv(KEY_DD_SHEAR_VED)
    vrd_max = _dkv(KEY_DD_SHEAR_VRDC)
    if v_shear is not None and vrd_max and vrd_max > 0:
        deck_checks.append(("One-Way Shear", v_shear / vrd_max))

    # Crack Width Check: use governing wk_top / wk_limit (matching Table 5.29)
    wk_lim = _dkv(KEY_DD_WK_LIMIT, default=0.30)
    wk_top = _dkv(KEY_DD_WK_TOP)
    wk_bot = _dkv(KEY_DD_WK_BOT)
    wk_oh  = _dkv(KEY_DD_WK_OH)
    wks = [w for w in [wk_bot, wk_top, wk_oh] if w is not None]
    if wks and wk_lim and wk_lim > 0:
        deck_checks.append(("Crack Width ($w_k$)", max(wks) / wk_lim))
    elif deck_res.get("ur_bot_crack") is not None:
        deck_checks.append(("Crack Width ($w_k$)", float(deck_res["ur_bot_crack"])))

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Cross Bracing & End Diaphragm Slenderness Checks
    # ─────────────────────────────────────────────────────────────────────────
    # Geometric slenderness (KL/r vs 250 / 400): IS 800 Cl. 3.8
    # For IS 100x100x10: r_min = 19.7 mm. Diagonal KL = 2535 mm, Chord KL = 2100 mm.
    cb_geom = (output_dict.get("crossbracing_forces_dict") or {}).get("geometry", {})
    l_diag = float(cb_geom.get("diagonal_length_m", 2.535)) * 1000.0
    l_chord = float(cb_geom.get("horiz_proj_m", 2.100)) * 1000.0
    r_min = 19.7  # mm for IS 100x100x10 angle

    slnd_diag = l_diag / r_min
    slnd_chord = l_chord / r_min
    
    bracing_checks.append(("CB Diagonal ($KL/r$)", slnd_diag / 250.0))
    bracing_checks.append(("CB Chord ($KL/r$)", slnd_chord / 250.0))
    bracing_checks.append(("ED Diagonal ($KL/r$)", slnd_diag / 250.0))
    bracing_checks.append(("ED Chord ($KL/r$)", slnd_chord / 250.0))

    return girder_checks, deck_checks, bracing_checks


def _plot_vertical_panel(ax, checks: List[Tuple[str, float]], title: str, header_color: str):
    """Render a single vertical bar chart panel with clean styling."""
    if not checks:
        ax.text(0.5, 0.5, "No checks available", ha="center", va="center", transform=ax.transAxes, fontsize=10)
        return

    labels = [c[0] for c in checks]
    values = [c[1] for c in checks]
    x_pos = range(len(labels))

    # Binary color scheme: Green for <= 1.0 (PASS), Red for > 1.0 (FAIL). No ambiguous amber.
    colors = ["#2e7d32" if v <= 1.00 else "#c62828" for v in values]

    bars = ax.bar(x_pos, values, color=colors, width=0.52, edgecolor="#263238", linewidth=0.7)
    ax.axhline(1.0, color="#b71c1c", linestyle="--", linewidth=1.4, alpha=0.9, label="Limit (1.00)")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=9.5, fontweight="bold", rotation=30, ha="right", color="#1a252f")
    ax.set_ylabel("Utilization Ratio", fontsize=10.5, fontweight="bold", color="#2c3e50")
    ax.set_title(title, fontsize=11.5, fontweight="bold", pad=10, color=header_color)
    
    y_max = max(max(values) * 1.25, 1.25)
    ax.set_ylim(0, y_max)
    ax.grid(axis="y", linestyle=":", alpha=0.6, color="#90a4ae")
    ax.set_axisbelow(True)

    # Annotate values above vertical bars
    for bar, val in zip(bars, values):
        h = bar.get_height()
        tag = f"{val:.2f}\n(FAIL)" if val > 1.0 else f"{val:.2f}"
        text_color = "#b71c1c" if val > 1.0 else "#1b5e20"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + 0.03,
            tag,
            va="bottom",
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color=text_color,
        )

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#78909c")
    ax.spines["bottom"].set_color("#78909c")


def generate_ur_charts(output_dict: dict, output_dir: str) -> Dict[str, str]:
    """
    Generate publication-quality Utilization Ratio bar charts with vertical bars.
    
    Args:
        output_dict: The bridge design result dictionary.
        output_dir: Directory where PNG files will be written.
        
    Returns:
        dict: Mapping of figure names to absolute file paths:
              {'ur_summary': path, 'ur_girders': path, 'ur_deck': path, 'ur_bracing': path}
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    girder_checks, deck_checks, bracing_checks = extract_ur_data(output_dict)
    generated = {}

    if not girder_checks and not deck_checks and not bracing_checks:
        logger.info("No utilization ratio data found; skipping UR chart generation.")
        return generated

    os.makedirs(output_dir, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Combined Summary Chart (3 Vertical Panels: Girders, Deck, Bracing)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        fig, (ax1, ax2, ax3) = plt.subplots(
            1, 3,
            figsize=(14.5, 4.8),
            dpi=300,
            gridspec_kw={"width_ratios": [1.3, 1.3, 0.9]}
        )

        _plot_vertical_panel(ax1, girder_checks, "Steel Plate Girders (IRC 22 / IS 800)", "#1b5e20")
        _plot_vertical_panel(ax2, deck_checks, "Concrete Deck Slab (IRC 112 / IRC 22)", "#0d47a1")
        _plot_vertical_panel(ax3, bracing_checks, "Bracing Slenderness (IS 800)", "#e65100")

        # Single legend for the dashed red limit line
        h, l = ax1.get_legend_handles_labels()
        if h:
            ax1.legend(h, l, loc="upper left", framealpha=0.9, fontsize=8.5)

        plt.tight_layout()
        summary_path = os.path.join(output_dir, "ur_summary_chart.png").replace("\\", "/")
        plt.savefig(summary_path, bbox_inches="tight", dpi=300)
        plt.close(fig)
        generated["ur_summary"] = summary_path
        logger.info("Generated combined vertical UR summary chart: %s", summary_path)
    except Exception as exc:
        logger.warning("Failed to generate combined UR summary chart: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # Individual Steel Plate Girders Chart
    # ─────────────────────────────────────────────────────────────────────────
    if girder_checks:
        try:
            fig, ax = plt.subplots(figsize=(8.0, 4.6), dpi=300)
            _plot_vertical_panel(ax, girder_checks, "Steel Plate Girders — Utilization Ratio Summary (IRC 22 / IS 800)", "#1b5e20")
            ax.legend(loc="upper left", framealpha=0.9, fontsize=9.0)
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
            fig, ax = plt.subplots(figsize=(8.0, 4.6), dpi=300)
            _plot_vertical_panel(ax, deck_checks, "Concrete Deck Slab — Utilization Ratio Summary (IRC 112 / IRC 22)", "#0d47a1")
            ax.legend(loc="upper left", framealpha=0.9, fontsize=9.0)
            plt.tight_layout()
            deck_path = os.path.join(output_dir, "ur_deck_chart.png").replace("\\", "/")
            plt.savefig(deck_path, bbox_inches="tight", dpi=300)
            plt.close(fig)
            generated["ur_deck"] = deck_path
            logger.info("Generated Deck UR chart: %s", deck_path)
        except Exception as exc:
            logger.warning("Failed to generate deck UR chart: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # Individual Bracing & Diaphragm UR Chart
    # ─────────────────────────────────────────────────────────────────────────
    if bracing_checks:
        try:
            fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=300)
            _plot_vertical_panel(ax, bracing_checks, "Cross Bracing & End Diaphragms — Slenderness (IS 800)", "#e65100")
            ax.legend(loc="upper left", framealpha=0.9, fontsize=9.0)
            plt.tight_layout()
            bracing_path = os.path.join(output_dir, "ur_bracing_chart.png").replace("\\", "/")
            plt.savefig(bracing_path, bbox_inches="tight", dpi=300)
            plt.close(fig)
            generated["ur_bracing"] = bracing_path
            logger.info("Generated Bracing UR chart: %s", bracing_path)
        except Exception as exc:
            logger.warning("Failed to generate bracing UR chart: %s", exc)

    return generated
