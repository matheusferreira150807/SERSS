"""
decisao.py
==========
Motor de TOMADA DE DECISÃO BÁSICA / RESPOSTAS AUTOMATIZADAS.

Implementa as "estruturas lógicas para tomada de decisão" exigidas pelo
desafio. Diante de situações críticas (bateria baixa, superaquecimento,
perda de comunicação), o sistema reage SOZINHO, ajustando os módulos para
preservar a missão — priorizando sempre os módulos CRÍTICOS (suporte à
vida, navegação etc.).

Estratégia de gestão sustentável de energia (carga progressiva):
  1. Déficit + bateria baixa  -> corta cargas NÃO críticas (economia máxima).
  2. Déficit persistente      -> reduz potência dos módulos que permitem.
  3. Bateria muito baixa      -> MODO DE SOBREVIVÊNCIA (só o essencial).
  4. Sobra de energia + SoC ok-> RELIGA módulos para retomar operação plena.
"""

from typing import List

from . import config
from .modelos import (Decisao, EstadoModulo, StatusComunicacao)


def _nao_criticos_ligados(modulos):
    return [m for m in modulos if not m.critico and m.ligado]


def _reduziveis_em_nominal(modulos):
    return [m for m in modulos
            if m.pode_reduzir and m.ligado and not m.reduzido]


def decidir(instante_min: float, soc_pct: float, potencia_liquida_w: float,
            modulos: List[EstadoModulo]) -> List[Decisao]:
    """
    Analisa o estado e aplica ações automatizadas DIRETAMENTE nos módulos.
    Retorna a lista de decisões tomadas (para registro/visualização).
    """
    decisoes: List[Decisao] = []

    def registrar(acao, motivo):
        decisoes.append(Decisao(acao, motivo, instante_min))

    deficit = potencia_liquida_w < 0

    # 1) MODO DE SOBREVIVÊNCIA: bateria em emergência -----------------------
    if soc_pct < config.SOC_EMERGENCIA_PCT:
        for m in modulos:
            if not m.critico and m.ligado:
                m.ligado = False
                registrar(f"Desligar {m.nome}",
                          "Modo de sobrevivencia: bateria em emergencia")
            elif m.critico and m.pode_reduzir and not m.reduzido:
                m.reduzido = True
                registrar(f"Reduzir {m.nome}",
                          "Modo de sobrevivencia: economia de energia")
    # 2) BATERIA CRÍTICA + DÉFICIT: corta não críticos ----------------------
    elif soc_pct < config.SOC_CRITICO_PCT and deficit:
        nao_criticos = _nao_criticos_ligados(modulos)
        if nao_criticos:
            # corta o de MAIOR consumo primeiro (mais economia por ação)
            alvo = max(nao_criticos, key=lambda m: m.consumo_w)
            alvo.ligado = False
            registrar(f"Desligar {alvo.nome}",
                      f"Bateria critica ({soc_pct:.0f}%) e deficit de energia")
        else:
            reduziveis = _reduziveis_em_nominal(modulos)
            if reduziveis:
                alvo = max(reduziveis, key=lambda m: m.consumo_w)
                alvo.reduzido = True
                registrar(f"Reduzir {alvo.nome}",
                          "Bateria critica: reducao de potencia")
    # 3) ATENÇÃO + DÉFICIT: reduz potência de módulos secundários -----------
    elif soc_pct < config.SOC_ATENCAO_PCT and deficit:
        reduziveis = [m for m in _reduziveis_em_nominal(modulos) if not m.critico]
        if reduziveis:
            alvo = max(reduziveis, key=lambda m: m.consumo_w)
            alvo.reduzido = True
            registrar(f"Reduzir {alvo.nome}",
                      f"Bateria em atencao ({soc_pct:.0f}%): economia preventiva")

    # 4) RECUPERAÇÃO: sobra de energia e bateria saudável -> religa ----------
    if not deficit and soc_pct > config.SOC_ATENCAO_PCT + 10:
        # primeiro retoma potência plena dos reduzidos, depois religa desligados
        reduzidos = [m for m in modulos if m.reduzido and m.ligado]
        if reduzidos:
            alvo = reduzidos[0]
            alvo.reduzido = False
            registrar(f"Restaurar {alvo.nome}",
                      "Energia restabelecida: operacao nominal")
        else:
            desligados = [m for m in modulos if not m.ligado]
            if desligados:
                alvo = desligados[0]
                alvo.ligado = True
                alvo.reduzido = True  # religa em modo econômico por segurança
                registrar(f"Religar {alvo.nome}",
                          "Energia restabelecida: retomando operacao")

    # 5) PROTEÇÃO TÉRMICA: superaquecimento crítico -> reduz/desliga --------
    for m in modulos:
        if m.temperatura >= config.TEMP_MAX_CRITICA and m.ligado:
            if m.pode_reduzir and not m.reduzido:
                m.reduzido = True
                registrar(f"Reduzir {m.nome}",
                          f"Protecao termica: {m.temperatura:.0f} C")
            elif not m.critico:
                m.ligado = False
                registrar(f"Desligar {m.nome}",
                          f"Protecao termica critica: {m.temperatura:.0f} C")

    return decisoes
