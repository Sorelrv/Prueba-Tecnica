"""
Dashboard 1: Resumen Ejecutivo
KPIs clave, tendencia de transacciones, top clientes
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from db_connection import query, GLOBAL_CSS, CHART_COLORS, PLOT_LAYOUT, fmt_monto

st.set_page_config(page_title="Resumen Ejecutivo | FinanzasDB", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>Resumen Ejecutivo</h1>
    <p>Visión 360° · Tendencias · KPIs · Top Clientes</p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    fechas_df = query("SELECT MIN(fecha) AS mn, MAX(fecha) AS mx FROM transacciones")
    min_f = pd.to_datetime(fechas_df["mn"][0])
    max_f = pd.to_datetime(fechas_df["mx"][0])
    fecha_inicio, fecha_fin = st.date_input("Período", value=(min_f, max_f),
                                            min_value=min_f, max_value=max_f)
    segs   = query("SELECT DISTINCT segmento FROM clientes ORDER BY segmento")["segmento"].tolist()
    seg    = st.selectbox("Segmento", ["Todos"] + segs)
    estats = query("SELECT DISTINCT estado FROM transacciones ORDER BY estado")["estado"].tolist()
    estat  = st.selectbox("Estado", ["Todos"] + estats)
    st.markdown("---")
    st.caption("Dashboard 1 / 3 · Resumen Ejecutivo")

# ── FILTROS SQL ────────────────────────────────────────────────────────────────
w_fecha = f"t.fecha BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
w_seg   = f" AND c.segmento = '{seg}'"   if seg   != "Todos" else ""
w_est   = f" AND t.estado   = '{estat}'" if estat  != "Todos" else ""
WHERE   = f"WHERE {w_fecha}{w_seg}{w_est}"

# ── KPIs ───────────────────────────────────────────────────────────────────────
kpis = query(f"""
SELECT
    COUNT(t.transaccion_id)                                          AS txs,
    SUM(t.monto)                                                     AS vol,
    AVG(t.monto)                                                     AS ticket,
    COUNT(DISTINCT t.cliente_id)                                     AS clientes,
    ROUND(100.0 * SUM(CASE WHEN t.estado='Completada' THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*),0),1)                                    AS pct_ok,
    (SELECT SUM(saldo_actual) FROM carteras)                         AS saldo_carteras
FROM transacciones t
JOIN clientes c ON t.cliente_id = c.cliente_id
{WHERE}
""").iloc[0]

def _i(v): return int(v) if v is not None else 0
def _f(v): return float(v) if v is not None else 0.0

metrics = [
    ("Transacciones",   f"{_i(kpis['txs']):,}"),
    ("Volumen Total",   fmt_monto(kpis["vol"])),
    ("Ticket Promedio", fmt_monto(kpis["ticket"])),
    ("Clientes Activos",f"{_i(kpis['clientes']):,}"),
    ("% Completadas",   f"{_f(kpis['pct_ok']):.1f}%"),
    ("Saldo Carteras",  fmt_monto(kpis["saldo_carteras"])),
]
cols = st.columns(6)
for col, (label, val) in zip(cols, metrics):
    with col:
        st.metric(label=label, value=val)

st.markdown("<br>", unsafe_allow_html=True)

# ── EVOLUCIÓN TEMPORAL ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Evolución Mensual de Transacciones</div>', unsafe_allow_html=True)

evol = query(f"""
SELECT DATE_TRUNC('month', t.fecha) AS mes,
       SUM(t.monto)                  AS volumen,
       COUNT(*)                       AS cantidad
