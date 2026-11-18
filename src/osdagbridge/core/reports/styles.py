"""
Report styling module: Table geometries, column width presets, and typography.
All table widths are strictly relative to \\linewidth so that tables fit within
the text boundaries and never overflow past the footer rule.
"""

# Tabcolsep is 5pt, arrayrulewidth is 0.5pt.
# Document textwidth is 170mm (483.696 pt).
# For N columns, the horizontal margin overhead is:
#   overhead = (2 * N * 5pt + (N + 1) * 0.5pt) / 483.696pt \approx 0.0217 * N + 0.001
# To guarantee that sum(col_widths) + overhead <= 0.98 * \linewidth, available content ratio is:
#   avail_ratio = 0.98 - overhead

def compute_colspec(cols: list[tuple[str, float]], target_ratio: float = 0.98) -> str:
    """
    Compute a LaTeX column specification where each column width is a fraction of \\linewidth.
    
    Args:
        cols: list of tuples (align_type, weight) where align_type is 'L', 'C', 'R', or 'p'.
        target_ratio: maximum total width of table as fraction of \\linewidth (default 0.98).
    
    Returns:
        Formatted colspec string, e.g. '|C{0.100\\linewidth}|C{0.270\\linewidth}|...|'
    """
    n = len(cols)
    linewidth_pt = 483.696
    margin_pt = 2.0 * n * 5.0 + (n + 1.0) * 0.5
    margin_ratio = margin_pt / linewidth_pt
    avail_ratio = max(0.1, target_ratio - margin_ratio)
    
    total_w = sum(w for _, w in cols)
    parts = ['|']
    for align, w in cols:
        ratio = (w / total_w) * avail_ratio
        parts.append(f"{align}{{{ratio:.3f}\\linewidth}}|")
    return ''.join(parts)


# ── PRESET TABLE STYLES (RELATIVE TO \linewidth) ──────────────────────────────

# 2-column tables (e.g. Parameter / Value)
STYLE_TWO_COL = compute_colspec([('L', 0.38), ('p', 0.62)])

# 3-column tables (e.g. Girder Section Properties, Transverse Shear)
STYLE_GIRDER_PROPERTIES = compute_colspec([('C', 0.18), ('L', 0.48), ('C', 0.34)])
STYLE_STIFFENER_SUMMARY = compute_colspec([('C', 0.18), ('L', 0.41), ('p', 0.41)])
STYLE_TRANSVERSE_SHEAR = compute_colspec([('L', 0.35), ('p', 0.45), ('C', 0.20)])

# 4-column tables (e.g. Footpath Live Load, Shear Connectors, Deck Overhang/Punching)
STYLE_FOUR_COL_PARAM = compute_colspec([('L', 0.38), ('C', 0.18), ('C', 0.16), ('p', 0.28)])
STYLE_SHEAR_CONN_CAP = compute_colspec([('L', 0.26), ('C', 0.34), ('C', 0.20), ('L', 0.20)])
STYLE_SHEAR_CONN_SPACE = compute_colspec([('L', 0.25), ('C', 0.30), ('C', 0.30), ('C', 0.15)])
STYLE_DECK_CHECK_4COL = compute_colspec([('L', 0.35), ('C', 0.22), ('C', 0.25), ('C', 0.18)])
STYLE_REBAR_SUMMARY = compute_colspec([('L', 0.32), ('C', 0.27), ('C', 0.27), ('C', 0.14)])

