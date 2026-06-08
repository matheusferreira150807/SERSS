"""
alertas.py
==========
Motor de GERAÇÃO AUTOMÁTICA DE ALERTAS.

Avalia o estado atual da missão e produz uma lista de alertas com nível de
severidade (INFO, ATENÇÃO, CRÍTICO). Atende ao requisito do desafio de
"geração automática de alertas diante de condições críticas simuladas".

A lógica é totalmente baseada nos limiares definidos em config.py, o que
mantém as regras transparentes e fáceis de ajustar.
"""

from typing import List

from . import config
from .modelos import (Alerta, Severidade, EstadoModulo,
                      StatusComunicacao)


def gerar_alertas(instante_min: float, soc_pct: float,
                  potencia_liquida_w: float, autonomia_h: float,
                  modulos: List[EstadoModulo],
                  anomalias: List[str]) -> List[Alerta]:
    """Avalia todos os subsistemas e devolve a lista de alertas ativos."""
    alertas: List[Alerta] = []

    def add(sev, origem, msg):
        alertas.append(Alerta(sev, origem, msg, instante_min))

    # ---- BATERIA / ENERGIA ------------------------------------------------
    if soc_pct < config.SOC_EMERGENCIA_PCT:
        add(Severidade.CRITICO, "Bateria",
            f"SoC em nivel de EMERGENCIA: {soc_pct:.1f}%")
    elif soc_pct < config.SOC_CRITICO_PCT:
        add(Severidade.CRITICO, "Bateria",
            f"SoC critico: {soc_pct:.1f}% — reserva de energia baixa")
    elif soc_pct < config.SOC_ATENCAO_PCT:
        add(Severidade.ATENCAO, "Bateria",
            f"SoC em atencao: {soc_pct:.1f}%")

    if potencia_liquida_w < 0:
        add(Severidade.ATENCAO, "Energia",
            f"Deficit de potencia: {potencia_liquida_w:.0f} W "
            f"(consumo maior que geracao)")

    if autonomia_h < 1.0 and potencia_liquida_w < 0:
        add(Severidade.CRITICO, "Energia",
            f"Autonomia baixa: ~{autonomia_h*60:.0f} min de reserva")

    # ---- TEMPERATURA ------------------------------------------------------
    for m in modulos:
        if m.temperatura >= config.TEMP_MAX_CRITICA:
            add(Severidade.CRITICO, m.nome,
                f"Superaquecimento critico: {m.temperatura:.1f} C")
        elif m.temperatura >= config.TEMP_MAX_ATENCAO:
            add(Severidade.ATENCAO, m.nome,
                f"Temperatura elevada: {m.temperatura:.1f} C")
        elif m.temperatura <= config.TEMP_MIN_SEGURA:
            add(Severidade.ATENCAO, m.nome,
                f"Temperatura muito baixa: {m.temperatura:.1f} C")

    # ---- COMUNICAÇÃO ------------------------------------------------------
    for m in modulos:
        if m.comunicacao == StatusComunicacao.OFFLINE:
            add(Severidade.CRITICO, m.nome, "Comunicacao OFFLINE — link perdido")
        elif m.comunicacao == StatusComunicacao.DEGRADADA:
            add(Severidade.ATENCAO, m.nome, "Comunicacao DEGRADADA")

    # ---- ANOMALIAS DETECTADAS PELA IA ------------------------------------
    for a in anomalias:
        add(Severidade.ATENCAO, "IA", f"Anomalia detectada — {a}")

    return alertas