FROM transacciones t
JOIN clientes c ON t.cliente_id = c.cliente_id
{WHERE}
GROUP BY 1 ORDER BY 1
""")
evol["mes"]     = pd.to_datetime(evol["mes"])
evol["volumen"] = evol["volumen"].astype(float)

fig_evol = make_subplots(specs=[[{"secondary_y": True}]])
fig_evol.add_trace(go.Scatter(
    x=evol["mes"], y=evol["volumen"], name="Volumen ($)",
    fill="tozeroy", line=dict(color="#F59E0B", width=2.5),
    fillcolor="rgba(245,158,11,0.12)"
), secondary_y=False)
fig_evol.add_trace(go.Bar(
    x=evol["mes"], y=evol["cantidad"].astype(int),
    name="Cantidad", marker_color="rgba(99,102,241,0.5)", marker_line_width=0
), secondary_y=True)
fig_evol.update_layout(**{**PLOT_LAYOUT, "height": 300,
    "yaxis":  dict(gridcolor="rgba(255,255,255,0.05)", title=dict(text="Volumen ($)",  font=dict(color="#F59E0B"))),
    "yaxis2": dict(gridcolor="rgba(0,0,0,0)",          title=dict(text="Cantidad",     font=dict(color="#6366F1")), overlaying="y", side="right"),
})
st.plotly_chart(fig_evol, use_container_width=True)

# ── TIPO + TOP CLIENTES ────────────────────────────────────────────────────────
c1, c2 = st.columns([1, 1.7])

with c1:
    st.markdown('<div class="section-title">Distribución por Tipo</div>', unsafe_allow_html=True)
    tipo_df = query(f"""
    SELECT t.tipo, SUM(t.monto) AS total
    FROM transacciones t JOIN clientes c ON t.cliente_id=c.cliente_id
    {WHERE} GROUP BY t.tipo ORDER BY total DESC
    """)
    tipo_df["total"] = tipo_df["total"].astype(float)
    fig_tipo = px.pie(tipo_df, names="tipo", values="total",
                      color_discrete_sequence=CHART_COLORS, hole=0.58)
    fig_tipo.update_traces(textinfo="percent+label", textfont_color="white",
                           marker=dict(line=dict(color="#080B14", width=2)))
    fig_tipo.update_layout(**{**PLOT_LAYOUT, "height": 300, "showlegend": True})
    st.plotly_chart(fig_tipo, use_container_width=True)

with c2:
    st.markdown('<div class="section-title">Top 10 Clientes por Volumen</div>', unsafe_allow_html=True)
    top = query(f"""
    SELECT c.nombre, c.segmento, SUM(t.monto) AS vol
    FROM transacciones t JOIN clientes c ON t.cliente_id=c.cliente_id
    {WHERE} GROUP BY c.nombre, c.segmento ORDER BY vol DESC LIMIT 10
    """)
    top["vol"] = top["vol"].astype(float)
    seg_color  = {"Premium":"#F59E0B","Standard":"#6366F1","Básico":"#34D399","B\u00e1sico":"#34D399"}
    top["color"] = top["segmento"].map(seg_color).fillna("#94A3B8")
    fig_top = go.Figure(go.Bar(
        y=top["nombre"], x=top["vol"], orientation="h",
        marker_color=top["color"].tolist(), marker_line_width=0,
        text=[fmt_monto(v) for v in top["vol"]],
        textposition="inside", textfont=dict(color="#080B14", size=11, weight=700)
    ))
    fig_top.update_layout(**{**PLOT_LAYOUT, "height": 310,
        "xaxis": dict(showgrid=False, showticklabels=False, zeroline=False),
        "yaxis": dict(gridcolor="rgba(255,255,255,0.05)", autorange="reversed"),
    })
    st.plotly_chart(fig_top, use_container_width=True)

# ── TABLA RESUMEN POR SEGMENTO ─────────────────────────────────────────────────
st.markdown('<div class="section-title">Resumen por Segmento</div>', unsafe_allow_html=True)
seg_df = query(f"""
SELECT c.segmento,
       COUNT(DISTINCT t.cliente_id)                                    AS clientes,
       COUNT(*)                                                         AS transacciones,
       SUM(t.monto)                                                     AS volumen,
       AVG(t.monto)                                                     AS ticket,
       ROUND(100.0*SUM(CASE WHEN t.estado='Completada' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),1) AS pct
FROM transacciones t JOIN clientes c ON t.cliente_id=c.cliente_id
{WHERE} GROUP BY c.segmento ORDER BY volumen DESC
""")
seg_df["volumen"] = seg_df["volumen"].astype(float).map(lambda x: f"${x:,.0f}")
seg_df["ticket"]  = seg_df["ticket"].astype(float).map(lambda x: f"${x:,.0f}")
seg_df["pct"]     = seg_df["pct"].astype(float).map(lambda x: f"{x:.1f}%")
seg_df.columns    = ["Segmento","Clientes","Transacciones","Volumen","Ticket Prom.","% Completadas"]
st.dataframe(seg_df, use_container_width=True, hide_index=True)
