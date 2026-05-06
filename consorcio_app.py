import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# --- Configuração da Página --- #
st.set_page_config(
    page_title="Trade de Consórcio — Simulador Asset-Light",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funções Auxiliares --- #
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# --- CSS Personalizado --- #
# Salvando o CSS em um arquivo separado para melhor organização
css_content = """
@import url('https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap');
html, body, [class*="css"] { font-family: 'Satoshi', sans-serif !important; }
.main { background: #f7f6f2; }
.stSidebar { background: #1c1b19 !important; }
.stSidebar label, .stSidebar .stMarkdown, .stSidebar p { color: #cdccca !important; }
.stSidebar h2, .stSidebar h3 { color: #4f98a3 !important; }
.kpi-card { background:#fff; border-radius:12px; padding:20px 16px; box-shadow:0 1px 2px rgba(40,37,29,.06),0 4px 12px rgba(40,37,29,.04); border:1px solid rgba(40,37,29,.08); text-align:center; }
.kpi-label { font-size:10px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:#7a7974; margin-bottom:6px; }
.kpi-value { font-size:22px; font-weight:700; color:#28251d; line-height:1.2; }
.kpi-sub { font-size:11px; color:#7a7974; margin-top:4px; }
.kpi-positive { color:#437a22; }
.kpi-negative { color:#a12c7b; }
.kpi-neutral  { color:#01696f; }
.section-header { font-size:17px; font-weight:700; color:#28251d; margin:24px 0 10px; padding-bottom:6px; border-bottom:2px solid #01696f; }
.alert-box { background:#cedcd8; border-left:4px solid #01696f; border-radius:8px; padding:12px 16px; color:#0f3638; font-size:13px; margin:10px 0; }
.warning-box { background:#ddcfc6; border-left:4px solid #964219; border-radius:8px; padding:12px 16px; color:#4b2614; font-size:13px; margin:10px 0; }
"""
with open("style.css", "w") as f:
    f.write(css_content)
local_css("style.css")

# --- Sidebar --- #
with st.sidebar:
    st.markdown("## 🚛 Parâmetros")

    st.markdown("### 1. Cota & Câmbio")
    taxa_cambio_base   = st.number_input("Taxa de Câmbio Base (R$/€)", 1.0, 20.0, 6.20, 0.05)
    valor_carta_brl    = st.number_input("Valor da Carta de Crédito (R$)", 10000, 2000000, 150000, 5000)
    lance_embutido_pct = st.slider("Lance Embutido Máx. (%)", 0.0, 0.50, 0.30, 0.01, format="%.2f")
    lance_alvo_pct     = st.slider("Lance Alvo Histórico (%)", 0.0, 0.80, 0.35, 0.01, format="%.2f")

    st.markdown("### 2. Desembolso Mensal")
    parcela_eur        = st.number_input("Parcela Mensal (€)", 10.0, 5000.0, 150.0, 10.0)
    caixa_paralelo_eur = st.number_input("Aporte Caixa Paralelo (€/mês)", 0.0, 5000.0, 250.0, 10.0)

    st.markdown("### 3. Condições de Saída")
    agio_pct              = st.slider("Ágio de Mercado (% crédito líq.)", 0.0, 0.80, 0.30, 0.01, format="%.2f")
    comissao_broker_pct   = st.slider("Comissão Broker (% carta total)", 0.0, 0.20, 0.05, 0.01, format="%.2f")

    st.markdown("### 4. Stress Cambial")
    stress_rates = st.multiselect("Taxas de Stress (R$/€)", [5.5,6.0,6.5,7.0,7.5,8.0,8.5,9.0,10.0], default=[7.0,8.0,9.0])
    if not stress_rates:
        stress_rates = [7.0, 8.0, 9.0]

    st.markdown("---")
    max_months = st.slider("Horizonte Máximo (meses)", 12, 120, 60)

# --- Core math --- #
lance_embutido_brl         = lance_embutido_pct * valor_carta_brl
lance_alvo_brl             = lance_alvo_pct     * valor_carta_brl
caixa_par_necessario_brl   = max(0.0, lance_alvo_brl - lance_embutido_brl)
caixa_par_necessario_eur   = caixa_par_necessario_brl / taxa_cambio_base

mes_contemplacao = int(np.ceil(caixa_par_necessario_eur / caixa_paralelo_eur)) if caixa_paralelo_eur > 0 else max_months + 1
mes_contemplacao = min(mes_contemplacao, max_months)
contemplado      = mes_contemplacao <= max_months

total_parcelas_eur   = parcela_eur       * mes_contemplacao
total_caixa_par_eur  = caixa_paralelo_eur * mes_contemplacao
total_desembolso_eur = total_parcelas_eur + total_caixa_par_eur
total_desembolso_brl = total_desembolso_eur * taxa_cambio_base

credito_liquido_brl  = valor_carta_brl   - lance_embutido_brl
agio_bruto_brl       = credito_liquido_brl * agio_pct
comissao_broker_brl  = valor_carta_brl     * comissao_broker_pct
lucro_liquido_brl    = agio_bruto_brl      - comissao_broker_brl
lucro_liq_eur_base   = lucro_liquido_brl   / taxa_cambio_base
roi_nominal          = lucro_liquido_brl   / total_desembolso_brl if total_desembolso_brl > 0 else 0

# --- Month-by-month --- #
months, parc_acc, caixa_acc, desp_acc, lance_pct_list = [], [], [], [], []
for m in range(1, max_months + 1):
    months.append(m)
    p = parcela_eur * m
    c = caixa_paralelo_eur * m
    parc_acc.append(p)
    caixa_acc.append(c)
    desp_acc.append(p + c)
    pct = (c * taxa_cambio_base + lance_embutido_brl) / valor_carta_brl * 100
    lance_pct_list.append(pct)

df_sim = pd.DataFrame({
    "Mês": months,
    "Parcelas (€)": parc_acc,
    "Caixa Paralelo (€)": caixa_acc,
    "Desembolso Total (€)": desp_acc,
    "Lance % da Carta": lance_pct_list
})

# --- Header --- #
st.markdown("""<div style='display:flex;align-items:center;gap:14px;margin-bottom:8px'>
  <div style='font-size:34px'>🚛</div>
  <div>
    <div style='font-size:22px;font-weight:700;color:#28251d'>Trade de Consórcio — Simulador Asset-Light</div>
    <div style='font-size:12px;color:#7a7974'>Estratégia Broker / Ágio | Caminhões & Pesados</div>
  </div>
</div>""", unsafe_allow_html=True)

if contemplado:
    st.markdown(f"<div class='alert-box'>✅ <strong>Contemplação prevista no Mês {mes_contemplacao}</strong> — "
                f"Caixa Paralelo acumulado (€ {caixa_par_necessario_eur:,.0f}) + Lance Embutido (€ {lance_embutido_brl/taxa_cambio_base:,.0f}) "
                f"≥ Lance Alvo ({lance_alvo_pct*100:.0f}% da carta = R$ {lance_alvo_brl:,.0f}).</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='warning-box'>⚠️ <strong>Contemplação não atingida</strong> no horizonte de {max_months} meses. "
                "Aumente o Aporte no Caixa Paralelo ou o Horizonte.</div>", unsafe_allow_html=True)

# --- KPIs --- #
st.markdown("<div class='section-header'>📊 Indicadores-Chave</div>", unsafe_allow_html=True)
c1,c2,c3,c4,c5,c6 = st.columns(6)
kpis = [
    (c1, "Mês Contemplação",    f"Mês {mes_contemplacao}",              "",                                              "neutral"),
    (c2, "Desembolso Total",    f"€ {total_desembolso_eur:,.0f}",        f"R$ {total_desembolso_brl:,.0f}",              "neutral"),
    (c3, "Ágio Bruto",          f"R$ {agio_bruto_brl:,.0f}",             f"€ {agio_bruto_brl/taxa_cambio_base:,.0f}",    "positive"),
    (c4, "Comissão Broker",     f"R$ {comissao_broker_brl:,.0f}",        f"€ {comissao_broker_brl/taxa_cambio_base:,.0f}","negative"),
    (c5, "Lucro Líquido",       f"R$ {lucro_liquido_brl:,.0f}",          f"€ {lucro_liq_eur_base:,.0f}",                 "positive" if lucro_liquido_brl >= 0 else "negative"),
    (c6, "ROI Nominal",         f"{roi_nominal*100:.1f}%",               "Lucro / Desembolso",                           "positive" if roi_nominal >= 0 else "negative"),
]
for col, lbl, val, sub, cls in kpis:
    with col:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>{lbl}</div>"
                    f"<div class='kpi-value kpi-{cls}'>{val}</div>"
                    f"<div class='kpi-sub'>{sub}</div></div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- Charts --- #
st.markdown("<div class='section-header'>📈 Evolução Mensal</div>", unsafe_allow_html=True)
fig = make_subplots(rows=1, cols=2,
    subplot_titles=["Desembolso Acumulado (€)", "Progresso do Lance (% da Carta)"],
    horizontal_spacing=0.08)

fig.add_trace(go.Scatter(x=df_sim["Mês"], y=df_sim["Caixa Paralelo (€)"],
    name="Caixa Paralelo", fill="tozeroy",
    line=dict(color="#01696f", width=2), fillcolor="rgba(1,105,111,0.12)"), row=1, col=1)
fig.add_trace(go.Scatter(x=df_sim["Mês"], y=df_sim["Desembolso Total (€)"],
    name="Desembolso Total", fill="tonexty",
    line=dict(color="#964219", width=2), fillcolor="rgba(150,66,25,0.10)"), row=1, col=1)
if contemplado:
    for c in [1,2]:
        fig.add_vline(x=mes_contemplacao, line_dash="dash", line_color="#01696f",
                      annotation_text=f"M{mes_contemplacao}" if c==2 else "",
                      annotation_font_color="#01696f", row=1, col=c)

fig.add_trace(go.Scatter(x=df_sim["Mês"], y=df_sim["Lance % da Carta"],
    name="Lance %", line=dict(color="#da7101", width=2.5),
    fill="tozeroy", fillcolor="rgba(218,113,1,0.10)"), row=1, col=2)
fig.add_hline(y=lance_alvo_pct*100, line_dash="dot", line_color="#a12c7b",
              annotation_text=f"Alvo {lance_alvo_pct*100:.0f}%",
              annotation_position="right", annotation_font_color="#a12c7b", row=1, col=2)
fig.add_hline(y=lance_embutido_pct*100, line_dash="dot", line_color="#006494",
              annotation_text=f"Embutido {lance_embutido_pct*100:.0f}%",
              annotation_position="right", annotation_font_color="#006494", row=1, col=2)

fig.update_layout(height=360, showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
    plot_bgcolor="#ffffff", paper_bgcolor="#f7f6f2",
    font=dict(family="Satoshi, sans-serif", color="#28251d", size=12),
    margin=dict(l=10, r=10, t=40, b=60))
fig.update_xaxes(gridcolor="#dcd9d5", title_text="Mês")
fig.update_yaxes(gridcolor="#dcd9d5")
st.plotly_chart(fig, use_container_width=True)

# --- Waterfall + Exit Table --- #
st.markdown("<div class='section-header'>💰 Cascata de Saída</div>", unsafe_allow_html=True)
cl, cr = st.columns([1.3, 1])

with cl:
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute","relative","total","relative","relative","total"],
        x=["Carta Bruta","(-) Lance\nEmbutido","Crédito\nLíquido",f"(+) Ágio\n{agio_pct*100:.0f}%",
           f"(-) Comissão\nBroker {comissao_broker_pct*100:.0f}%","✅ Lucro\nLíquido"],
        y=[valor_carta_brl, -lance_embutido_brl, 0, agio_bruto_brl, -comissao_broker_brl, 0],
        connector=dict(line=dict(color="#dcd9d5")),
        increasing=dict(marker_color="#437a22"),
        decreasing=dict(marker_color="#a12c7b"),
        totals=dict(marker_color="#01696f"),
        text=[f"R$ {abs(v):,.0f}" if v != 0 else "" for v in [valor_carta_brl,-lance_embutido_brl,0,agio_bruto_brl,-comissao_broker_brl,0]],
        textposition="outside",
    ))
    fig_wf.update_layout(height=340, title="Cascata de Valor (R$)",
        plot_bgcolor="#ffffff", paper_bgcolor="#f7f6f2", showlegend=False,
        font=dict(family="Satoshi, sans-serif", size=11, color="#28251d"),
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(gridcolor="#dcd9d5"))
    st.plotly_chart(fig_wf, use_container_width=True)

