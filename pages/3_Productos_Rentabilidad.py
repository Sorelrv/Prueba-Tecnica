"""
Dashboard 3: Productos y Rentabilidad
Saldos por categoría, ingresos estimados, comisiones
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from db_connection import query, GLOBAL_CSS, CHART_COLORS, PLOT_LAYOUT, fmt_monto

st.set_page_config(page_title="Productos y Rentabilidad | FinanzasDB", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>Productos y Rentabilidad</h1>
    <p>Saldos por Categoría · Ingresos Estimados · Comisiones · Ranking</p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    cats    = query("SELECT DISTINCT categoria FROM productos ORDER BY categoria")["categoria"].tolist()
    cat_sel = st.multiselect("Categoría de producto", cats, default=cats)
    segs    = query("SELECT DISTINCT segmento FROM clientes ORDER BY segmento")["segmento"].tolist()
    seg_sel = st.multiselect("Segmento de cliente", segs, default=segs)
    st.markdown("---")
    st.caption("Dashboard 3 / 3 · Productos y Rentabilidad")

# ── FILTROS SQL ────────────────────────────────────────────────────────────────
cat_list = "', '".join(cat_sel) if cat_sel else "''"
seg_list = "', '".join(seg_sel) if seg_sel else "''"
WHERE_P  = f"WHERE p.categoria IN ('{cat_list}') AND c.segmento IN ('{seg_list}')"

# ── KPIs (medidas calculadas) ──────────────────────────────────────────────────
kpis = query(f"""
SELECT
    COUNT(DISTINCT p.producto_id)                              AS productos,
    SUM(ca.saldo_actual)                                       AS saldo_total,
    SUM(ca.saldo_actual * p.tasa_anual / 100)                 AS ingreso_est,
    COALESCE(SUM(t.monto * p.comision / 100),0)              AS comisiones,
    ROUND(AVG(p.tasa_anual),2)                                AS tasa_prom,
    COUNT(DISTINCT ca.cliente_id)                              AS clientes
FROM carteras ca
JOIN productos p  ON ca.producto_id = p.producto_id
JOIN clientes  c  ON ca.cliente_id  = c.cliente_id
LEFT JOIN transacciones t ON t.cliente_id=c.cliente_id AND t.producto_id=p.producto_id
{WHERE_P}
""").iloc[0]

metrics = [
    ("Productos",           f"{int(kpis['productos'])}"),
    ("Saldo Total",         fmt_monto(kpis["saldo_total"])),
    ("Ingreso Est. Anual",  fmt_monto(kpis["ingreso_est"])),
    ("Comisiones",          fmt_monto(kpis["comisiones"])),
    ("Tasa Promedio",       f"{float(kpis['tasa_prom'] or 0):.2f}%"),
    ("Clientes Alcanzados", f"{int(kpis['clientes']):,}"),
]
cols = st.columns(6)
for col, (label, val) in zip(cols, metrics):
    with col:
        st.metric(label=label, value=val)

st.markdown("<br>", unsafe_allow_html=True)

# ── FILA 1: Sunburst + Ranking ─────────────────────────────────────────────────
c1, c2 = st.columns([1, 1.6])

with c1:
    st.markdown('<div class="section-title">Saldo por Categoría y Producto</div>', unsafe_allow_html=True)
    cat_df = query(f"""
    SELECT p.categoria, p.nombre AS producto, SUM(ca.saldo_actual) AS saldo
    FROM carteras ca
    JOIN productos p ON ca.producto_id=p.producto_id
    JOIN clientes  c ON ca.cliente_id=c.cliente_id
    {WHERE_P} GROUP BY p.categoria, p.nombre ORDER BY saldo DESC
    """)
    cat_df["saldo"] = cat_df["saldo"].astype(float)
    fig_sun = px.sunburst(cat_df, path=["categoria","producto"], values="saldo",
                          color="saldo",
                          color_continuous_scale=["#0F1629","#6366F1","#F59E0B"])
    fig_sun.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#F1F5F9", family="Inter"),
                          height=360, margin=dict(l=0,r=0,t=10,b=0),
                          coloraxis_showscale=False)
    fig_sun.update_traces(textfont_color="white", insidetextorientation="radial",
                          marker=dict(line=dict(color="#080B14", width=1.5)))
    st.plotly_chart(fig_sun, use_container_width=True)

with c2:
    st.markdown('<div class="section-title">Ranking por Saldo e Ingreso Estimado</div>', unsafe_allow_html=True)
    rank = query(f"""
    SELECT p.nombre, p.categoria,
           SUM(ca.saldo_actual)                        AS saldo,
           SUM(ca.saldo_actual * p.tasa_anual / 100)   AS ingreso,
           COUNT(DISTINCT ca.cliente_id)               AS clientes
    FROM carteras ca
    JOIN productos p ON ca.producto_id=p.producto_id
    JOIN clientes  c ON ca.cliente_id=c.cliente_id
    {WHERE_P}
    GROUP BY p.producto_id, p.nombre, p.categoria
    ORDER BY saldo DESC
    """)
    rank["saldo"]   = rank["saldo"].astype(float)
    rank["ingreso"] = rank["ingreso"].astype(float)

    fig_rank = go.Figure()
    fig_rank.add_trace(go.Bar(
        y=rank["nombre"], x=rank["saldo"], orientation="h", name="Saldo Total",
        marker_color="rgba(99,102,241,0.75)", marker_line_width=0,
    ))
    fig_rank.add_trace(go.Bar(
        y=rank["nombre"], x=rank["ingreso"], orientation="h", name="Ingreso Est.",
        marker_color="#F59E0B", marker_line_width=0,
    ))
    fig_rank.update_layout(**{**PLOT_LAYOUT, "barmode":"group", "height":360,
        "xaxis": dict(showticklabels=False, showgrid=False, zeroline=False),
        "yaxis": dict(gridcolor="rgba(255,255,255,0.05)", autorange="reversed"),
    })
    st.plotly_chart(fig_rank, use_container_width=True)

# ── INGRESOS Y COMISIONES POR SEGMENTO ────────────────────────────────────────
st.markdown('<div class="section-title">Ingresos Estimados y Comisiones por Segmento</div>', unsafe_allow_html=True)

ing = query(f"""
SELECT c.segmento,
       SUM(ca.saldo_actual * p.tasa_anual / 100)        AS ingreso,
       COALESCE(SUM(t.monto * p.comision / 100),0)     AS comision
