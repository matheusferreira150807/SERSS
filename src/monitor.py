"""
monitor.py
==========
MONITOR CENTRAL do HELIOS — orquestra todo o pipeline.

A cada passo de tempo (tick) o monitor executa, em ordem:

    simulador -> energia -> IA -> alertas -> decisao

e devolve um objeto `Leitura` completo, pronto para ser exibido pela CLI ou
pelo painel web. Mantém o estado contínuo da missão (bateria e módulos) entre
os passos.
"""

from typing import List

from . import config, energia
from .alertas import gerar_alertas
from .decisao import decidir
from .ia import CerebroIA
from .modelos import Leitura
from .simulador import SimuladorMissao, criar_modulos_iniciais


class MonitorMissao:
    """Estado vivo da missão + execução do ciclo de monitoramento."""

    def __init__(self, semente: int | None = 42, soc_inicial_wh: float | None = None):
        self.simulador = SimuladorMissao(semente=semente)
        self.cerebro = CerebroIA()
        self.modulos = criar_modulos_iniciais()
        self.soc_wh = soc_inicial_wh if soc_inicial_wh is not None else config.SOC_INICIAL_WH
        self.historico: List[Leitura] = []

    def proxima_leitura(self) -> Leitura:
        """Executa um ciclo completo de monitoramento e retorna a leitura."""
        # 1) SIMULAÇÃO: ambiente + telemetria bruta dos módulos
        t, eclipse, irr = self.simulador.passo(self.modulos)

        # 2) ENERGIA: geração solar, consumo, saldo e bateria
        geracao = energia.geracao_solar(irr, em_eclipse=eclipse)
        consumo = sum(m.consumo_w for m in self.modulos)
        p_liq = energia.potencia_liquida(geracao, consumo)
        self.soc_wh = energia.atualizar_bateria(self.soc_wh, p_liq,
                                                config.PASSO_TEMPO_MIN)
        soc_pct = energia.soc_percentual(self.soc_wh)
        autonomia = energia.autonomia_bateria(self.soc_wh, p_liq)
        sustentab = energia.indice_sustentabilidade(geracao, consumo, soc_pct)

        # 3) IA: anomalias, previsão de autonomia e classificação de saúde
        anomalias = self.cerebro.detectar_anomalias(self.modulos)
        prev_critico = self.cerebro.prever_tempo_ate_critico(soc_pct)
        saude, risco = self.cerebro.avaliar_saude(soc_pct, p_liq,
                                                  self.modulos, len(anomalias))
        if prev_critico is not None and prev_critico < 30:
            anomalias.append(
                f"IA preve nivel critico de bateria em ~{prev_critico:.0f} min")

        # 4) ALERTAS automáticos
        alertas = gerar_alertas(t, soc_pct, p_liq, autonomia,
                                self.modulos, anomalias)

        # 5) DECISÃO automatizada (altera os módulos para o próximo ciclo)
        decisoes = decidir(t, soc_pct, p_liq, self.modulos)

        leitura = Leitura(
            instante_min=t,
            em_eclipse=eclipse,
            irradiancia_w_m2=round(irr, 1),
            geracao_w=round(geracao, 1),
            consumo_total_w=round(consumo, 1),
            potencia_liquida_w=round(p_liq, 1),
            soc_wh=round(self.soc_wh, 1),
            soc_pct=round(soc_pct, 1),
            autonomia_h=autonomia,
            indice_sustentabilidade=sustentab,
            modulos=[self._copiar_modulo(m) for m in self.modulos],
            alertas=alertas,
            decisoes=decisoes,
            anomalias=anomalias,
            saude_geral=saude,
            risco_pct=risco,
        )
        self.historico.append(leitura)
        return leitura

    @staticmethod
    def _copiar_modulo(m):
        """Cópia rasa do estado do módulo para registrar o instante."""
        from .modelos import EstadoModulo
        return EstadoModulo(
            nome=m.nome, critico=m.critico, pode_reduzir=m.pode_reduzir,
            potencia_nominal_w=m.potencia_nominal_w, ligado=m.ligado,
            reduzido=m.reduzido, temperatura=m.temperatura,
            temp_base=m.temp_base,
            consumo_w=m.consumo_w, status=m.status, comunicacao=m.comunicacao,
        )
