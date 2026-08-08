"""
theme.py — "Contract Intelligence Command Room" visual identity.

Design plan (kept here rather than scattered across pages):

Color   — exact palette provided by spec (see COLORS below). Dark
          investigation-room base (#0A0E17 / #141A26 / #1C2433), warm
          paper (#F5F1E8) reserved ONLY for contract/document text so
          it reads as a physical exhibit inside a dark room, gold
          accents (#C6A15B / #9C7A3B) for the case-file system, and a
          restrained set of investigation-marker colors (risk /
          compliance / modified / evidence / missing) used nowhere
          else.

Type    — three roles, none of them a default SaaS pairing:
          - "IBM Plex Mono"   — case-file eyebrows, evidence tags,
            risk markers, stamps, nav labels. Uppercase, letter-spaced.
            Reads like a typewritten case log.
          - "Source Serif 4"  — contract paper text and the report
            dossier body. Reads like a printed legal document.
          - "IBM Plex Sans"   — ordinary UI chrome (buttons, inputs,
            captions) so it stays quiet and doesn't compete with the
            document/evidence material.

Layout  — panels are "case files": slate panels with a 4px gold
          left-bar and a monospace eyebrow label, not cards with
          shadows-all-around. Contract text sits on a literal paper
          surface with a dashed binder-strip top edge and an "EXHIBIT"
          corner tag.

Signature — the Evidence Tag: a small rectangle with a colored dot +
          uppercase monospace label + thin dashed border. It recurs as
          the risk marker, the clause-type legend, the pipeline
          stage-status stamp, and the compliance-matrix indicator —
          one motif holding the whole platform together.
"""
import streamlit as st

COLORS = {
    "bg": "#0A0E17",
    "panel": "#141A26",
    "panel2": "#1C2433",
    "paper": "#F5F1E8",
    "paper_border": "#D8CDB8",
    "gold": "#C6A15B",
    "gold_muted": "#9C7A3B",
    "evidence": "#4D6B8A",
    "success": "#3E6B48",
    "warning": "#B5893D",
    "critical": "#8C2F39",
    "missing": "#6B4D2A",
    "text": "#E8E6E3",
    "text_muted": "#A0A8B5",
}

RISK_COLOR = {
    "Low": COLORS["success"],
    "Moderate": COLORS["warning"],
    "High": "#A8632F",
    "Critical": COLORS["critical"],
}

CLAUSE_TYPE_COLOR = {
    "risk": COLORS["critical"],
    "compliance": COLORS["success"],
    "modified": COLORS["warning"],
    "evidence": COLORS["evidence"],
    "missing": COLORS["missing"],
}