FROM carteras ca
JOIN productos p  ON ca.producto_id=p.producto_id
JOIN clientes  c  ON ca.cliente_id=c.cliente_id
LEFT JOIN transacciones t ON t.cliente_id=c.cliente_id AND t.producto_id=p.producto_id
{WHERE_P}
GROUP BY c.segmento ORDER BY ingreso DESC
""")
ing["ingreso"]  = ing["ingreso"].astype(float)
ing["comision"] = ing["comision"].astype(float)

fig_ing = make_subplots(rows=1, cols=2,
                        subplot_titles=("Ingreso Estimado Anual ($)","Comisiones Generadas ($)"))
for i, col_name in enumerate(["ingreso","comision"]):
    fig_ing.add_trace(go.Bar(
        x=ing["segmento"], y=ing[col_name],
        marker_color=CHART_COLORS[:len(ing)], marker_line_width=0,
        name=col_name,
        text=[fmt_monto(v) for v in ing[col_name]],
        textposition="outside", textfont=dict(color="white", size=11),
    ), row=1, col=i+1)
fig_ing.update_layout(**{**PLOT_LAYOUT, "showlegend":False, "height":280,
    "margin": dict(l=4, r=4, t=45, b=4),
})
fig_ing.update_annotations(font_color="rgba(241,245,249,0.7)", font_size=12)
st.plotly_chart(fig_ing, use_container_width=True)

# ── TABLA DETALLE ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Detalle por Producto</div>', unsafe_allow_html=True)
tabla = query(f"""
SELECT p.nombre, p.categoria,
       p.tasa_anual, p.comision,
       COUNT(DISTINCT ca.cliente_id)                        AS clientes,
       SUM(ca.saldo_actual)                                 AS saldo_total,
       ROUND(SUM(ca.saldo_actual * p.tasa_anual / 100),0)  AS ingreso_anual,
       ROUND(AVG(ca.saldo_actual),0)                        AS saldo_prom
FROM carteras ca
JOIN productos p ON ca.producto_id=p.producto_id
JOIN clientes  c ON ca.cliente_id=c.cliente_id
{WHERE_P}
GROUP BY p.producto_id, p.nombre, p.categoria, p.tasa_anual, p.comision
ORDER BY saldo_total DESC
""")
tabla["saldo_total"]  = tabla["saldo_total"].astype(float).map(lambda x: f"${x:,.0f}")
tabla["ingreso_anual"]= tabla["ingreso_anual"].astype(float).map(lambda x: f"${x:,.0f}")
tabla["saldo_prom"]   = tabla["saldo_prom"].astype(float).map(lambda x: f"${x:,.0f}")
tabla["tasa_anual"]   = tabla["tasa_anual"].astype(float).map(lambda x: f"{x:.2f}%")
tabla["comision"]     = tabla["comision"].astype(float).map(lambda x: f"{x:.2f}%")
tabla.columns = ["Producto","Categoría","Tasa Anual","Comisión","Clientes",
                 "Saldo Total","Ingreso Est. Anual","Saldo Promedio"]
st.dataframe(tabla, use_container_width=True, hide_index=True)
