"""
🏦 Portal Principal — FinanzasDB
"""
import streamlit as st
from db_connection import query, GLOBAL_CSS, fmt_monto

st.set_page_config(
    page_title="FinanzasDB · Dashboard Ejecutivo",
    layout="wide",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.hero {
    text-align: center;
    padding: 3.5rem 1rem 2rem;
}
.hero-badge {
    display: inline-block;
    background: rgba(245,158,11,.12);
    border: 1px solid rgba(245,158,11,.3);
    color: #F59E0B;
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    padding: .35rem 1.1rem;
    border-radius: 99px;
    margin-bottom: 1.2rem;
}
.hero h1 {
    font-size: 3.2rem;
    font-weight: 900;
    color: #F1F5F9;
    margin: 0 0 .6rem;
    line-height: 1.1;
}
.hero h1 span { color: #F59E0B; }
.hero p {
    color: rgba(241,245,249,.5);
    font-size: 1.05rem;
    max-width: 520px;
    margin: 0 auto 2.2rem;
    line-height: 1.6;
}
.pill {
    display: inline-block;
    background: rgba(99,102,241,.15);
    border: 1px solid rgba(99,102,241,.3);
    color: #818CF8;
    padding: .3rem .85rem;
    border-radius: 99px;
    font-size: .75rem;
    font-weight: 600;
    margin: .2rem;
}
.stat-strip {
    display: flex;
    justify-content: center;
    gap: 0;
    margin: 2.5rem 0;
    background: #0F1629;
    border: 1px solid rgba(245,158,11,.18);
    border-radius: 16px;
    overflow: hidden;
}
.stat-item {
    flex: 1;
    padding: 1.4rem 1rem;
    text-align: center;
    border-right: 1px solid rgba(245,158,11,.1);
}
.stat-item:last-child { border-right: none; }
.stat-val { font-size: 2rem; font-weight: 800; color: #F59E0B; }
.stat-lbl { font-size: .72rem; font-weight: 600; letter-spacing: .08em;
             text-transform: uppercase; color: rgba(241,245,249,.4); margin-top:.25rem; }

.nav-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.2rem;
    margin: 1.5rem 0;
}
.nav-card {
    background: #0F1629;
    border: 1px solid rgba(245,158,11,.18);
    border-radius: 16px;
    padding: 2rem 1.5rem;
    transition: transform .22s, border-color .22s, box-shadow .22s;
    cursor: pointer;
}
.nav-card:hover {
    transform: translateY(-5px);
    border-color: #F59E0B;
    box-shadow: 0 16px 48px rgba(245,158,11,.15);
}
.nav-icon    { font-size: 2.8rem; margin-bottom: .8rem; }
.nav-card h3 { color: #F1F5F9; font-size: 1.1rem; font-weight: 700; margin: 0 0 .5rem; }
.nav-card p  { color: rgba(241,245,249,.5); font-size: .83rem; line-height: 1.55; margin: 0; }
.nav-badge   {
    display: inline-block;
    margin-top: 1.1rem;
    background: rgba(245,158,11,.12);
    border: 1px solid rgba(245,158,11,.3);
    color: #F59E0B;
    font-size: .72rem; font-weight: 700;
    padding: .3rem .85rem; border-radius: 99px;
}
.footer {
    text-align: center;
    color: rgba(241,245,249,.2);
    font-size: .75rem;
    padding: 2rem 0 .5rem;
}
</style>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">Dashboard Ejecutivo · PostgreSQL en Vivo</div>
    <h1>Finanzas<span>DB</span></h1>
    <p>Análisis financiero profesional construido con Python. Datos reales, gráficos interactivos y filtros dinámicos.</p>
    <div>
        <span class="pill">Python</span>
        <span class="pill">Streamlit</span>
        <span class="pill">PostgreSQL</span>
        <span class="pill">Plotly</span>
        <span class="pill">Pandas</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── ESTADÍSTICAS RÁPIDAS ──────────────────────────────────────────────────────
stats = query("""
    SELECT
        (SELECT COUNT(*)            FROM clientes)      AS clientes,
        (SELECT COUNT(*)            FROM transacciones)  AS transacciones,
        (SELECT SUM(saldo_actual)   FROM carteras)       AS saldo_total,
        (SELECT COUNT(*)            FROM productos)      AS productos,
        (SELECT COUNT(DISTINCT estado) FROM transacciones) AS estados
""").iloc[0]

st.markdown(f"""
<div class="stat-strip">
    <div class="stat-item">
        <div class="stat-val">{int(stats['clientes']):,}</div>
        <div class="stat-lbl">Clientes</div>
    </div>
    <div class="stat-item">
        <div class="stat-val">{int(stats['transacciones']):,}</div>
        <div class="stat-lbl">Transacciones</div>
    </div>
    <div class="stat-item">
        <div class="stat-val">{fmt_monto(stats['saldo_total'])}</div>
        <div class="stat-lbl">Saldo Total</div>
    </div>
    <div class="stat-item">
        <div class="stat-val">{int(stats['productos'])}</div>
        <div class="stat-lbl">Productos</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── CARDS DE NAVEGACIÓN ────────────────────────────────────────────────────────
st.markdown("""
<div class="nav-grid">
    <div class="nav-card">
        <div class="nav-icon"> </div>
        <h3>Resumen Ejecutivo</h3>
        <p>KPIs clave, evolución temporal de transacciones, top 10 clientes y distribución por tipo.</p>
        <span class="nav-badge">Página 1 →</span>
    </div>
    <div class="nav-card">
        <div class="nav-icon"> </div>
        <h3>Análisis de Clientes</h3>
        <p>Segmentación por categoría, distribución por ciudad, cohortes de antigüedad y actividad.</p>
        <span class="nav-badge">Página 2 →</span>
    </div>
    <div class="nav-card">
        <div class="nav-icon"> </div>
        <h3>Productos y Rentabilidad</h3>
        <p>Saldos por categoría, ingresos estimados por tasa anual, comisiones y ranking de productos.</p>
        <span class="nav-badge">Página 3 →</span>
    </div>
</div>

<div class="footer">
    FinanzasDB · Analista de Datos
</div>
""", unsafe_allow_html=True)
