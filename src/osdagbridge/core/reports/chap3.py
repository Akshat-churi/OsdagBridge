# =============================================================================
# Chapter 3: Loads and Load Combinations
# Refactored for clean separation of Vehicular LL & Footpath LL,
# structured unit columns, active vehicle selection, and repeated table headers.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SAFETY_KERB_PRESENT,
    KEY_SAFETY_KERB_WIDTH,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_TS_FOOTPATH_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from osdagbridge.core.reports.styles import (
    STYLE_TWO_COL, STYLE_VEHICULAR_LL, STYLE_FOUR_COL_PARAM, compute_colspec
)
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

STYLE_LOAD_COMBINATIONS = compute_colspec([('C', 0.22), ('p', 0.78)])



def ch3_loads(input_dict):
    span = input_dict.get(KEY_SPAN)
    span_m = 0.0
    if span not in (None, ""):
        try:
            span_m = float(span)
        except Exception:
            span_m = 0.0

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_total_str = "N/A"
    braking_force_kN = 0.0
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_total_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} t)"
        except Exception:
            braking_force_total_str = "N/A"

    # ─────────────────────────────────────────────────────────────────────────
    # Table 3.3: Vehicular Live Loads (LL) --- per IRC 6
    # Active vehicles populated strictly as per UI selection in Loading tab
    # ─────────────────────────────────────────────────────────────────────────
    def _is_truthy(val):
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        return s in ("true", "1", "yes", "checked", "on")

    active_vehicles = []
    if _is_truthy(input_dict.get(KEY_LL_IRC_CLASS_A)):
        active_vehicles.append(('Class A', 554.0, 'cl_208_2', 114.0, 'IRC 6 Cl. 204.1'))
    if _is_truthy(input_dict.get(KEY_LL_IRC_70R_WHEELED)):
        active_vehicles.append(('Class 70R (Wheeled)', 1000.0, 'cl_208_3', 200.0, 'IRC 6 Cl. 204.3'))
    if _is_truthy(input_dict.get(KEY_LL_IRC_70R_TRACKED)):
        active_vehicles.append(('Class 70R (Tracked)', 700.0, 'cl_208_3', 140.0, 'IRC 6 Cl. 204.2'))
    if _is_truthy(input_dict.get(KEY_LL_IRC_AA_WHEELED)):
        active_vehicles.append(('Class AA (Wheeled)', 400.0, 'cl_208_3', 80.0, 'IRC 6 Cl. 204.4'))
    if _is_truthy(input_dict.get(KEY_LL_IRC_AA_TRACKED)):
        active_vehicles.append(('Class AA (Tracked)', 700.0, 'cl_208_3', 140.0, 'IRC 6 Cl. 204.4'))
    if _is_truthy(input_dict.get(KEY_LL_IRC_70R_BOGIE)):
        active_vehicles.append(('Class 70R (Bogie)', 400.0, 'cl_208_3', 80.0, 'IRC 6 Cl. 204.3'))
    if _is_truthy(input_dict.get(KEY_LL_IRC_CLASS_SV)):
        active_vehicles.append(('Class SV (Special Vehicle)', 3850.0, None, 385.0, 'IRC 6 Annex B'))
    if _is_truthy(input_dict.get(KEY_LL_IRC_CLASS_FATIGUE)):
        active_vehicles.append(('Class Fatigue Vehicle', 400.0, None, None, 'IRC 6 Cl. 219'))

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            c_name = c.get('name', 'Custom Vehicle') if isinstance(c, dict) else str(c)
            c_wt = c.get('total_weight', 'N/A') if isinstance(c, dict) else 'N/A'
            active_vehicles.append((c_name, c_wt, None, None, 'Custom Vehicle'))

    # If no vehicle explicitly flagged in inputs (e.g. baseline or defaults), show standard IRC suite
    if not active_vehicles:
        active_vehicles = [
            ('Class A', 554.0, 'cl_208_2', 114.0, 'IRC 6 Cl. 204.1'),
            ('Class 70R (Wheeled)', 1000.0, 'cl_208_3', 200.0, 'IRC 6 Cl. 204.3'),
        ]

    # Horizontal alignment check for centrifugal force
    radius_val = input_dict.get("geometry.radius_of_curvature") or input_dict.get("horizontal_curve_radius")
    is_curved = False
    if radius_val:
        try:
            is_curved = float(radius_val) > 0
        except Exception:
            is_curved = False

    ll_rows = []
    for vname, wt, im_func, brk, ref in active_vehicles:
        wt_str = f"{wt:.1f}" if isinstance(wt, (int, float)) else str(wt)
        if im_func == 'cl_208_2' and span_m > 0:
            im_val = 1.0 + IRC6_2017.cl_208_2_impact_factor(span_m)
            im_str = f"{im_val:.3f}"
        elif im_func == 'cl_208_3' and span_m > 0:
            im_val = 1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)
            im_str = f"{im_val:.3f}"
        else:
            im_str = "1.000"

        brk_str = f"{brk:.1f}" if isinstance(brk, (int, float)) else ("--" if brk is None else str(brk))
        cf_str = "0.00" if is_curved else "N/A (straight span)"

        ll_rows.append(
            f"{_tex(vname)} & {wt_str} & {im_str} & {brk_str} & {cf_str} & {_tex(ref)} \\\\[6pt]\n\\hline"
        )
    ll_table_rows = "\n".join(ll_rows)

    # ─────────────────────────────────────────────────────────────────────────
    # Table 3.4: Footpath Live Load --- per IRC 6
    # Distinct, clearly structured table with parameter, value, unit, and code ref
    # ─────────────────────────────────────────────────────────────────────────
    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    try:
        p_intensity = float(fp_value) if fp_value not in (None, "") else IRC6_2017.cl_206_1_footway_load()
    except Exception:
        p_intensity = 4.905

    fp_width = input_dict.get(KEY_TS_FOOTPATH_WIDTH)
    try:
        fp_w_float = float(fp_width) if fp_width not in (None, "") else 1.50
    except Exception:
        fp_w_float = 1.50

    w_lin = fp_w_float * p_intensity
    has_fp = input_dict.get(KEY_FOOTPATH) or input_dict.get(KEY_TS_NO_OF_FOOTPATHS)
    fp_prov_str = "Present (Both Sides)" if str(has_fp).strip() not in ("0", "None", "False", "no") else "None"

    fp_thickness = _render_value(input_dict, KEY_TS_FOOTPATH_THICKNESS)
    fp_rows = [
        f"Footpath Provision & {_tex(fp_prov_str)} & -- & IRC 5 Cl. 106 \\\\*[6pt]\n\\hline",
        f"Clear Footpath Width, $w_{{fp}}$ & {fp_w_float:.2f} & m & IRC 5 Cl. 106.3 \\\\*[6pt]\n\\hline",
        f"Footpath Slab Thickness & {fp_thickness} & mm & IRC 22 Cl. 602 \\\\*[6pt]\n\\hline",
        f"Pedestrian Live Load Intensity, $p$ & {p_intensity:.3f} & kN/m\\textsuperscript{{2}} & IRC 6 Cl. 206.1 \\\\*[6pt]\n\\hline",
        f"Linear Pedestrian Load ($w_{{fp}} \\times p$) & {w_lin:.2f} & kN/m & IRC 6 Cl. 206.1 \\\\*[6pt]\n\\hline",
        f"Horizontal Kerb / Barrier Load & 5.00 & kN/m & IRC 6 Cl. 206.3 \\\\*[6pt]\n\\hline",
        f"Pedestrian Parapet / Handrail Load & 1.00 & kN/m & IRC 6 Cl. 206.2 \\[6pt]\n\\hline",
    ]
    fp_table_rows = "\n".join(fp_rows)

    # ─────────────────────────────────────────────────────────────────────────
    # Wind Load (WL)
    # ─────────────────────────────────────────────────────────────────────────
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Seismic Load (EL)
    # ─────────────────────────────────────────────────────────────────────────
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah = _res.get("Ah")
            if not sl_av:
                sl_av = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Temperature Load (TL)
    # ─────────────────────────────────────────────────────────────────────────
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise = f"{_bt_max - _mean:.2f}"
            tl_fall = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # Load Combinations
    # ─────────────────────────────────────────────────────────────────────────
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all applied loads and load combinations considered for the structural analysis and design of the bridge superstructure in accordance with IRC 6.

