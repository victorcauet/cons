import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# --- Configuration & Theme Engine ---
st.set_page_config(
    page_title="Consortium Strategy | Private Equity Simulator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Design System Constants
COLORS = {
    "bg_main": "#F5F5F7",
    "bg_card": "#FFFFFF",
    "navy": "#002147",
    "gold": "#AF9500",
    "text_primary": "#1D1D1F",
    "text_secondary": "#86868B",
    "success": "#34C759",
    "error": "#FF3B30",
    "border": "rgba(0,0,0,0.05)",
    "shadow": "0 8px 30px rgba(0,0,0,0.04)"
}

FONTS = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

def apply_apple_theme(fig):
    fig.update_layout(
        font=dict(family=FONTS, size=12, color=COLORS["text_primary"]),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family=FONTS),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color=COLORS["text_secondary"])
        )
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.03)', zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.03)', zeroline=False)
    return fig

# --- CSS Injection ---
css_content = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {{ background-color: {COLORS["bg_main"]}; }}
html, body, [class*="css"] {{ font-family: {FONTS} !important; color: {COLORS["text_primary"]}; }}

[data-testid="stSidebar"] {{ background-color: #FFFFFF !important; border-right: 1px solid {COLORS["border"]}; }}
[data-testid="stSidebar"] .stMarkdown h2 {{ font-size: 1.2rem; font-weight: 700; color: {COLORS["navy"]} !important; }}

.kpi-card {{
    background: {COLORS["bg_card"]};
    border-radius: 18px;
    padding: 24px;
    box-shadow: {COLORS["shadow"]};
    border: 1px solid {COLORS["border"]};
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
}}
.kpi-card:hover {{ transform: translateY(-5px); box-shadow: 0 12px 40px rgba(0,0,0,0.08); }}
.kpi-label {{ font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: {COLORS["text_secondary"]}; margin-bottom: 12px; }}
.kpi-value {{ font-size: 26px; font-weight: 700; color: {COLORS["navy"]}; line-height: 1.1; }}
.kpi-sub {{ font-size: 13px; color: {COLORS["text_secondary"]}; margin-top: 6px; }}

.status-banner {{ padding: 16px 24px; border-radius: 14px; margin-bottom: 32px; font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 12px; }}
.status-success {{ background-color: rgba(52, 199, 89, 0.08); color: #248a3d; border: 1px solid rgba(52, 199, 89, 0.15); }}
.status-warning {{ background-color: rgba(255, 59, 48, 0.08); color: #d70015; border: 1px solid rgba(255, 59, 48, 0.15); }}

.section-title {{ font-size: 20px; font-weight: 600; color: {COLORS["navy"]}; margin: 48px 0 24px; padding-left: 12px; border-left: 4px solid {COLORS["gold"]}; }}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
"""
st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

# --- Sidebar Inputs ---
with st.sidebar:
    st.markdown("## ⚙️ Parâmetros Analíticos")
    
    with st.expander("🏦 Capital & Câmbio", expanded=True):
        taxa_cambio_base   = st.number_input("Câmbio Base (R$/€)", 1.0, 20.0, 6.20, 0.05)
        valor_carta_brl    = st.number_input("Carta de Crédito (R$)", 10000, 5000000, 150000, 5000)
        lance_embutido_pct = st.slider("Lance Embutido (%)", 0.0, 0.50, 0.30, 0.01, format="%.2f")
        lance_alvo_pct     = st.slider("Lance Alvo Histórico (%)", 0.0, 0.80, 0.35, 0.01, format="%.2f")

    with st.expander("💸 Fluxo Mensal", expanded=True):
        parcela_eur        = st.number_input("Parcela Mensal (€)", 10.0, 10000.0, 150.0, 10.0)
        caixa_paralelo_eur = st.number_input("Aporte Adicional (€/mês)", 0.0, 10000.0, 250.0, 10.0)

    with st.expander("📈 Estratégia de Saída", expanded=True):
        agio_pct              = st.slider("Ágio de Mercado (%)", 0.0, 0.80, 0.30, 0.01, format="%.2f")
        comissao_broker_pct   = st.slider("Comissão de Intermediação (%)", 0.0, 0.20, 0.05, 0.01, format="%.2f")

    with st.expander("🎲 Monte Carlo (Risco de Grupo)", expanded=True):
        volatilidade_lance = st.slider("Volatilidade do Lance (%)", 0.0, 0.20, 0.05, 0.01, help="Variação esperada na concorrência do grupo.")
        n_simulacoes = 5000

    with st.expander("🛡️ Stress Cambial", expanded=False):
        stress_rates = st.multiselect("Taxas de Stress (R$/€)", [5.5,6.0,6.5,7.0,7.5,8.0,8.5,9.0,10.0], default=[7.0,8.0,9.0])
        if not stress_rates: stress_rates = [7.0, 8.0, 9.0]
        max_months = st.slider("Horizonte Máximo (meses)", 12, 120, 60)

# --- Core Logic & Monte Carlo Engine ---
# Deterministic Logic
lance_embutido_brl = lance_embutido_pct * valor_carta_brl
credito_liquido_brl = valor_carta_brl - lance_embutido_brl
agio_bruto_brl = credito_liquido_brl * agio_pct
comissao_broker_brl = valor_carta_brl * comissao_broker_pct
lucro_liquido_brl = agio_bruto_brl - comissao_broker_brl

# Monte Carlo Simulation: Variabilidade do Lance de Contemplação
# Simulamos que o lance necessário para ganhar flutua em torno do lance_alvo_pct
np.random.seed(42)
lances_simulados = np.random.normal(lance_alvo_pct, volatilidade_lance, n_simulacoes)
lances_simulados = np.clip(lances_simulados, lance_embutido_pct, 0.90)

meses_contemplacao_sim = []
for lance_sim in lances_simulados:
    caixa_necessario_brl = max(0.0, (lance_sim * valor_carta_brl) - lance_embutido_brl)
    caixa_necessario_eur = caixa_necessario_brl / taxa_cambio_base
    mes = int(np.ceil(caixa_necessario_eur / caixa_paralelo_eur)) if caixa_paralelo_eur > 0 else max_months + 1
    meses_contemplacao_sim.append(min(mes, max_months + 1))

meses_contemplacao_sim = np.array(meses_contemplacao_sim)
prob_contemplacao = np.mean(meses_contemplacao_sim <= max_months)
mes_medio = np.median(meses_contemplacao_sim[meses_contemplacao_sim <= max_months]) if prob_contemplacao > 0 else max_months

# Resultados Base (Usando a mediana da simulação para ser mais conservador/realista)
mes_contemplacao = int(mes_medio)
total_desembolso_eur = (parcela_eur + caixa_paralelo_eur) * mes_contemplacao
total_desembolso_brl = total_desembolso_eur * taxa_cambio_base
roi_nominal = lucro_liquido_brl / total_desembolso_brl if total_desembolso_brl > 0 else 0
lucro_liq_eur_base = lucro_liquido_brl / taxa_cambio_base

# --- Header Section ---
st.markdown(f'''
    <div style="margin-bottom: 48px;">
        <p style="color: {COLORS["gold"]}; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; font-size: 11px; margin-bottom: 8px;">Institutional Asset Management</p>
        <h1 style="color: {COLORS["navy"]}; font-weight: 800; font-size: 42px; margin-top: 0; letter-spacing: -0.02em;">Consortium Strategy Simulator</h1>
        <p style="color: {COLORS["text_secondary"]}; font-size: 17px; max-width: 800px; line-height: 1.5;">
            Análise quantitativa com <b>Monte Carlo Engine</b> ({n_simulacoes} iterações). 
            Modelagem de risco de grupo e arbitragem cambial para Private Equity.
        </p>
    </div>
''', unsafe_allow_html=True)

# --- KPI Grid ---
st.markdown('<div class="section-title">Indicadores de Performance (Probabilísticos)</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)

kpi_data = [
    (c1, "Prob. Contemplação", f"{prob_contemplacao:.1%}", f"Em {max_months} meses", COLORS["success"] if prob_contemplacao > 0.7 else COLORS["gold"]),
    (c2, "ROI Esperado (Mediano)", f"{roi_nominal:.2%}", "Retorno s/ Capital", COLORS["navy"]),
    (c3, "Lucro Líquido", f"R$ {lucro_liquido_brl:,.0f}", f"€ {lucro_liq_eur_base:,.0f}", COLORS["navy"]),
    (c4, "Mês de Saída (P50)", f"{mes_contemplacao}", "Mediana da Simulação", COLORS["navy"]),
    (c5, "Desembolso Total", f"€ {total_desembolso_eur:,.0f}", f"R$ {total_desembolso_brl:,.0f}", COLORS["navy"]),
    (c6, "Risco de Grupo", f"{volatilidade_lance:.0%}", "Volatilidade do Lance", COLORS["error"]),
]

for col, lbl, val, sub, color in kpi_data:
    with col:
        st.markdown(f'''<div class='kpi-card'>
            <div class='kpi-label'>{lbl}</div>
            <div class='kpi-value' style="color: {color}">{val}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>''', unsafe_allow_html=True)

# --- Monte Carlo Visualization ---
st.markdown('<div class="section-title">Análise Estatística de Monte Carlo</div>', unsafe_allow_html=True)
col_mc1, col_mc2 = st.columns([1.5, 1])

with col_mc1:
    # Histograma de Contemplação
    fig_hist = go.Figure()
    valid_months = meses_contemplacao_sim[meses_contemplacao_sim <= max_months]
    fig_hist.add_trace(go.Histogram(
        x=valid_months,
        nbinsx=max_months,
        marker_color=COLORS["navy"],
        opacity=0.7,
        name="Simulações"
    ))
    fig_hist.update_layout(
        title="Distribuição de Probabilidade do Mês de Contemplação",
        xaxis_title="Mês",
        yaxis_title="Frequência (Simulações)",
    )
    apply_apple_theme(fig_hist)
    st.plotly_chart(fig_hist, use_container_width=True)

with col_mc2:
    # Probabilidade Acumulada
    counts, bin_edges = np.histogram(meses_contemplacao_sim, bins=range(1, max_months + 2))
    cdf = np.cumsum(counts) / n_simulacoes
    fig_cdf = go.Figure()
    fig_cdf.add_trace(go.Scatter(
        x=list(range(1, max_months + 1)), y=cdf,
        mode='lines', line=dict(color=COLORS["gold"], width=3),
        fill='tozeroy', fillcolor='rgba(175, 149, 0, 0.05)'
    ))
    fig_cdf.update_layout(
        title="Curva de Probabilidade Acumulada",
        xaxis_title="Mês",
        yaxis_title="Probabilidade de já ter sido contemplado",
        yaxis=dict(tickformat=".0%")
    )
    apply_apple_theme(fig_cdf)
    st.plotly_chart(fig_cdf, use_container_width=True)

# --- Standard Projections ---
st.markdown('<div class="section-title">Projeção de Fluxo e Sensibilidade</div>', unsafe_allow_html=True)
cl, cr = st.columns([1.2, 1])

with cl:
    # Waterfall Chart
    fig_wf = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ['absolute', 'relative', 'total', 'relative', 'relative', 'total'],
        x = ['Carta Bruta', 'Lance Embutido', 'Líquido', 'Ágio', 'Comissão', 'Lucro'],
        y = [valor_carta_brl, -lance_embutido_brl, 0, agio_bruto_brl, -comissao_broker_brl, 0],
        connector = {'line':{'color': COLORS["border"]}},
        increasing = {'marker':{'color': COLORS["success"]}},
        decreasing = {'marker':{'color': COLORS["error"]}},
        totals = {'marker':{'color': COLORS["navy"]}},
        textposition = 'outside'
    ))
    apply_apple_theme(fig_wf)
    fig_wf.update_layout(height=380, title="Cascata de Valor (R$)")
    st.plotly_chart(fig_wf, use_container_width=True)

with cr:
    # Sensitivity Table
    all_rates = sorted(set([taxa_cambio_base] + [float(r) for r in stress_rates]))
    stress_rows = []
    for r in all_rates:
        ll_eur = lucro_liquido_brl / r
        roi_eur = ll_eur / (total_desembolso_brl / r)
        stress_rows.append({
            "Cenário": "📌 Base" if r == taxa_cambio_base else "🔴 Stress",
            "Câmbio": f"R$ {r:.2f}",
            "Lucro (€)": f"€ {ll_eur:,.0f}",
            "ROI (€)": f"{roi_eur:.1%}"
        })
    st.markdown('<p style="font-size: 14px; font-weight: 600; color: var(--pe-navy); margin-bottom: 12px;">Sensibilidade Cambial (EUR)</p>', unsafe_allow_html=True)
    st.table(pd.DataFrame(stress_rows))

# --- Footer ---
st.markdown("---")
st.markdown(
    f"<p style='text-align: center; color: {COLORS['text_secondary']}; font-size: 12px;'>"
    "Proprietary Financial Model • Monte Carlo Engine v1.0 • Private Equity Strategy<br>"
    "© 2024 Asset-Light Simulator. All rights reserved."
    "</p>", 
    unsafe_allow_html=True
)
