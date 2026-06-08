"""
ia.py
=====
INTELIGÊNCIA ARTIFICIAL INTRODUTÓRIA do HELIOS.

Aplica três técnicas acessíveis, porém genuínas, de análise inteligente de
dados — sem depender de bibliotecas pesadas de machine learning:

1. DETECÇÃO DE ANOMALIAS (estatística / z-score)
   Mantém uma janela móvel das últimas leituras de cada sinal e marca como
   anômalo todo valor que se afasta demais da média (acima de N desvios
   padrão). Detecta problemas ANTES de virarem falhas.

2. PREVISÃO DE AUTONOMIA (regressão linear)
   Ajusta uma reta (numpy.polyfit) à tendência recente do estado de carga
   da bateria e EXTRAPOLA quando ela chegaria a um nível crítico. É uma
   previsão preditiva simples, base de modelos de séries temporais.

3. CLASSIFICAÇÃO DE SAÚDE (pontuação de risco ponderada)
   Combina vários indicadores (bateria, temperatura, comunicação, déficit)
   em uma pontuação 0-100 e classifica a missão como NOMINAL / ATENÇÃO /
   CRÍTICO — uma forma introdutória de classificação baseada em regras.
"""

from collections import defaultdict, deque
from typing import Deque, Dict, List

import numpy as np

from . import config
from .modelos import EstadoModulo, StatusComunicacao


class CerebroIA:
    """Agrupa as técnicas de IA usadas no monitoramento inteligente."""

    def __init__(self, janela: int = config.JANELA_IA):
        self.janela = janela
        # histórico de temperaturas por módulo (janela móvel)
        self._hist_temp: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=janela))
        # histórico de SoC (%) para previsão de autonomia
        self._hist_soc: Deque[float] = deque(maxlen=max(janela, 6))

    # ------------------------------------------------------------------
    # 1) DETECÇÃO DE ANOMALIAS
    # ------------------------------------------------------------------
    def detectar_anomalias(self, modulos: List[EstadoModulo]) -> List[str]:
        """
        Retorna a lista de descrições de anomalias detectadas nesta leitura,
        usando z-score sobre a janela móvel de temperatura de cada módulo.
        """
        anomalias: List[str] = []
        for m in modulos:
            hist = self._hist_temp[m.nome]
            if len(hist) >= 4:
                media = float(np.mean(hist))
                desvio = float(np.std(hist))
                if desvio > 0.1:
                    z = (m.temperatura - media) / desvio
                    if abs(z) >= config.ZSCORE_ANOMALIA:
                        anomalias.append(
                            f"{m.nome}: temperatura anomala "
                            f"({m.temperatura:.1f} C, z={z:+.1f})")
            hist.append(m.temperatura)
        return anomalias

    # ------------------------------------------------------------------
    # 2) PREVISÃO DE AUTONOMIA (regressão linear sobre o SoC)
    # ------------------------------------------------------------------
    def prever_tempo_ate_critico(self, soc_pct: float) -> float | None:
        """
        Atualiza o histórico de SoC e prevê, por regressão linear, em quantos
        MINUTOS o estado de carga atingirá o nível crítico, mantida a
        tendência atual. Retorna None se a bateria não estiver descarregando.
        """
        self._hist_soc.append(soc_pct)
        if len(self._hist_soc) < 4:
            return None

        y = np.array(self._hist_soc, dtype=float)
        x = np.arange(len(y)) * config.PASSO_TEMPO_MIN  # eixo de tempo em min
        # ajuste de reta: y = a*x + b  (a = inclinação = taxa de variação)
        a, b = np.polyfit(x, y, 1)

        if a >= -0.01:          # estável ou carregando -> sem previsão de risco
            return None

        x_atual = x[-1]
        # resolve a*x + b = SOC_CRITICO  ->  x = (crit - b)/a
        x_critico = (config.SOC_CRITICO_PCT - b) / a
        minutos = x_critico - x_atual
        return round(minutos, 1) if minutos > 0 else 0.0

    # ------------------------------------------------------------------
    # 3) CLASSIFICAÇÃO DE SAÚDE / PONTUAÇÃO DE RISCO
    # ------------------------------------------------------------------
    def avaliar_saude(self, soc_pct: float, potencia_liquida_w: float,
                      modulos: List[EstadoModulo],
                      n_anomalias: int) -> tuple[str, float]:
        """
        Calcula uma pontuação de risco (0-100) combinando vários sinais com
        pesos, e devolve (classificacao, risco_pct).

        Quanto maior a pontuação, pior a saúde da missão.
        """
        risco = 0.0

        # Bateria: risco cresce conforme o SoC cai
        if soc_pct < config.SOC_EMERGENCIA_PCT:
            risco += 45
        elif soc_pct < config.SOC_CRITICO_PCT:
            risco += 30
        elif soc_pct < config.SOC_ATENCAO_PCT:
            risco += 15

        # Déficit de energia (consumindo mais do que gera)
        if potencia_liquida_w < 0:
            risco += min(20.0, abs(potencia_liquida_w) / 30.0)

        # Temperatura dos módulos
        for m in modulos:
            if m.temperatura >= config.TEMP_MAX_CRITICA:
                risco += 12
            elif m.temperatura >= config.TEMP_MAX_ATENCAO:
                risco += 5
            if m.temperatura <= config.TEMP_MIN_SEGURA:
                risco += 5

        # Comunicação
        for m in modulos:
            if m.comunicacao == StatusComunicacao.OFFLINE:
                risco += 12
            elif m.comunicacao == StatusComunicacao.DEGRADADA:
                risco += 5

        # Anomalias detectadas pela IA
        risco += n_anomalias * 4

        risco = round(min(100.0, risco), 1)

        if risco >= 50:
            classe = "CRITICO"
        elif risco >= 25:
            classe = "ATENCAO"
        else:
            classe = "NOMINAL"
        return classe, risco