with cr:
    st.markdown("<br>", unsafe_allow_html=True)
    df_exit = pd.DataFrame({
        "Item": ["Valor Total da Carta","(-) Lance Embutido","= Crédito Líquido",
                 f"(+) Ágio {agio_pct*100:.0f}%",f"(-) Comissão {comissao_broker_pct*100:.0f}%",
                 "✅ Lucro Líquido","Desembolso Total","📊 ROI Nominal"],
        "R$":  [f"{valor_carta_brl:,.0f}", f"({lance_embutido_brl:,.0f})",
                f"{credito_liquido_brl:,.0f}", f"{agio_bruto_brl:,.0f}",
                f"({comissao_broker_brl:,.0f})", f"{lucro_liquido_brl:,.0f}",
                f"({total_desembolso_brl:,.0f})", f"{roi_nominal*100:.1f}%"],
        "€ (base)": [f"{valor_carta_brl/taxa_cambio_base:,.0f}", f"({lance_embutido_brl/taxa_cambio_base:,.0f})",
                     f"{credito_liquido_brl/taxa_cambio_base:,.0f}", f"{agio_bruto_brl/taxa_cambio_base:,.0f}",
                     f"({comissao_broker_brl/taxa_cambio_base:,.0f})", f"{lucro_liq_eur_base:,.0f}",
                     f"({total_desembolso_eur:,.0f})", f"{roi_nominal*100:.1f}%"]
    })
    st.dataframe(df_exit, use_container_width=True, hide_index=True)