# 5-column tables (e.g. Capacity Checks, Deflection, Section Classification, Overall Summary)
# Table 5.2 Section Classification
STYLE_SECTION_CLASSIFICATION = compute_colspec([('C', 0.12), ('L', 0.22), ('C', 0.24), ('C', 0.20), ('C', 0.22)])
# Tables 5.3, 5.4, 5.5, 5.6, 5.8 Capacity Checks (Girder, Governing LC, Demand, Capacity, Status)
STYLE_CAPACITY_CHECK = compute_colspec([('C', 0.10), ('C', 0.30), ('C', 0.20), ('C', 0.20), ('C', 0.20)])
# Table 5.9 Deflection Check (Girder, Parameter, Actual, Allowable, Status)
STYLE_DEFLECTION_CHECK = compute_colspec([('C', 0.12), ('L', 0.28), ('C', 0.20), ('C', 0.20), ('C', 0.20)])
# Tables 5.10, 5.11 Serviceability Stress and Fatigue
STYLE_SERVICEABILITY = compute_colspec([('C', 0.12), ('L', 0.28), ('C', 0.20), ('C', 0.20), ('C', 0.20)])
# Table 5.17 Deck Slab Flexure
STYLE_DECK_FLEXURE_INTERIOR = compute_colspec([('C', 0.16), ('C', 0.22), ('C', 0.22), ('C', 0.24), ('C', 0.16)])
# Table 5.29 Overall Design Check Summary (Member/Check, Governing LC, Demand, Capacity, UR)
STYLE_OVERALL_SUMMARY = compute_colspec([('C', 0.22), ('L', 0.28), ('C', 0.20), ('C', 0.20), ('C', 0.10)])

# 6-column tables (e.g. Live Loads Table 3.3, Cross Bracing / Diaphragm Connections & Slenderness)
STYLE_VEHICULAR_LL = compute_colspec([('L', 0.22), ('C', 0.13), ('C', 0.14), ('C', 0.14), ('C', 0.21), ('p', 0.16)])
STYLE_BRACING_CONNECTION = compute_colspec([('C', 0.14), ('L', 0.18), ('L', 0.18), ('C', 0.20), ('C', 0.15), ('C', 0.15)])
STYLE_BRACING_SLENDERNESS = compute_colspec([('C', 0.14), ('L', 0.16), ('L', 0.16), ('C', 0.18), ('C', 0.16), ('C', 0.20)])

# 7-column tables (e.g. Table 5.12 Girder Design Summary DCR, Table 7.1 BOQ)
STYLE_GIRDER_DCR_SUMMARY = compute_colspec([('C', 0.08), ('L', 0.26), ('C', 0.16), ('C', 0.16), ('C', 0.10), ('C', 0.10), ('C', 0.14)])
STYLE_BOQ_TABLE = compute_colspec([('C', 0.06), ('L', 0.28), ('C', 0.20), ('C', 0.10), ('C', 0.12), ('C', 0.12), ('C', 0.12)])

# 8-column tables (e.g. Tables 5.24, 5.28 Cross Bracing / End Diaphragm Capacity Summary)
STYLE_BRACING_CAPACITY = compute_colspec([('C', 0.09), ('L', 0.11), ('C', 0.13), ('C', 0.21), ('C', 0.13), ('C', 0.13), ('C', 0.08), ('C', 0.12)])

# Chapter 2 Tables
STYLE_GIRDER_GENERAL_INFO = compute_colspec([('C', 0.12), ('C', 0.15), ('C', 0.23), ('C', 0.25), ('C', 0.25)])
STYLE_GIRDER_DIMENSIONS = compute_colspec([('C', 0.10), ('C', 0.18), ('C', 0.16), ('C', 0.28), ('C', 0.28)])
STYLE_GIRDER_STIFFENERS = compute_colspec([('C', 0.08), ('p', 0.22), ('p', 0.18), ('p', 0.24), ('p', 0.14), ('p', 0.14)])
STYLE_BRACING_PROPERTIES = compute_colspec([('C', 0.14), ('C', 0.18), ('C', 0.20), ('C', 0.28), ('C', 0.20)])

# Chapter 4 Analysis Tables
STYLE_MAX_DEMANDS_9COL = compute_colspec([('C', 0.20), ('C', 0.10), ('C', 0.08), ('C', 0.09), ('C', 0.10), ('C', 0.08), ('C', 0.09), ('C', 0.13), ('C', 0.13)])
STYLE_REACTIONS_3COL = compute_colspec([('C', 0.34), ('C', 0.33), ('C', 0.33)])

# Chapter 8 Standards Tables
STYLE_CODES_3COL = compute_colspec([('C', 0.16), ('C', 0.14), ('L', 0.70)])
