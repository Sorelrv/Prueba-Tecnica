"""
Dashboard 2: Análisis de Clientes
Segmentación, distribución geográfica, antigüedad
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from db_connection import query, GLOBAL_CSS, CHART_COLORS, PLOT_LAYOUT, fmt_monto

st.set_page_config(page_title="Análisis de Clientes | FinanzasDB", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>Análisis de Clientes</h1>
    <p>Segmentación · Distribución Geográfica · Antigüedad · Estado</p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    segs     = query("SELECT DISTINCT segmento FROM clientes ORDER BY segmento")["segmento"].tolist()
    seg_sel  = st.multiselect("Segmento", segs, default=segs)
    ciudades = query("SELECT DISTINCT ciudad FROM clientes ORDER BY ciudad")["ciudad"].tolist()
    ciudad   = st.selectbox("Ciudad", ["Todas"] + ciudades)
    solo_act = st.toggle("Solo clientes activos", value=False)
    st.markdown("---")
    st.caption("Dashboard 2 / 3 · Análisis de Clientes")

# ── FILTROS SQL ────────────────────────────────────────────────────────────────
seg_list  = "', '".join(seg_sel) if seg_sel else "''"
WHERE_CLI = f"WHERE c.segmento IN ('{seg_list}')"
if ciudad != "Todas":
    WHERE_CLI += f" AND c.ciudad = '{ciudad}'"
if solo_act:
    WHERE_CLI += " AND c.activo = TRUE"

# ── KPIs ───────────────────────────────────────────────────────────────────────
kpis = query(f"""
SELECT
    COUNT(*)                                                      AS total,
    SUM(CASE WHEN activo THEN 1 ELSE 0 END)                      AS activos,
    ROUND(AVG(EXTRACT(YEAR FROM AGE(NOW(), fecha_alta))),1)       AS antiguedad,
    COUNT(DISTINCT ciudad)                                         AS ciudades