# --- Stress Test --- #
st.markdown("<div class='section-header'>⚠️ Stress Cambial (Repatriação BRL → EUR)</div>", unsafe_allow_html=True)
all_rates = sorted(set([taxa_cambio_base] + [float(r) for r in stress_rates]))
stress_rows = []
for r in all_rates:
    # Recalcular valores em EUR com a nova taxa 'r'
    ll_eur = lucro_liquido_brl / r
    dd_eur = total_desembolso_brl / r
    
    roi_eur = ll_eur / dd_eur if dd_eur > 0 else 0
    delta   = ll_eur - lucro_liq_eur_base
    delta_p = (delta / abs(lucro_liq_eur_base) * 100) if lucro_liq_eur_base != 0 else 0
    
    tag     = "📌 Base" if abs(r - taxa_cambio_base) < 0.01 else "🔴 Stress"
    stress_rows.append({
        "Cenário": tag, "R$/€": f"{r:.2f}",
        "Lucro (€)": f"{ll_eur:,.0f}", "Desembolso (€)": f"{dd_eur:,.0f}",
        "ROI em €": f"{roi_eur*100:.1f}%",
        "Δ vs Base (€)": f"{'▲' if delta>=0 else '▼'} {delta:,.0f}",
        "Erosão (%)": f"{delta_p:+.1f}%"
    })
