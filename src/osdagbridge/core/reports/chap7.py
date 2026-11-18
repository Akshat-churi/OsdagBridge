from osdagbridge.core.reports.styles import STYLE_BOQ_TABLE

def ch7_quantities(input_dict, fig_paths=None):
    vis_latex = ""
    if fig_paths:
        parts = []
        steel_chart = fig_paths.get("boq_steel_tonnage")
        cr_chart = fig_paths.get("boq_concrete_rebar")
        
        if steel_chart or cr_chart:
            parts.append(r"""
\vspace{1em}
\subsection{Material Quantity Visualizations}
\label{subsec:material-visualizations}
""")
        if steel_chart:
            p = str(steel_chart).replace("\\", "/")
            parts.append(r"""
\begin{figure}[H]
\centering
\includegraphics[width=0.80\textwidth]{""" + p + r"""}
\caption{Structural Steel Tonnage Breakdown by Superstructure Component}
\label{fig:ch7-steel-tonnage}
\par\vspace{3pt}
{\footnotesize\textit{Note: Cross bracing and end diaphragm quantities are reported as N.A. pending transverse member design execution; only girder structural steel tonnage is quantified.}}
\end{figure}
""")
        if cr_chart:
            p = str(cr_chart).replace("\\", "/")
            parts.append(r"""
\begin{figure}[H]
\centering
\includegraphics[width=0.84\textwidth]{""" + p + r"""}
\caption{Concrete Volume ($\text{m}^3$) vs. Reinforcement Steel Weight (MT)}
\label{fig:ch7-concrete-rebar}
\end{figure}
""")
        vis_latex = "\n".join(parts)

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\begingroup
\setlength{\tabcolsep}{3.5pt}
\begin{longtable}{""" + STYLE_BOQ_TABLE + r"""}
\caption{\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}} \\
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\[6pt]
\hline
\endfirsthead
\multicolumn{7}{c}{{\footnotesize\textit{\tablename\ \thetable{} -- Continued from previous page}}} \\[4pt]
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\[6pt]
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
1 & Structural Steel (IS 2062) for Girders & """ + str(input_dict.get("steel_girders_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_qty", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_total", "N.A.")) + r""" \\
\hline
2(a) & Cross Bracing - Top Chord & """ + str(input_dict.get("bracing_top_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_total", "N.A.")) + r""" \\
\hline
2(b) & Cross Bracing - Bottom Chord & """ + str(input_dict.get("bracing_bot_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r""" \\
\hline
2(c) & Cross Bracing - Diagonal Chord & """ + str(input_dict.get("bracing_diag_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r""" \\
\hline
2(d) & End Diaphragms & """ + str(input_dict.get("end_diaphragm_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_qty", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("end_diaphragm_wt_total", "N.A.")) + r""" \\
\hline
3 & Concrete (M40) for Deck Slab & """ + str(input_dict.get("concrete_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_total", "N.A.")) + r""" \\
\hline
4 & Reinforcement Steel (Fe 500) & """ + str(input_dict.get("rebar_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_total", "N.A.")) + r""" \\
\hline
5 & Shear Stud Connectors & """ + str(input_dict.get("shear_studs_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_qty", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_total", "N.A.")) + r""" \\
\hline
6 & Crash Barrier & """ + str(input_dict.get("crash_barrier_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_qty", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_total", "N.A.")) + r""" \\
\hline
\end{longtable}
\endgroup
""" + vis_latex