FROM clientes c {WHERE_CLI}
""").iloc[0]

saldo_prom = query(f"""
SELECT ROUND(AVG(ca.saldo_actual),0) AS sp
FROM carteras ca JOIN clientes c ON ca.cliente_id=c.cliente_id {WHERE_CLI}
""").iloc[0]["sp"]

def _i(v): return int(v)   if v is not None else 0
def _f(v): return float(v) if v is not None else 0.0

metrics = [
    ("Total Clientes",      f"{_i(kpis['total']):,}"),
    ("Clientes Activos",    f"{_i(kpis['activos']):,}"),
    ("Antigüedad Prom.",    f"{_f(kpis['antiguedad']):.1f} años"),
    ("Ciudades Cubiertas",  f"{_i(kpis['ciudades'])}"),
    ("Saldo Prom. Cartera", fmt_monto(saldo_prom)),
]
cols = st.columns(5)
for col, (label, val) in zip(cols, metrics):
    with col:
        st.metric(label=label, value=val)

st.markdown("<br>", unsafe_allow_html=True)

# ── FILA 1: Saldo por segmento + Clientes por ciudad ──────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="section-title">Saldo Total por Segmento</div>', unsafe_allow_html=True)
    seg_dist = query(f"""
    SELECT c.segmento, COUNT(*) AS clientes, SUM(ca.saldo_actual) AS saldo
    FROM clientes c LEFT JOIN carteras ca ON ca.cliente_id=c.cliente_id
    {WHERE_CLI} GROUP BY c.segmento ORDER BY saldo DESC
    """)
    seg_dist["saldo"] = seg_dist["saldo"].astype(float)
    fig_seg = px.bar(seg_dist, x="segmento", y="saldo", color="segmento",
                     text=seg_dist["clientes"].astype(str) + " cli.",
                     color_discrete_sequence=CHART_COLORS)
    fig_seg.update_traces(textposition="outside", textfont_color="white",
                          marker_line_width=0, textfont_size=11)
    fig_seg.update_layout(**{**PLOT_LAYOUT, "height":300, "showlegend":False,
        "yaxis": dict(gridcolor="rgba(255,255,255,0.05)", title="Saldo Total ($)"),
        "xaxis": dict(title=""),
    })
    st.plotly_chart(fig_seg, use_container_width=True)

with c2:
    st.markdown('<div class="section-title">Distribución por Ciudad</div>', unsafe_allow_html=True)
    ciudad_df = query(f"""
    SELECT c.ciudad, COUNT(*) AS clientes, COALESCE(SUM(ca.saldo_actual),0) AS saldo
    FROM clientes c LEFT JOIN carteras ca ON ca.cliente_id=c.cliente_id
    {WHERE_CLI} GROUP BY c.ciudad ORDER BY clientes DESC
    """)
    ciudad_df["saldo"] = ciudad_df["saldo"].astype(float)
    fig_ciudad = px.treemap(ciudad_df, path=["ciudad"], values="clientes",
                            color="saldo",
                            color_continuous_scale=["#0F1629","#6366F1","#F59E0B"])
    fig_ciudad.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F1F5F9", family="Inter"),
        height=300, margin=dict(l=0, r=0, t=20, b=0),
        coloraxis_showscale=False,
    )
    fig_ciudad.update_traces(textfont_color="white", textfont_size=13)
    st.plotly_chart(fig_ciudad, use_container_width=True)

# ── FILA 2: Cohorte + Estado ───────────────────────────────────────────────────
c3, c4 = st.columns([1.7, 1])

with c3:
    st.markdown('<div class="section-title">Clientes Nuevos por Año (Cohorte)</div>', unsafe_allow_html=True)
    cohorte = query(f"""
    SELECT EXTRACT(YEAR FROM c.fecha_alta)::int AS anio,
           c.segmento, COUNT(*) AS nuevos
    FROM clientes c {WHERE_CLI}
    GROUP BY 1,2 ORDER BY 1
    """)
    cohorte["nuevos"] = cohorte["nuevos"].astype(int)
    fig_coh = px.bar(cohorte, x="anio", y="nuevos", color="segmento",
                     barmode="group", color_discrete_sequence=CHART_COLORS)
    fig_coh.update_layout(**{**PLOT_LAYOUT, "height":290,
        "xaxis": dict(gridcolor="rgba(255,255,255,0.05)", title="Año de Alta", dtick=1),
        "yaxis": dict(gridcolor="rgba(255,255,255,0.05)", title="Nuevos Clientes"),
    })
    fig_coh.update_traces(marker_line_width=0)
    st.plotly_chart(fig_coh, use_container_width=True)

with c4:
    st.markdown('<div class="section-title">Estado de Clientes</div>', unsafe_allow_html=True)
    act_df = query(f"""
    SELECT CASE WHEN activo THEN 'Activo' ELSE 'Inactivo' END AS estado,
           COUNT(*) AS total
    FROM clientes c {WHERE_CLI} GROUP BY activo
    """)
    act_df["total"] = act_df["total"].astype(int)
    fig_act = px.pie(act_df, names="estado", values="total",
                     color_discrete_sequence=["#F59E0B","#1E2540"], hole=0.62)
    fig_act.update_traces(textinfo="percent+label", textfont_color="white",
                          marker=dict(line=dict(color="#080B14", width=2)))
    fig_act.update_layout(**{**PLOT_LAYOUT, "height":290, "showlegend":True})
    st.plotly_chart(fig_act, use_container_width=True)

# ── TABLA DETALLE ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Detalle de Clientes</div>', unsafe_allow_html=True)
det = query(f"""
SELECT c.nombre, c.segmento, c.ciudad,
       c.fecha_alta,
       CASE WHEN c.activo THEN 'Activo' ELSE 'Inactivo' END AS estado,
       COUNT(DISTINCT ca.producto_id)   AS productos,
       COALESCE(SUM(ca.saldo_actual),0) AS saldo_total,
       COUNT(t.transaccion_id)          AS transacciones
FROM clientes c
LEFT JOIN carteras      ca ON ca.cliente_id = c.cliente_id
LEFT JOIN transacciones t  ON t.cliente_id  = c.cliente_id
{WHERE_CLI}
GROUP BY c.cliente_id, c.nombre, c.segmento, c.ciudad, c.fecha_alta, c.activo
ORDER BY saldo_total DESC
""")
det["saldo_total"] = det["saldo_total"].astype(float).map(lambda x: f"${x:,.0f}")
det.columns = ["Nombre","Segmento","Ciudad","Fecha Alta","Estado","Productos","Saldo Total","Transacciones"]
st.dataframe(det, use_container_width=True, hide_index=True)
