# 🛰️ HELIOS — Monitoramento Energético de Missão Espacial

**Hub de Energia, Logística Inteligente e Operações Sustentáveis**

> Global Solution · Ciência da Computação (1CCPK) · **Soluções em Energias Renováveis e Sustentáveis**

Sistema inteligente de **monitoramento de sistemas energéticos** de uma missão
espacial experimental. O HELIOS recebe, interpreta e exibe dados simulados das
condições operacionais (temperatura, comunicação, energia e status dos
módulos), **gera alertas automáticos**, **toma decisões autônomas** de gestão de
energia e aplica **Inteligência Artificial introdutória** para detectar
anomalias e prever a autonomia da bateria.

O tema da disciplina — **energias renováveis e sustentáveis** — está no centro
da solução: a fonte de energia da missão é **fotovoltaica (painéis solares)**,
com **bateria** para armazenar o excedente captado e atravessar os períodos de
eclipse. Um **Índice de Sustentabilidade** mede continuamente quanto do consumo
está sendo coberto por energia renovável.

---

## Aderência ao desafio

| Requisito técnico do desafio | Onde está implementado |
|---|---|
| **Monitoramento de dados simulados** (temperatura, comunicação, energia, status dos módulos) | `src/simulador.py` (gera telemetria) + `src/monitor.py` (interpreta) |
| **Geração automática de alertas** diante de condições críticas | `src/alertas.py` |
| **Tomada de decisão básica** / respostas automatizadas | `src/decisao.py` |
| **Visualização clara e organizada** dos dados | `app.py` (painel web) e `cli.py` (terminal) |
| **Algoritmos / pensamento computacional / IA introdutória** | `src/ia.py`, `src/energia.py` |

---

## Conceitos de energia, potência e sustentabilidade aplicados

Todas as fórmulas físicas ficam isoladas e testáveis em **`src/energia.py`**:

| Conceito | Fórmula | Uso na missão |
|---|---|---|
| **Geração solar** (renovável) | `P_ger = Irradiância × Área × Eficiência` | Potência produzida pelos painéis ao Sol |
| **Energia** | `E = P × t` | Conversão potência → Watt-hora |
| **Saldo energético** | `P_líq = P_ger − P_consumo` | Superávit (carrega) ou déficit (descarrega) |
| **Estado de carga (SoC)** | `SoC% = E_armazenada / Capacidade` | Nível da bateria |
| **Autonomia** | `t = E_armazenada / P_déficit` | Quanto tempo a reserva dura |
| **Índice de Sustentabilidade** | `0,7 × cobertura_renovável + 0,3 × reserva` | % do consumo coberto por energia limpa |

A nave alterna entre fase **iluminada** (gera energia solar e carrega a bateria)
e **eclipse** (geração zero — depende 100% da bateria), reproduzindo o desafio
real de sustentabilidade energética de uma operação espacial.

---

## Inteligência Artificial introdutória (`src/ia.py`)

Três técnicas acessíveis, porém genuínas, sem bibliotecas pesadas:

1. **Detecção de anomalias (z-score)** — janela móvel das últimas leituras de
   temperatura de cada módulo; valores que se afastam mais de 2,5 desvios da
   média são marcados como anômalos *antes* de virarem falhas.
2. **Previsão de autonomia (regressão linear)** — ajusta uma reta
   (`numpy.polyfit`) à tendência recente do estado de carga e **extrapola**
   quando a bateria chegaria ao nível crítico.
3. **Classificação de saúde (pontuação de risco ponderada)** — combina bateria,
   déficit, temperatura, comunicação e anomalias em uma pontuação 0–100,
   classificando a missão como **NOMINAL / ATENÇÃO / CRÍTICO**.

---

## Alertas automáticos (`src/alertas.py`)

Gerados por severidade (**INFO / ATENÇÃO / CRÍTICO**) para: bateria baixa,
déficit de potência, autonomia curta, superaquecimento, temperatura muito
baixa, perda/degradação de comunicação e anomalias detectadas pela IA.

## Tomada de decisão automatizada (`src/decisao.py`)

Diante de situações críticas, o sistema reage sozinho, **priorizando sempre os
módulos críticos** (suporte à vida, navegação, comunicação, controle térmico):

1. **Déficit + bateria crítica** → desliga o módulo **não crítico** de maior consumo.
2. **Atenção + déficit** → reduz a potência de módulos secundários (economia).
3. **Bateria em emergência** → **modo de sobrevivência** (apenas o essencial).
4. **Energia restabelecida** → restaura potência plena e **religa** módulos.
5. **Proteção térmica** → reduz/desliga módulos em superaquecimento crítico.

---

## Estrutura do projeto

```
helios/
├── app.py                # Painel web (Streamlit + Plotly)
├── cli.py                # Painel no terminal (rich)
├── requirements.txt
├── README.md
├── src/
│   ├── config.py         # Constantes físicas, módulos e limiares
│   ├── modelos.py        # Estruturas de dados (dataclasses)
│   ├── energia.py        # Núcleo de energia/potência/sustentabilidade
│   ├── simulador.py      # Geração de dados simulados (dinâmica orbital)
│   ├── ia.py             # IA: anomalias, previsão e classificação
│   ├── alertas.py        # Geração automática de alertas
│   ├── decisao.py        # Respostas automatizadas / tomada de decisão
│   └── monitor.py        # Orquestra o ciclo de monitoramento
└── dados/                # Saída opcional de telemetria (CSV)
```

Fluxo de cada ciclo: **simulador → energia → IA → alertas → decisão → visualização**.

---

##  Como executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Painel web (recomendado para a demonstração)
```bash
streamlit run app.py
```
Configure na barra lateral o número de ciclos e a **carga inicial da bateria**.
>  Defina a carga inicial em ~20% para ver o motor de decisão **cortar cargas
> não críticas** e ativar o modo de economia. Use ** Reproduzir** para animar.

### 3. Painel no terminal (funciona sem navegador)
```bash
python cli.py                    # missão padrão (45 ciclos)
python cli.py --ciclos 90        # mais ciclos
python cli.py --soc 20           # cenário crítico (corte de carga)
python cli.py --rapido           # sem pausa entre ciclos
python cli.py --csv saida.csv    # exporta a telemetria ao final
```

---

## Critérios de avaliação atendidos

- **Técnica (60):** código modular e organizado em pacote `src/`, separação clara
  de responsabilidades, alertas e decisões totalmente automatizados.
- **Inovação (30):** IA introdutória (z-score + regressão linear + score de risco),
  motor de decisão com priorização de cargas e Índice de Sustentabilidade.
- **Usabilidade (10):** painel web com KPIs, gráficos interativos e playback;
  alternativa em terminal acessível em qualquer ambiente.

---

##  Integrantes

- Matheus Caaviglia ferreira - 569638
- Gustavo Henrique Pereira Correia - 569921
