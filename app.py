"""
app.py
======
PAINEL WEB do HELIOS (Streamlit + Plotly).

Centro de Controle visual da missão. Oferece:
  - indicadores (KPIs) de energia, bateria e sustentabilidade em tempo real;
  - gráficos da linha do tempo (geração x consumo, estado de carga, risco);
  - tabela de módulos com status colorido;
  - painel de alertas automáticos e log de decisões;
  - reprodução (playback) animada da missão ciclo a ciclo.

Execução:
    streamlit run app.py
"""

import time

import plotly.graph_objects as go
import streamlit as st

from src import config
from src.modelos import Severidade, StatusOperacional, StatusComunicacao
from src.monitor import MonitorMissao

st.set_page_config(page_title="HELIOS — Monitor Energetico Espacial",
                   page_icon="🛰️", layout="wide")

# --------------------------------------------------------------------------- #
# Estilo (tema espacial escuro)
# --------------------------------------------------------------------------- #
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at 20% 0%, #0b1226 0%, #060912 60%); }
    h1, h2, h3 { color: #e8ecff; }
    .stMetric { background:#111a33; border:1px solid #24365f; border-radius:12px;
                padding:10px 14px; }
    [data-testid="stMetricValue"] { color:#dfe7ff; }
    .crit { color:#ff5d6c; font-weight:700; }
    .atn  { color:#ffce54; font-weight:700; }
    .ok   { color:#4dd599; font-weight:700; }
    .card { background:#111a33; border:1px solid #24365f; border-radius:12px;
            padding:14px 16px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

CORES_SAUDE = {"NOMINAL": "#4dd599", "ATENCAO": "#ffce54", "CRITICO": "#ff5d6c"}


# --------------------------------------------------------------------------- #
# Barra lateral — controles da missão
# --------------------------------------------------------------------------- #
st.sidebar.title("🛰️ HELIOS")
st.sidebar.caption("Hub de Energia, Logística Inteligente\ne Operações Sustentáveis")
st.sidebar.markdown("---")

ciclos = st.sidebar.slider("Ciclos da missão", 20, 200, 90, step=10)
soc_pct0 = st.sidebar.slider("Carga inicial da bateria (%)", 5, 100, 60, step=5,
                             help="Valores baixos (ex.: 20%) acionam o modo de "
                                  "economia e o corte de carga automatico.")
semente = st.sidebar.number_input("Semente (aleatoriedade)", value=42, step=1)

if st.sidebar.button("🚀 Executar missão", use_container_width=True):
    monitor = MonitorMissao(semente=int(semente),
                            soc_inicial_wh=(soc_pct0 / 100) * config.CAPACIDADE_BATERIA_WH)
    historico = [monitor.proxima_leitura() for _ in range(ciclos)]
    st.session_state["hist"] = historico
    st.session_state["idx"] = 0
    st.session_state["play"] = False

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Painel solar:** {config.AREA_PAINEL_M2} m² · {int(config.EFICIENCIA_PAINEL*100)}%  \n"
    f"**Bateria:** {int(config.CAPACIDADE_BATERIA_WH)} Wh  \n"
    f"**Período orbital:** {int(config.PERIODO_ORBITAL_MIN)} min")


# --------------------------------------------------------------------------- #
# Tela inicial (sem missão executada)
# --------------------------------------------------------------------------- #
if "hist" not in st.session_state:
    st.title("HELIOS · Centro de Controle Energético")
    st.markdown("""
Sistema inteligente de **monitoramento de energias renováveis e sustentáveis**
de uma missão espacial experimental. Monitora geração solar, consumo dos
módulos, estado da bateria, temperatura e comunicação; gera **alertas
automáticos**, toma **decisões autônomas** de gestão de energia e usa **IA**
para detectar anomalias e prever a autonomia.

👈 Configure os parâmetros na barra lateral e clique em **Executar missão**.
""")
    st.info("Dica: defina a carga inicial em ~20% para ver o motor de decisão "
            "cortar cargas não críticas e ativar o modo de economia.")
    st.stop()


hist = st.session_state["hist"]
n = len(hist)

# --------------------------------------------------------------------------- #
# Controles de reprodução
# --------------------------------------------------------------------------- #
c1, c2, c3 = st.columns([1, 1, 4])
play = c1.toggle("▶ Reproduzir", value=st.session_state.get("play", False))
st.session_state["play"] = play
if c2.button("⏮ Reiniciar"):
    st.session_state["idx"] = 0
idx = st.slider("Ciclo da missão", 0, n - 1, st.session_state.get("idx", 0))
st.session_state["idx"] = idx

leitura = hist[idx]

# --------------------------------------------------------------------------- #
# Cabeçalho + saúde geral
# --------------------------------------------------------------------------- #
cor = CORES_SAUDE[leitura.saude_geral]
fase = "🌑 ECLIPSE (sem Sol)" if leitura.em_eclipse else "☀️ ILUMINADO (gerando)"
st.markdown(f"## T+{leitura.instante_min:.0f} min &nbsp;|&nbsp; "
            f"<span style='color:{cor}'>Saúde: {leitura.saude_geral}</span> "
            f"<span style='color:#9fb3d1;font-size:0.6em'>(risco IA {leitura.risco_pct:.0f}/100)</span> "
            f"&nbsp;|&nbsp; <span style='color:#9fb3d1;font-size:0.6em'>{fase}</span>",
            unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Geração solar", f"{leitura.geracao_w:.0f} W", help="Fonte renovável")
k2.metric("Consumo total", f"{leitura.consumo_total_w:.0f} W")
k3.metric("Saldo energético", f"{leitura.potencia_liquida_w:.0f} W",
          delta="superávit" if leitura.potencia_liquida_w >= 0 else "déficit",
          delta_color="normal" if leitura.potencia_liquida_w >= 0 else "inverse")
k4.metric("Bateria (SoC)", f"{leitura.soc_pct:.1f} %")
k5.metric("Sustentabilidade", f"{leitura.indice_sustentabilidade:.0f} %",
          help="% do consumo coberto por energia renovável")

aut = "estável" if leitura.autonomia_h >= 999 else f"{leitura.autonomia_h*60:.0f} min"
st.caption(f"Autonomia estimada da bateria (previsão IA): **{aut}**")

st.markdown("---")

# --------------------------------------------------------------------------- #
# Gráficos da linha do tempo
# --------------------------------------------------------------------------- #
tempos = [l.instante_min for l in hist[:idx + 1]]
ger = [l.geracao_w for l in hist[:idx + 1]]
con = [l.consumo_total_w for l in hist[:idx + 1]]
soc = [l.soc_pct for l in hist[:idx + 1]]
risco = [l.risco_pct for l in hist[:idx + 1]]

g1, g2 = st.columns(2)

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=tempos, y=ger, name="Geração (renovável)",
                          line=dict(color="#ffce54", width=2), fill="tozeroy",
                          fillcolor="rgba(255,206,84,0.15)"))
fig1.add_trace(go.Scatter(x=tempos, y=con, name="Consumo",
                          line=dict(color="#5b8cff", width=2)))
fig1.update_layout(title="Geração solar × Consumo (W)", template="plotly_dark",
                   height=300, margin=dict(l=10, r=10, t=40, b=10),
                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                   legend=dict(orientation="h", y=1.15))
g1.plotly_chart(fig1, use_container_width=True)

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=tempos, y=soc, name="SoC (%)",
                          line=dict(color="#4dd599", width=2), fill="tozeroy",
                          fillcolor="rgba(77,213,153,0.12)"))
fig2.add_hline(y=config.SOC_ATENCAO_PCT, line_dash="dot", line_color="#ffce54",
               annotation_text="atenção")
fig2.add_hline(y=config.SOC_CRITICO_PCT, line_dash="dot", line_color="#ff5d6c",
               annotation_text="crítico")
fig2.update_layout(title="Estado de carga da bateria (%)", template="plotly_dark",
                   height=300, margin=dict(l=10, r=10, t=40, b=10),
                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                   yaxis=dict(range=[0, 100]))
g2.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------------------------------- #
# Módulos + Alertas + Decisões
# --------------------------------------------------------------------------- #
col_mod, col_eventos = st.columns([3, 2])

with col_mod:
    st.subheader("Módulos da missão")
    cor_status = {"NOMINAL": "#4dd599", "REDUZIDO": "#ffce54",
                  "DESLIGADO": "#6c7a99", "FALHA": "#ff5d6c"}
    cor_comm = {"ONLINE": "#4dd599", "DEGRADADA": "#ffce54", "OFFLINE": "#ff5d6c"}
    linhas = ("<table style='width:100%;border-collapse:collapse;color:#dfe7ff'>"
              "<tr style='color:#9fb3d1;text-align:left'>"
              "<th>Módulo</th><th>Status</th><th>Consumo</th><th>Temp</th>"
              "<th>Comm</th><th>Crítico</th></tr>")
    for m in leitura.modulos:
        cs = cor_status[m.status.value]
        cc = cor_comm[m.comunicacao.value]
        ct = "#ff5d6c" if m.temperatura >= 70 else ("#ffce54" if m.temperatura >= 55 else "#dfe7ff")
        linhas += (f"<tr style='border-top:1px solid #24365f'>"
                   f"<td>{m.nome}</td>"
                   f"<td style='color:{cs}'>{m.status.value}</td>"
                   f"<td>{m.consumo_w:.0f} W</td>"
                   f"<td style='color:{ct}'>{m.temperatura:.0f} °C</td>"
                   f"<td style='color:{cc}'>{m.comunicacao.value}</td>"
                   f"<td>{'🔴' if m.critico else '—'}</td></tr>")
    linhas += "</table>"
    st.markdown(linhas, unsafe_allow_html=True)

with col_eventos:
    st.subheader("Alertas automáticos")
    if not leitura.alertas:
        st.markdown("<div class='card ok'>Nenhum alerta — operação nominal.</div>",
                    unsafe_allow_html=True)
    else:
        cls = {Severidade.CRITICO: "crit", Severidade.ATENCAO: "atn", Severidade.INFO: "ok"}
        for a in leitura.alertas:
            st.markdown(
                f"<div class='card'><span class='{cls[a.severidade]}'>"
                f"[{a.severidade.value}]</span> <b>{a.origem}</b>: {a.mensagem}</div>",
                unsafe_allow_html=True)

    st.subheader("Decisões automatizadas")
    if not leitura.decisoes:
        st.markdown("<div class='card'>Sem ações — sistema estável.</div>",
                    unsafe_allow_html=True)
    else:
        for d in leitura.decisoes:
            st.markdown(f"<div class='card'>⚙️ <b>{d.acao}</b><br>"
                        f"<span style='color:#9fb3d1;font-size:0.9em'>{d.motivo}</span></div>",
                        unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Animação (playback)
# --------------------------------------------------------------------------- #
if play and idx < n - 1:
    time.sleep(0.55)
    st.session_state["idx"] = idx + 1
    st.rerun()
elif play and idx >= n - 1:
    st.session_state["play"] = False
