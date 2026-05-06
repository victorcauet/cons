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
css_content = """
@import url('https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap');

:root {
    --primary-color: #0A2463; /* Deep Blue */
    --secondary-color: #1E1E1E; /* Charcoal Gray */
    --accent-color: #B8860B; /* Muted Gold */
    --background-light: #F8F8F8; /* Off-white */
    --background-dark: #EFEFEF; /* Light Gray */
    --text-dark: #2C2C2C;
    --text-light: #6C757D;
    --border-color: #DCDCDC;
    --positive-color: #28A745;
    --negative-color: #DC3545;
    --neutral-color: #6C757D;
}

html, body, [class*="css"] {
    font-family: 'Satoshi', sans-serif !important;
    color: var(--text-dark);
}

.main {
    background: var(--background-light);
}

.stSidebar {
    background: var(--secondary-color) !important;
}

.stSidebar label, .stSidebar .stMarkdown, .stSidebar p {
    color: var(--background-light) !important;
}

.stSidebar h2, .stSidebar h3 {
    color: var(--accent-color) !important;
}

.kpi-card {
    background: #fff;
    border-radius: 8px;
    padding: 20px 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    border: 1px solid var(--border-color);
    text-align: center;
    transition: all 0.2s ease-in-out;
}

.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.kpi-label {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--text-light);
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-dark);
    line-height: 1.2;
}

.kpi-sub {
    font-size: 12px;
    color: var(--text-light);
    margin-top: 6px;
}

.kpi-positive {
    color: var(--positive-color);
}

.kpi-negative {
    color: var(--negative-color);
}

.kpi-neutral  {
    color: var(--neutral-color);
}

.section-header {
    font-size: 18px;
    font-weight: 700;
    color: var(--primary-color);
    margin: 30px 0 15px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--accent-color);
}

.alert-box {
    background: rgba(40, 167, 69, 0.1);
    border-left: 4px solid var(--positive-color);
    border-radius: 8px;
    padding: 15px 20px;
    color: var(--positive-color);
    font-size: 14px;
    margin: 15px 0;
}

.warning-box {
    background: rgba(220, 53, 69, 0.1);
    border-left: 4px solid var(--negative-color);
    border-radius: 8px;
    padding: 15px 20px;
    color: var(--negative-color);
    font-size: 14px;
    margin: 15px 0;
}
"""
st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

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
caixa_par_necessario_eur   = caixa_par_necessario_brl / taxa_cambio_base if taxa_cambio_base > 0 else 0

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
lucro_liq_eur_base   = lucro_liquido_brl   / taxa_cambio_base if taxa_cambio_base > 0 else 0
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
    pct = (c * taxa_cambio_base + lance_embutido_brl) / valor_carta_brl * 100 if valor_carta_brl > 0 else 0
    lance_pct_list.append(pct)

df_sim = pd.DataFrame({
    "Mês": months,
    "Parcelas (€)": parc_acc,
    "Caixa Paralelo (€)": caixa_acc,
    "Desembolso Total (€)": desp_acc,
    "Lance % da Carta": lance_pct_list
})

# --- Header --- #
st.markdown('''<div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;">
  <div style="font-size:38px; color: var(--primary-color);">🏦</div>
  <div>
    <div style="font-size:24px;font-weight:700;color:var(--primary-color);">Simulador de Estratégia de Consórcio</div>
    <div style="font-size:14px;color:var(--text-light);">Análise de Investimento Asset-Light</div>
  </div>
</div>''', unsafe_allow_html=True)

if contemplado:
    st.markdown(f"""<div class='alert-box'>
        <strong>Cenário Base: Contemplação no Mês {mes_contemplacao}</strong><br>
        Capital acumulado de €{caixa_par_necessario_eur:,.2f} atinge o lance alvo de {lance_alvo_pct:.0%}.
    </div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""<div class='warning-box'>
        <strong>Atenção:</strong> No cenário base, a contemplação não ocorre dentro do horizonte de {max_months} meses.
    </div>""", unsafe_allow_html=True)

