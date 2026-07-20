# db_connection.py - Módulo de conexión compartido
import pg8000
import pandas as pd
import streamlit as st

DB_CONFIG = {
    "user": "postgres",
    "host": "localhost",
    "port": 5432,
    "database": "DB_Finanzasdb",
    "password": "sorel",
}

# ── Paleta y estilos globales ──────────────────────────────────────────────────
COLORS = {
    "bg":        "#080B14",
    "surface":   "#0F1629",
    "border":    "rgba(245, 158, 11, 0.18)",
    "amber":     "#F59E0B",
    "amber_dim": "#FBBF24",
    "indigo":    "#6366F1",
    "indigo_dim":"#818CF8",
    "green":     "#34D399",
    "red":       "#F87171",
    "text":      "#F1F5F9",
    "muted":     "rgba(241, 245, 249, 0.45)",
}

# Secuencia de colores para gráficos (siempre la misma en todos los dashboards)
CHART_COLORS = ["#F59E0B", "#6366F1", "#34D399", "#FBBF24", "#818CF8", "#F87171"]

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#F1F5F9", family="Inter, sans-serif"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#F1F5F9")),
    margin=dict(l=4, r=4, t=20, b=4),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.08)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.08)"),
)

# CSS global reutilizable
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif !important; }
.stApp                       { background: #080B14 !important; }
.block-container             { padding-top: 1.5rem !important; }

/* Sidebar */
[data-testid="stSidebar"]        { background: #0A0D1A !important; border-right: 1px solid rgba(245,158,11,.15) !important; }
[data-testid="stSidebar"] label  { color: rgba(241,245,249,.65) !important; font-size:.78rem !important; letter-spacing:.06em !important; text-transform:uppercase !important; }
[data-testid="stSidebar"] *      { color: #F1F5F9 !important; }

/* Selectbox / multiselect */
[data-baseweb="select"] > div   { background:#0F1629 !important; border-color: rgba(245,158,11,.25) !important; color:#F1F5F9 !important; }
[data-baseweb="tag"]            { background:#1E2540 !important; }

/* Dataframe */
[data-testid="stDataFrame"] > div { border: 1px solid rgba(245,158,11,.15) !important; border-radius:12px !important; }
thead tr th { background: #0F1629 !important; color: #F59E0B !important; font-weight:700 !important; }
tbody tr:nth-child(even) td { background: rgba(99,102,241,.06) !important; }
tbody tr td { color: #F1F5F9 !important; }

/* Toggle */
[data-testid="stToggle"] { accent-color: #F59E0B; }

/* Header bar */
.main-header {
    background: linear-gradient(120deg, #0F1629 0%, #1a1f3d 100%);
    border: 1px solid rgba(245,158,11,.25);
    border-left: 4px solid #F59E0B;
    padding: 1.5rem 2rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
}
.main-header h1 { color:#F1F5F9; font-size:1.9rem; font-weight:900; margin:0; }
.main-header p  { color:rgba(241,245,249,.55); margin:.25rem 0 0; font-size:.9rem; }

/* KPI card */
.kpi-card {
    background: #0F1629;
    border: 1px solid rgba(245,158,11,.18);
    border-radius: 14px;
    padding: 1.3rem 1.2rem;
    text-align: center;
    transition: transform .2s, border-color .2s, box-shadow .2s;
    height: 100%;
}
.kpi-card:hover { transform:translateY(-3px); border-color:rgba(245,158,11,.55); box-shadow:0 8px 28px rgba(245,158,11,.12); }
.kpi-icon  { font-size:1.5rem; margin-bottom:.4rem; }
.kpi-label { color:rgba(241,245,249,.5); font-size:.7rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.35rem; }
.kpi-value { color:#F1F5F9; font-size:1.85rem; font-weight:800; line-height:1; }

/* Section title */
.section-title {
    color:#F1F5F9; font-size:1rem; font-weight:700;
    margin:1.4rem 0 .7rem; padding-left:.7rem;
    border-left:3px solid #F59E0B;
}

/* Divider */
hr { border-color: rgba(245,158,11,.12) !important; }
</style>
"""

def get_connection():
    return pg8000.connect(**DB_CONFIG)

@st.cache_data(ttl=300)
def query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()

def fmt_monto(v):
    """Formatea montos en M/K con símbolo $."""
    if v is None: return "–"
    v = float(v)
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:     return f"${v/1_000:.0f}K"
    return f"${v:.0f}"


# ── CSS para st.metric (reemplaza kpi_card HTML) ──────────────────────────────
_METRIC_CSS = """
    /* KPI cards via st.metric */
    [data-testid="stMetric"] {
        background: #0F1629 !important;
        border: 1px solid rgba(245,158,11,.2) !important;
        border-radius: 14px !important;
        padding: 1.2rem 1rem !important;
        transition: transform .2s, border-color .2s, box-shadow .2s;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px) !important;
        border-color: rgba(245,158,11,.55) !important;
        box-shadow: 0 8px 28px rgba(245,158,11,.1) !important;
    }
    [data-testid="stMetricLabel"] > div {
        color: rgba(241,245,249,.5) !important;
        font-size: .7rem !important;
        font-weight: 700 !important;
        letter-spacing: .1em !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricValue"] > div {
        color: #F1F5F9 !important;
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
    }
    [data-testid="stMetricDelta"]  { display: none !important; }
"""

GLOBAL_CSS = GLOBAL_CSS.replace("</style>", _METRIC_CSS + "\n</style>")

def kpi_card(icon: str, label: str, value: str):
    """Kept for backwards compatibility — no longer used."""
    icon_html = f'<div class="kpi-icon">{icon}</div>' if icon else ""
    return f"""<div class="kpi-card">{icon_html}
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div></div>"""