\vspace{1em}
\begin{longtable}{""" + STYLE_TWO_COL + r"""}
\caption{\textbf{Dead Load -- Self Weight}} \\
\hline
\textbf{Parameter} & \textbf{Value / Specification} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{{\footnotesize\textit{\tablename\ \thetable{} -- Continued from previous page}}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Value / Specification} \\[6pt]
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{""" + STYLE_TWO_COL + r"""}
\caption{\textbf{Dead Load for Surfacing (DW)}} \\
\hline
\textbf{Parameter} & \textbf{Value / Specification} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{{\footnotesize\textit{\tablename\ \thetable{} -- Continued from previous page}}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Value / Specification} \\[6pt]
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{""" + STYLE_VEHICULAR_LL + r"""}
\caption{\textbf{Vehicular Live Loads (LL) --- per IRC 6}} \\
\hline
\textbf{Vehicle Class / Model} & \textbf{Gross Load (kN)} & \textbf{Impact Factor ($1+i$)} & \textbf{Braking Force (kN)} & \textbf{Centrifugal Force (kN)} & \textbf{Code Reference} \\[6pt]
\hline
\endfirsthead
\multicolumn{6}{c}{{\footnotesize\textit{\tablename\ \thetable{} -- Continued from previous page}}} \\[4pt]
\hline
\textbf{Vehicle Class / Model} & \textbf{Gross Load (kN)} & \textbf{Impact Factor ($1+i$)} & \textbf{Braking Force (kN)} & \textbf{Centrifugal Force (kN)} & \textbf{Code Reference} \\[6pt]
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
""" + ll_table_rows + r"""
\end{longtable}