df_stress = pd.DataFrame(stress_rows)
st.dataframe(df_stress, use_container_width=True, hide_index=True)

# Bar chart stress
rates_chart  = [float(r["R$/€"]) for r in stress_rows]
lucros_chart = [lucro_liquido_brl / r for r in rates_chart]
bar_colors   = ["#01696f" if abs(r - taxa_cambio_base) < 0.01 else ("#a12c7b" if l < 0 else "#964219") for r, l in zip(rates_chart, lucros_chart)]
fig_s = go.Figure(go.Bar(
    x=[f"R${r:.2f}/€" for r in rates_chart], y=lucros_chart,
    marker_color=bar_colors,
    text=[f"€ {v:,.0f}" for v in lucros_chart], textposition="outside"))
fig_s.add_hline(y=0, line_color="#28251d", line_width=1)
fig_s.update_layout(height=260, title="Lucro Líquido em € por Cenário Cambial",
    plot_bgcolor="#ffffff", paper_bgcolor="#f7f6f2", showlegend=False,
    font=dict(family="Satoshi, sans-serif", size=12, color="#28251d"),
    margin=dict(l=10, r=10, t=40, b=10),
    yaxis=dict(gridcolor="#dcd9d5", title="€"), xaxis=dict(gridcolor="#dcd9d5"))
st.plotly_chart(fig_s, use_container_width=True)

# --- Detail table --- #
with st.expander("📋 Fluxo Detalhado Mês a Mês", expanded=False):
    df_d = df_sim.copy()
    df_d["Status"] = df_d["Mês"].apply(
        lambda m: "🎯 CONTEMPLAÇÃO" if m == mes_contemplacao else ("✅ Pós-contemplação" if m > mes_contemplacao else "⏳ Acumulando"))
    df_d["Parcelas (R$)"]      = (df_d["Parcelas (€)"]      * taxa_cambio_base).round(0)
    df_d["Caixa Paralelo (R$)"]= (df_d["Caixa Paralelo (€)"]* taxa_cambio_base).round(0)
    df_d["Desembolso Total (R$)"]= (df_d["Desembolso Total (€)"] * taxa_cambio_base).round(0)
    st.dataframe(df_d[["Mês","Parcelas (€)","Caixa Paralelo (€)","Desembolso Total (€)",
                        "Parcelas (R$)","Caixa Paralelo (R$)","Desembolso Total (R$)",
                        "Lance % da Carta","Status"]].round(1),
                 use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<div style='font-size:11px;color:#7a7974;text-align:center'>"
            "Simulação para fins de planejamento financeiro. Não constitui recomendação de investimento. "
            "Resultados dependem de condições reais de mercado, do grupo de consórcio e da taxa de câmbio na repatriação."
            "</div>", unsafe_allow_html=True)
