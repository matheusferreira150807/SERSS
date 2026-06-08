"""
simulador.py
============
Gerador de DADOS SIMULADOS da missão espacial.

Como não temos uma nave real, o simulador produz telemetria realista a
partir de uma dinâmica orbital simplificada:

  - A nave orbita a Terra; parte da órbita fica iluminada pelo Sol e parte
    fica na sombra (ECLIPSE). Na luz há geração solar; no eclipse, não.
  - As temperaturas dos módulos sobem ao Sol e caem no eclipse.
  - O consumo de cada módulo depende do seu estado (ligado/reduzido/desligado),
    controlado pelo motor de decisão.
  - Anomalias aleatórias (picos de temperatura, falha de comunicação) são
    injetadas para exercitar os alertas, a IA e a tomada de decisão.
"""

import math
import random
from typing import List

from . import config
from .modelos import (EstadoModulo, StatusOperacional, StatusComunicacao)


class SimuladorMissao:
    """Produz leituras de telemetria a cada passo de tempo."""

    def __init__(self, semente: int | None = 42):
        if semente is not None:
            random.seed(semente)
        self.tempo_min = 0.0

    def em_eclipse(self, tempo_min: float) -> bool:
        """
        Determina se a nave está na sombra da Terra.
        Usa a posição dentro do período orbital: a fração final da órbita
        (definida por FRACAO_ECLIPSE) é considerada eclipse.
        """
        fase = (tempo_min % config.PERIODO_ORBITAL_MIN) / config.PERIODO_ORBITAL_MIN
        return fase > (1.0 - config.FRACAO_ECLIPSE)

    def irradiancia(self, tempo_min: float, eclipse: bool) -> float:
        """
        Irradiância solar instantânea (W/m^2).
        Ao Sol, varia suavemente conforme o ângulo de incidência nos painéis
        (modelado por uma função seno); no eclipse é zero.
        """
        if eclipse:
            return 0.0
        fase = (tempo_min % config.PERIODO_ORBITAL_MIN) / config.PERIODO_ORBITAL_MIN
        # ângulo de incidência: melhor no meio da parte iluminada
        fator = math.sin(math.pi * fase / (1.0 - config.FRACAO_ECLIPSE))
        fator = max(0.2, fator)  # nunca totalmente zero enquanto há Sol
        return config.CONSTANTE_SOLAR * fator

    def atualizar_temperaturas(self, modulos: List[EstadoModulo], eclipse: bool):
        """
        Atualiza a temperatura de cada módulo.
        Ao Sol a temperatura tende a subir; no eclipse, a cair. Módulos
        desligados esfriam mais rápido. Há um ruído aleatório pequeno.
        """
        alvo_externo = 8.0 if eclipse else 35.0
        for m in modulos:
            base = m.temperatura
            # módulos ligados geram calor próprio proporcional ao consumo
            calor_proprio = 6.0 if (m.ligado and not m.reduzido) else (3.0 if m.ligado else 0.0)
            alvo = m.temp_base + (alvo_externo - 20.0) * 0.4 + calor_proprio
            # aproxima-se do alvo de forma suave + ruído
            m.temperatura = round(base + (alvo - base) * 0.3 + random.uniform(-1.5, 1.5), 1)

    def injetar_anomalias(self, modulos: List[EstadoModulo], tempo_min: float):
        """
        Injeta eventos anômalos ocasionais para testar o sistema:
        - pico de superaquecimento em um módulo;
        - degradação/perda de comunicação.
        """
        # ~12% de chance de um pico térmico em algum módulo a cada passo
        if random.random() < 0.12:
            alvo = random.choice(modulos)
            if alvo.ligado:
                alvo.temperatura = round(alvo.temperatura + random.uniform(20, 45), 1)

        # ~8% de chance de problema de comunicação no módulo de comunicação
        for m in modulos:
            if m.nome == "Comunicacao" and m.ligado:
                r = random.random()
                if r < 0.05:
                    m.comunicacao = StatusComunicacao.OFFLINE
                elif r < 0.13:
                    m.comunicacao = StatusComunicacao.DEGRADADA
                else:
                    m.comunicacao = StatusComunicacao.ONLINE

    def calcular_consumo(self, modulos: List[EstadoModulo]):
        """
        Define o consumo (W) de cada módulo conforme seu estado:
          - desligado  -> 0 W
          - reduzido   -> potência nominal x FATOR_REDUCAO
          - nominal    -> potência nominal (com pequena variação realista)
        """
        for m in modulos:
            if not m.ligado:
                m.consumo_w = 0.0
                m.status = StatusOperacional.DESLIGADO
            elif m.reduzido and m.pode_reduzir:
                m.consumo_w = round(m.potencia_nominal_w * config.FATOR_REDUCAO
                                    * random.uniform(0.97, 1.03), 1)
                m.status = StatusOperacional.REDUZIDO
            else:
                m.consumo_w = round(m.potencia_nominal_w * random.uniform(0.96, 1.05), 1)
                m.status = StatusOperacional.NOMINAL

    def passo(self, modulos: List[EstadoModulo]):
        """
        Executa um passo de simulação, atualizando o ambiente e a telemetria
        bruta dos módulos. Retorna (tempo, em_eclipse, irradiância).
        Os cálculos de energia/bateria são feitos pelo monitor.
        """
        eclipse = self.em_eclipse(self.tempo_min)
        irr = self.irradiancia(self.tempo_min, eclipse)
        self.atualizar_temperaturas(modulos, eclipse)
        self.injetar_anomalias(modulos, eclipse)
        self.calcular_consumo(modulos)
        t = self.tempo_min
        self.tempo_min += config.PASSO_TEMPO_MIN
        return t, eclipse, irr


def criar_modulos_iniciais() -> List[EstadoModulo]:
    """Instancia os módulos da missão a partir da configuração."""
    modulos = []
    for espec in config.MODULOS_MISSAO:
        modulos.append(EstadoModulo(
            nome=espec.nome,
            critico=espec.critico,
            pode_reduzir=espec.pode_reduzir,
            potencia_nominal_w=espec.potencia_nominal_w,
            temp_base=espec.temp_base,
            temperatura=espec.temp_base,
        ))
    return modulos