def inject_global_css():
    c = COLORS
    st.markdown(f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"] {{
            font-family: 'IBM Plex Sans', sans-serif;
        }}
        .stApp {{
            background: {c['bg']};
            background-image:
                radial-gradient(ellipse at top left, rgba(198,161,91,0.04) 0%, transparent 45%),
                radial-gradient(ellipse at bottom right, rgba(77,107,138,0.05) 0%, transparent 50%);
        }}

        /* ---- FULL-WIDTH ENTERPRISE LAYOUT ----
           Streamlit's default `.block-container` caps content at ~730-1200px
           and centers it, which is what creates the large empty margins on
           wide/ultrawide monitors. Override it to use the full viewport,
           at every breakpoint Streamlit ships (mobile/tablet/desktop). */
        .main .block-container,
        [data-testid="stAppViewContainer"] .main .block-container,
        section.main > div.block-container {{
            max-width: 100% !important;
            width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-top: 1.5rem !important;
        }}
        [data-testid="stAppViewContainer"] {{
            max-width: 100% !important;
        }}
        [data-testid="stHorizontalBlock"] {{
            gap: 1.2rem;
        }}
        /* Streamlit sets an internal max-width via inline style on some
           versions of the block container — this catches that too. */
        div[data-testid="stMainBlockContainer"] {{
            max-width: 100% !important;
        }}
        @media (min-width: 1920px) {{
            .main .block-container {{ padding-left: 3rem !important; padding-right: 3rem !important; }}
        }}
        @media (min-width: 2560px) {{
            .main .block-container {{ padding-left: 4.5rem !important; padding-right: 4.5rem !important; }}
        }}
        section[data-testid="stSidebar"] {{
            background: {c['panel']};
            border-right: 1px solid #26304533;
        }}
        h1, h2, h3 {{
            font-family: 'IBM Plex Mono', monospace !important;
            letter-spacing: 0.03em;
            color: {c['text']} !important;
        }}
        h1 {{
            border-bottom: 1px solid #2A3346;
            padding-bottom: 0.5rem;
        }}
        p, span, div, label {{
            color: {c['text']};
        }}
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: {c['text_muted']} !important;
            font-family: 'IBM Plex Mono', monospace !important;
            letter-spacing: 0.02em;
            font-size: 0.78rem !important;
        }}

        .stButton > button, .stDownloadButton > button {{
            background: transparent;
            color: {c['gold']};
            border: 1px solid {c['gold_muted']};
            border-radius: 2px;
            font-family: 'IBM Plex Mono', monospace;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.5rem 1.2rem;
            transition: all 0.15s ease;
            width: 100%;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            background: {c['gold']};
            color: {c['bg']};
            border-color: {c['gold']};
        }}
        .stButton > button:disabled, .stDownloadButton > button:disabled {{
            color: {c['text_muted']};
            border-color: #2A3346;
        }}

        .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {{
            background: {c['panel2']} !important;
            color: {c['text']} !important;
            border: 1px solid #2A3346 !important;
            border-radius: 2px !important;
            font-family: 'IBM Plex Sans', sans-serif !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
            border-bottom: 1px solid #2A3346;
        }}
        .stTabs [data-baseweb="tab"] {{
            background: {c['panel']};
            border: 1px solid #2A3346;
            border-bottom: none;
            border-radius: 2px 2px 0 0;
            font-family: 'IBM Plex Mono', monospace;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            font-size: 0.72rem;
            color: {c['text_muted']};
            padding: 0.6rem 1rem;
        }}
        .stTabs [aria-selected="true"] {{
            background: {c['panel2']};
            color: {c['gold']} !important;
            border-color: {c['gold_muted']};
        }}

        .streamlit-expanderHeader, [data-testid="stExpander"] summary {{
            background: {c['panel']} !important;
            border: 1px solid #2A3346 !important;
            border-left: 3px solid {c['gold_muted']} !important;
            border-radius: 2px !important;
            font-family: 'IBM Plex Mono', monospace !important;
            font-size: 0.8rem !important;
            letter-spacing: 0.02em;
        }}
        [data-testid="stExpander"] {{
            background: transparent !important;
            border: none !important;
        }}

        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {c['panel']};
            border: 1px solid #2A3346 !important;
            border-radius: 2px !important;
        }}

        [data-testid="stMetric"] {{
            background: {c['panel']};
            border: 1px solid #2A3346;
            border-left: 3px solid {c['gold_muted']};
            padding: 0.7rem 1rem;
            border-radius: 2px;
        }}
        [data-testid="stMetricLabel"] {{
            font-family: 'IBM Plex Mono', monospace !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.68rem !important;
            color: {c['text_muted']} !important;
        }}
        [data-testid="stMetricValue"] {{
            font-family: 'IBM Plex Mono', monospace !important;
            color: {c['gold']} !important;
        }}

        [data-testid="stAlert"] {{
            border-radius: 2px;
            border: 1px solid #2A3346;
            font-family: 'IBM Plex Sans', sans-serif;
        }}

        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-track {{ background: {c['bg']}; }}
        ::-webkit-scrollbar-thumb {{ background: #2A3346; border-radius: 5px; }}

        .li-eyebrow {{
            font-family: 'IBM Plex Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.68rem;
            color: {c['gold_muted']};
            margin-bottom: 0.35rem;
        }}

        .li-panel {{
            background: {c['panel']};
            border: 1px solid #232C40;
            border-left: 4px solid {c['gold_muted']};
            border-radius: 2px;
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
        }}

        .li-tag {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-family: 'IBM Plex Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.3rem 0.65rem;
            border: 1px dashed;
            border-radius: 2px;
            background: {c['panel2']};
            margin: 0.15rem 0.3rem 0.15rem 0;
        }}
        .li-tag .li-dot {{
            width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
        }}

        .li-paper-wrap {{
            background: {c['paper']};
            border: 1px solid {c['paper_border']};
            border-top: 3px dashed {c['paper_border']};
            border-radius: 1px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.45), 0 2px 6px rgba(0,0,0,0.3);
            padding: 2.2rem 2.4rem;
            position: relative;
            color: #2A2418;
            font-family: 'Source Serif 4', serif;
            line-height: 1.65;
            font-size: 0.95rem;
            max-height: 560px;
            overflow-y: auto;
        }}
        .li-paper-wrap::before {{
            content: "EXHIBIT";
            position: absolute;
            top: 14px; right: -34px;
            transform: rotate(90deg);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.65rem;
            letter-spacing: 0.18em;
            color: {c['paper_border']};
        }}
        .li-paper-wrap h1, .li-paper-wrap h2, .li-paper-wrap h3,
        .li-paper-wrap p, .li-paper-wrap span, .li-paper-wrap div {{
            color: #2A2418 !important;
            font-family: 'Source Serif 4', serif !important;
        }}
        .li-dossier {{ max-height: none; }}
        .li-dossier h2 {{
            font-family: 'IBM Plex Mono', monospace !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.95rem !important;
            color: #6B5A34 !important;
            border-bottom: 1px solid {c['paper_border']};
            padding-bottom: 0.3rem;
            margin-top: 1.6rem;
        }}
        .li-dossier blockquote {{
            border-left: 3px solid {c['gold_muted']};
            padding-left: 0.8rem;
            color: #5A5138 !important;
            font-style: italic;
        }}
        .li-dossier table {{
            width: 100%; border-collapse: collapse; font-size: 0.88rem;
        }}
        .li-dossier th, .li-dossier td {{
            border-bottom: 1px solid {c['paper_border']};
            padding: 0.4rem 0.5rem;
            text-align: left;
        }}

        .li-divider {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin: 1.6rem 0 0.9rem 0;
        }}
        .li-divider .li-line {{
            flex: 1;
            height: 1px;
            background: linear-gradient(90deg, {c['gold_muted']}, transparent);
        }}
        .li-divider .li-label {{
            font-family: 'IBM Plex Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.78rem;
            color: {c['gold']};
            white-space: nowrap;
        }}

        .li-pipeline-step {{
            display: flex;
            align-items: flex-start;
            gap: 0.9rem;
            padding: 0.7rem 0.2rem;
            border-bottom: 1px solid #1E2636;
        }}
        .li-pipeline-step:last-child {{ border-bottom: none; }}
        .li-pipeline-marker {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            width: 26px; height: 26px;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            border: 1px solid {c['gold_muted']};
            color: {c['gold']};
            flex-shrink: 0;
        }}

        /* Full-width horizontal pipeline (Command Room home page) */
        .li-pipeline-horizontal {{
            display: flex;
            width: 100%;
            border: 1px solid #232C40;
            border-radius: 2px;
            background: {c['panel']};
            overflow-x: auto;
        }}
        .li-pipeline-hstep {{
            flex: 1 1 0;
            min-width: 130px;
            text-align: center;
            padding: 1rem 0.6rem;
            border-right: 1px solid #232C40;
            position: relative;
        }}
        .li-pipeline-hstep:last-child {{ border-right: none; }}
        .li-pipeline-hmarker {{
            width: 30px; height: 30px;
            margin: 0 auto 0.5rem auto;
            border-radius: 50%;
            border: 1px solid {c['gold_muted']};
            color: {c['gold']};
            display: flex; align-items: center; justify-content: center;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.75rem;
        }}
        .li-pipeline-hname {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.02em;
            color: {c['text']};
            line-height: 1.3;
        }}
        .li-pipeline-hstatus {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.58rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {c['text_muted']};
            margin-top: 0.3rem;
        }}

        .li-matrix {{
            width: 100%;
            border-collapse: collapse;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.85rem;
        }}
        .li-matrix th {{
            text-align: left;
            font-family: 'IBM Plex Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.68rem;
            color: {c['text_muted']};
            border-bottom: 1px solid {c['gold_muted']};
            padding: 0.5rem 0.6rem;
        }}
        .li-matrix td {{
            border-bottom: 1px solid #1E2636;
            padding: 0.55rem 0.6rem;
            color: {c['text']};
        }}
        .li-matrix tr:hover td {{ background: #161D2C; }}

        .li-redline-col {{
            background: {c['panel']};
            border: 1px solid #232C40;
            border-radius: 2px;
            padding: 0.9rem 1rem;
        }}
        .li-redline-added {{
            background: rgba(62,107,72,0.18);
            border-left: 3px solid {c['success']};
            padding: 0.5rem 0.7rem;
            margin: 0.35rem 0;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.85rem;
        }}
        .li-redline-removed {{
            background: rgba(140,47,57,0.16);
            border-left: 3px solid {c['critical']};
            padding: 0.5rem 0.7rem;
            margin: 0.35rem 0;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.85rem;
            text-decoration: line-through;
            text-decoration-color: {c['critical']}88;
        }}
        .li-redline-modified {{
            background: rgba(181,137,61,0.16);
            border-left: 3px solid {c['warning']};
            padding: 0.5rem 0.7rem;
            margin: 0.35rem 0;
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.85rem;
        }}

        /* Auto-fit responsive card grid (Risk Dashboard) */
        .li-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1rem;
            width: 100%;
        }}

        /* Metrics header strip */
        .li-metrics-header {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 1px;
            background: #232C40;
            border: 1px solid #232C40;
            border-radius: 2px;
            overflow: hidden;
            margin-bottom: 1.2rem;
        }}
        .li-metric-cell {{
            background: {c['panel']};
            padding: 0.8rem 1rem;
        }}
        .li-metric-label {{
            font-family: 'IBM Plex Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.64rem;
            color: {c['text_muted']};
            margin-bottom: 0.3rem;
        }}
        .li-metric-value {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.3rem;
            color: {c['gold']};
        }}

        /* Agent execution timeline */
        .li-timeline-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.55rem 0;
            border-bottom: 1px solid #1E2636;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.78rem;
        }}
        .li-timeline-item:last-child {{ border-bottom: none; }}
        .li-timeline-stamp {{
            color: {c['text_muted']};
            font-size: 0.7rem;
        }}

        /* Evidence / citation panel */
        .li-evidence-item {{
            border: 1px solid #232C40;
            border-left: 3px solid {c['evidence']};
            background: {c['panel']};
            border-radius: 2px;
            padding: 0.6rem 0.8rem;
            margin-bottom: 0.6rem;
            font-size: 0.8rem;
        }}
        .li-evidence-meta {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.66rem;
            color: {c['evidence']};
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.25rem;
        }}

        /* Download bar */
        .li-download-label {{
            font-family: 'IBM Plex Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 0.68rem;
            color: {c['text_muted']};
            margin: 0.6rem 0 0.3rem 0;
        }}
    </style>
    """, unsafe_allow_html=True)


def eyebrow(text: str) -> str:
    return f'<div class="li-eyebrow">{text}</div>'


def panel_open(eyebrow_text: str) -> str:
    return f'<div class="li-panel">{eyebrow(eyebrow_text)}'


def panel_close() -> str:
    return "</div>"


def risk_marker(level: str) -> str:
    color = RISK_COLOR.get(level, COLORS["text_muted"])
    label = f"{level.upper()} RISK" if level != "Critical" else "CRITICAL"
    return (
        f'<span class="li-tag" style="border-color:{color}; color:{color};">'
        f'<span class="li-dot" style="background:{color};"></span>{label}</span>'
    )


def clause_tag(kind: str, label: str) -> str:
    color = CLAUSE_TYPE_COLOR.get(kind, COLORS["text_muted"])
    return (
        f'<span class="li-tag" style="border-color:{color}; color:{color};">'
        f'<span class="li-dot" style="background:{color};"></span>{label}</span>'
    )


def contract_paper(body_html: str) -> str:
    return f'<div class="li-paper-wrap">{body_html}</div>'


def render_dossier(markdown_text: str, case_title: str = "LEGAL INTELLIGENCE REPORT", case_id: str = "") -> str:
    """Converts report markdown into a styled 'dossier' HTML block —
    cover header, then the rendered body, inside a paper-toned panel.
    Used instead of raw st.markdown() so the report reads as a printed
    legal document, not a markdown block."""
    import markdown as _md
    body_html = _md.markdown(markdown_text, extensions=["tables", "fenced_code"])
    header = (
        f'<div style="border-bottom:2px solid #D8CDB8; margin-bottom:1.2rem; padding-bottom:0.8rem;">'
        f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:0.68rem; letter-spacing:0.16em; color:#9C7A3B;">{case_title}</div>'
        + (f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:0.68rem; color:#8a7a5c; margin-top:0.2rem;">CASE ID: {case_id}</div>' if case_id else "")
        + "</div>"
    )
    return f'<div class="li-paper-wrap li-dossier">{header}{body_html}</div>'


def section_divider(label: str) -> str:
    return (
        '<div class="li-divider"><div class="li-line"></div>'
        f'<div class="li-label">{label}</div><div class="li-line"></div></div>'
    )


def pipeline_step(index: int, name: str, status: str = "complete") -> str:
    marker = "&#10003;" if status == "complete" else ("&hellip;" if status == "active" else str(index))
    dim = "opacity:0.4;" if status == "pending" else ""
    status_label = "case closed" if status == "complete" else ("in progress" if status == "active" else "pending")
    return (
        f'<div class="li-pipeline-step" style="{dim}">'
        f'<div class="li-pipeline-marker">{marker}</div>'
        f'<div style="padding-top:2px;">'
        f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:0.85rem; letter-spacing:0.03em;">{name}</div>'
        f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:0.62rem; color:{COLORS["text_muted"]}; text-transform:uppercase; letter-spacing:0.1em;">'
        f'{status_label}</div>'
        f'</div></div>'
    )


def pipeline_horizontal(steps: list) -> str:
    """steps: list of (name, status) where status is complete/active/pending.
    Renders a single full-width horizontal strip — used on the Command
    Room home page so the pipeline spans edge to edge instead of
    sitting in a narrow vertical list."""
    cells = "".join(
        f'<div class="li-pipeline-hstep">'
        f'<div class="li-pipeline-hmarker">{"&#10003;" if status == "complete" else ("&hellip;" if status == "active" else str(i + 1))}</div>'
        f'<div class="li-pipeline-hname">{name}</div>'
        f'<div class="li-pipeline-hstatus">{"case closed" if status == "complete" else ("in progress" if status == "active" else "pending")}</div>'
        f'</div>'
        for i, (name, status) in enumerate(steps)
    )
    return f'<div class="li-pipeline-horizontal">{cells}</div>'


def metrics_header(metrics: list) -> str:
    """metrics: list of (label, value) tuples. Renders a full-width
    metrics strip — used at the top of Contract Analysis / Compliance /
    Risk pages instead of st.metric cards, so the strip stretches edge
    to edge instead of leaving gutters."""
    cells = "".join(
        f'<div class="li-metric-cell"><div class="li-metric-label">{label}</div>'
        f'<div class="li-metric-value">{value}</div></div>'
        for label, value in metrics
    )
    return f'<div class="li-metrics-header">{cells}</div>'


def agent_timeline(stages: list) -> str:
    """stages: list of (name, timestamp_str_or_None). All rendered as
    completed steps with a checkmark and a timestamp, in the order
    the pipeline actually runs."""
    items = "".join(
        f'<div class="li-timeline-item"><span>&#10003; {name}</span>'
        f'<span class="li-timeline-stamp">{ts or ""}</span></div>'
        for name, ts in stages
    )
    return f'<div class="li-panel">{items}</div>'


def evidence_item(label: str, source: str, quote: str = None, confidence: float = None) -> str:
    conf_txt = f" &middot; CONFIDENCE {confidence:.2f}" if confidence is not None else ""
    quote_html = f'<div style="color:{COLORS["text_muted"]}; font-size:0.8rem; margin-top:0.2rem;">&ldquo;{quote}&rdquo;</div>' if quote else ""
    return (
        f'<div class="li-evidence-item">'
        f'<div class="li-evidence-meta">{label} &middot; {source}{conf_txt}</div>'
        f'{quote_html}'
        f'</div>'
    )


def grid_open() -> str:
    return '<div class="li-grid">'


def grid_close() -> str:
    return '</div>'