# --- KPIs --- #
st.markdown('<div class="section-header">Principais Indicadores</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
kpis = [
    (c1, "Mês de Contemplação", f"{mes_contemplacao}", "Horizonte Máximo: " + str(max_months), "neutral"),
    (c2, "Desembolso Total", f"€ {total_desembolso_eur:,.0f}", f"R$ {total_desembolso_brl:,.0f}", "neutral"),
    (c3, "Ágio Bruto", f"R$ {agio_bruto_brl:,.0f}", f"€ {agio_bruto_brl/taxa_cambio_base:,.0f}", "positive"),
    (c4, "Comissão do Broker", f"R$ {comissao_broker_brl:,.0f}", f"€ {comissao_broker_brl/taxa_cambio_base:,.0f}", "negative"),
    (c5, "Lucro Líquido", f"R$ {lucro_liquido_brl:,.0f}", f"€ {lucro_liq_eur_base:,.0f}", "positive" if lucro_liquido_brl >= 0 else "negative"),
    (c6, "ROI Nominal", f"{roi_nominal:.2%}", "Lucro / Desembolso", "positive" if roi_nominal >= 0 else "negative"),
]

for col, lbl, val, sub, cls in kpis:
    with col:
        st.markdown(f'''<div class='kpi-card'>
                        <div class='kpi-label'>{lbl}</div>
                        <div class=\'kpi-value kpi-{cls}\'>{val}</div>                    <div class='kpi-sub'>{sub}</div>
                      </div>''', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- Charts --- #
st.markdown('<div class="section-header">Projeção Financeira</div>', unsafe_allow_html=True)
fig = make_subplots(rows=1, cols=2,
                    subplot_titles=['Evolução do Desembolso (€)', 'Evolução do Lance (%)'],
                    horizontal_spacing=0.08)

# Gráfico de Desembolso Acumulado
fig.add_trace(go.Scatter(x=df_sim['Mês'], y=df_sim['Caixa Paralelo (€)'], name='Caixa Paralelo', fill='tozeroy', line=dict(color='var(--accent-color)'), fillcolor='rgba(184,134,11,0.1)'), row=1, col=1)
fig.add_trace(go.Scatter(x=df_sim['Mês'], y=df_sim['Desembolso Total (€)'], name='Desembolso Total', fill='tonexty', line=dict(color= 'var(--primary-color)'), fillcolor='rgba(10,36,99,0.2)'), row=1, col=1)

# Gráfico de Progresso do Lance
fig.add_trace(go.Scatter(x=df_sim['Mês'], y=df_sim['Lance % da Carta'], name='Lance Acumulado (%)', line=dict(color= 'var(--primary-color)', width=2.5), fill='tozeroy', fillcolor='rgba(10,36,99,0.1)'), row=1, col=2)
fig.add_hline(y=lance_alvo_pct*100, line_dash="dot", line_color="var(--negative-color)", annotation_text=f"Alvo {lance_alvo_pct*100:.0f}%", annotation_position="bottom right", annotation_font_color="var(--negative-color)", row=1, col=2)
fig.add_hline(y=lance_embutido_pct*100, line_dash="dot", line_color="var(--neutral-color)", annotation_text=f"Embutido {lance_embutido_pct*100:.0f}%", annotation_position="bottom right", annotation_font_color="var(--neutral-color)", row=1, col=2)

if contemplado:
    for c in [1,2]:
        fig.add_vline(x=mes_contemplacao, line_dash="dash", line_color="var(--positive-color)",
                      annotation_text=f"Contemplação Mês {mes_contemplacao}",
                      annotation_position="top",
                      annotation_font_color="var(--positive-color)", row=1, col=c)

fig.update_layout(height=380, showlegend=True,
                  legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                  plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)',
                  font=dict(family="Satoshi, sans-serif", color= 'var(--text-dark)', size=12),
                  margin=dict(l=20, r=20, t=50, b=80))
fig.update_xaxes(gridcolor= 'var(--background-dark)', title_text="Mês")
fig.update_yaxes(gridcolor= 'var(--background-dark)')
st.plotly_chart(fig, use_container_width=True)

# --- Waterfall + Exit Table --- #
st.markdown('<div class="section-header">Análise de Retorno</div>', unsafe_allow_html=True)
cl, cr = st.columns([1.3, 1])

with cl:
    fig_wf = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ['absolute', 'relative', 'total', 'relative', 'relative', 'total'],
        x = ['Carta Bruta', '(-) Lance Embutido', 'Crédito Líquido', f'(+) Ágio ({agio_pct:.0%})',
             f'(-) Comissão ({comissao_broker_pct:.0%})', 'Lucro Líquido'],
        y = [valor_carta_brl, -lance_embutido_brl, 0, agio_bruto_brl, -comissao_broker_brl, 0],
        connector = {'line':{'color': 'var(--border-color)'}},
        increasing = {'marker':{'color': 'var(--positive-color)'}},
        decreasing = {'marker':{'color': 'var(--negative-color)'}},
        totals = {'marker':{'color': 'var(--primary-color)'}},
        text = [f"R$ {abs(v):,.0f}" for v in [valor_carta_brl, -lance_embutido_brl, credito_liquido_brl, agio_bruto_brl, -comissao_broker_brl, lucro_liquido_brl]],
        textposition = 'outside',
    ))
    fig_wf.update_layout(height=340, title_text="Cascata de Valor (R$)",
                         plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)', showlegend=False,
                         font=dict(family="Satoshi, sans-serif", size=11, color="var(--text-dark)"),
                         margin=dict(l=10, r=10, t=40, b=10),
                         yaxis=dict(gridcolor='var(--background-dark)'))
    st.plotly_chart(fig_wf, use_container_width=True)