\vspace{1em}
\begin{longtable}{""" + STYLE_FOUR_COL_PARAM + r"""}
\caption{\textbf{Footpath Live Load --- per IRC 6}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} & \textbf{Unit} & \textbf{Code Reference} \\[6pt]
\hline
\endfirsthead
\multicolumn{4}{c}{{\footnotesize\textit{\tablename\ \thetable{} -- Continued from previous page}}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Design Value} & \textbf{Unit} & \textbf{Code Reference} \\[6pt]
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
""" + fp_table_rows + r"""
\end{longtable}

\vspace{1em}
\begin{longtable}{""" + STYLE_TWO_COL + r"""}
\caption{\textbf{Wind Load (WL) --- per IRC 6}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{{\footnotesize\textit{\tablename\ \thetable{} -- Continued from previous page}}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict,'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')) + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, ' N/m\\textsuperscript{2}')) + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{""" + STYLE_TWO_COL + r"""}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{{\footnotesize\textit{\tablename\ \thetable{} -- Continued from previous page}}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
\textnormal{Seismic Zone} & """ + (_render_value(input_dict,'seismic_zone')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & """ + '' + r""" kN \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & """ + '' + r""" kN \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{""" + STYLE_TWO_COL + r"""}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}} \\
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{{\footnotesize\textit{\tablename\ \thetable{} -- Continued from previous page}}} \\[4pt]
\hline
\textbf{Parameter} & \textbf{Design Value} \\[6pt]
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{""" + STYLE_LOAD_COMBINATIONS + r"""}
\caption{\textbf{Load Combinations}} \\
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{{\footnotesize\textit{\tablename\ \thetable{} -- Continued from previous page}}} \\[4pt]
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""