with cr:
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    df_exit = pd.DataFrame({
        "Item": ['Valor Total da Carta', '(-) Lance Embutido', '= Crédito Líquido',
                 f'(+) Ágio {agio_pct:.0%}', f'(-) Comissão {comissao_broker_pct:.0%}',
                 '✅ Lucro Líquido', 'Desembolso Total', '📊 ROI Nominal'],
        "R$":  [f'{valor_carta_brl:,.0f}', f'({lance_embutido_brl:,.0f})',
                f'{credito_liquido_brl:,.0f}', f'{agio_bruto_brl:,.0f}',
                f'({comissao_broker_brl:,.0f})', f'{lucro_liquido_brl:,.0f}',
                f'({total_desembolso_brl:,.0f})', f'{roi_nominal:.1%}'],
        "€ (base)": [f'{valor_carta_brl/taxa_cambio_base:,.0f}', f'({lance_embutido_brl/taxa_cambio_base:,.0f})',
                     f'{credito_liquido_brl/taxa_cambio_base:,.0f}', f'{agio_bruto_brl/taxa_cambio_base:,.0f}',
                     f'({comissao_broker_brl/taxa_cambio_base:,.0f})', f'{lucro_liq_eur_base:,.0f}',
                     f'({total_desembolso_eur:,.0f})', f'{roi_nominal:.1%}']
    })
    st.dataframe(df_exit, use_container_width=True, hide_index=True)

# --- Stress Test --- #
st.markdown('<div class="section-header">⚠️ Análise de Sensibilidade Cambial</div>', unsafe_allow_html=True)
all_rates = sorted(set([taxa_cambio_base] + [float(r) for r in stress_rates]))
stress_rows = []
for r in all_rates:
    ll_eur  = lucro_liquido_brl / r if r > 0 else 0
    dd_eur  = total_desembolso_brl / r if r > 0 else 0
    roi_eur = ll_eur / dd_eur if dd_eur > 0 else 0
    delta   = ll_eur - lucro_liq_eur_base
    delta_p = (delta / abs(lucro_liq_eur_base) * 100) if lucro_liq_eur_base != 0 else 0
    tag     = "📌 Base" if abs(r - taxa_cambio_base) < 0.01 else "🔴 Stress"
    stress_rows.append({
        "Cenário": tag, "R$/€": f'{r:.2f}',
        "Lucro (€)": f'{ll_eur:,.0f}', "Desembolso (€)": f'{dd_eur:,.0f}',
        "ROI em €": f'{roi_eur*100:.1f}%',
        "Δ vs Base (€)": f'{'▲' if delta>=0 else '▼'} {abs(delta):,.0f}',
        "Erosão (%)": f'{delta_p:+.1f}%'
    })
df_stress = pd.DataFrame(stress_rows)
st.dataframe(df_stress, use_container_width=True, hide_index=True)

# Bar chart stress
rates_chart  = [float(r['R$/€']) for r in stress_rows]
lucros_chart = [lucro_liquido_brl / r if r > 0 else 0 for r in rates_chart]
bar_colors   = ['var(--primary-color)' if abs(r - taxa_cambio_base) < 0.01 else ( 'var(--negative-color)' if l < 0 else 'var(--accent-color)') for r, l in zip(rates_chart, lucros_chart)]
fig_s = go.Figure(go.Bar(
    x=[f"R${r:.2f}/€" for r in rates_chart], y=lucros_chart,
    marker_color=bar_colors,
    text=[f"€ {v:,.0f}" for v in lucros_chart], textposition="outside"))
fig_s.add_hline(y=0, line_color="var(--text-dark)", line_width=1)
fig_s.update_layout(height=260, title="Lucro Líquido em € por Cenário Cambial",
    plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)', showlegend=False,
    font=dict(family="Satoshi, sans-serif", size=12, color="var(--text-dark)"),
    margin=dict(l=10, r=10, t=40, b=10),
    yaxis=dict(gridcolor='var(--background-dark)', title="€"), xaxis=dict(gridcolor='var(--background-dark)'))
st.plotly_chart(fig_s, use_container_width=True)

# --- Detail table --- #
with st.expander("📋 Fluxo Detalhado Mês a Mês", expanded=False):
    df_d = df_sim.copy()
    df_d['Status'] = df_d['Mês'].apply(
        lambda m: "🎯 CONTEMPLAÇÃO" if m == mes_contemplacao else ("✅ Pós-contemplação" if m > mes_contemplacao else "⏳ Acumulando"))
    df_d['Parcelas (R$)']      = (df_d['Parcelas (€)']      * taxa_cambio_base).round(0)
    df_d['Caixa Paralelo (R$)']= (df_d['Caixa Paralelo (€)']* taxa_cambio_base).round(0)
    df_d['Desembolso Total (R$)']= (df_d['Desembolso Total (€)'] * taxa_cambio_base).round(0)
    st.dataframe(df_d[['Mês','Parcelas (€)','Caixa Paralelo (€)','Desembolso Total (€)',
                        'Parcelas (R$)','Caixa Paralelo (R$)','Desembolso Total (R$)',
                        'Lance % da Carta','Status']].round(1),
                 use_container_width=True, hide_index=True)

st.markdown('---')
st.markdown('''<div style='font-size:11px;color:var(--text-light);text-align:center'>
            Simulação para fins de planejamento financeiro. Não constitui recomendação de investimento. 
            Resultados dependem de condições reais de mercado, do grupo de consórcio e da taxa de câmbio na repatriação.
            </div>''', unsafe_allow_html=True)
