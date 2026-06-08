"""
energia.py
==========
Núcleo de ENERGIA, POTÊNCIA, ENERGIAS RENOVÁVEIS e SUSTENTABILIDADE.

Este é o coração científico do HELIOS. Todas as fórmulas físicas que
sustentam o monitoramento energético da missão estão aqui, isoladas e
testáveis. É aqui que o tema da disciplina (energias renováveis e
sustentáveis) se traduz em código.

Fundamentos:
  Potência (P)      -> taxa de transferência de energia, medida em Watts (W).
  Energia (E)       -> E = P x t, medida em Watt-hora (Wh) quando t está em horas.
  Geração solar     -> P_ger = Irradiância x Área x Eficiência  (fonte RENOVÁVEL).
  Bateria (SoC)     -> energia armazenada / capacidade total (estado de carga).
  Saldo energético  -> P_liq = P_ger - P_consumo.
  Sustentabilidade  -> fração do consumo coberta por energia renovável.
"""

from . import config


def geracao_solar(irradiancia: float, area: float = config.AREA_PAINEL_M2,
                  eficiencia: float = config.EFICIENCIA_PAINEL,
                  em_eclipse: bool = False) -> float:
    """
    Calcula a potência elétrica gerada pelos painéis solares (em Watts).

        P_gerada = Irradiância (W/m^2) x Área (m^2) x Eficiência

    Durante o eclipse (a nave passa pela sombra da Terra) não há luz solar,
    logo a geração renovável é zero e a missão depende 100% da bateria.
    """
    if em_eclipse:
        return 0.0
    return irradiancia * area * eficiencia


def energia_wh(potencia_w: float, tempo_min: float) -> float:
    """
    Converte potência (W) e um intervalo de tempo (min) em energia (Wh).

        E = P x t      (t convertido de minutos para horas)
    """
    return potencia_w * (tempo_min / 60.0)


def potencia_liquida(geracao_w: float, consumo_w: float) -> float:
    """Saldo energético instantâneo: geração - consumo (positivo = sobra)."""
    return geracao_w - consumo_w


def atualizar_bateria(soc_wh: float, p_liquida_w: float, tempo_min: float,
                      capacidade_wh: float = config.CAPACIDADE_BATERIA_WH) -> float:
    """
    Atualiza a energia armazenada na bateria após um intervalo de tempo.

    Se houver sobra de energia (P_liq > 0) a bateria CARREGA;
    se houver déficit (P_liq < 0) a bateria DESCARREGA.
    O resultado é limitado entre 0 e a capacidade máxima.

        novo_SoC = SoC + (P_liq x t)
    """
    delta = energia_wh(p_liquida_w, tempo_min)
    novo = soc_wh + delta
    return max(0.0, min(capacidade_wh, novo))


def soc_percentual(soc_wh: float,
                   capacidade_wh: float = config.CAPACIDADE_BATERIA_WH) -> float:
    """Estado de carga da bateria em porcentagem (0-100%)."""
    return (soc_wh / capacidade_wh) * 100.0


def indice_sustentabilidade(geracao_w: float, consumo_w: float,
                            soc_pct: float) -> float:
    """
    Índice de Sustentabilidade Energética (0-100%).

    Mede o quanto a missão está sendo alimentada por energia RENOVÁVEL
    (painéis solares) em vez de drenar a reserva da bateria. Combina:
      - cobertura renovável instantânea (geração / consumo);
      - bônus pela reserva de energia disponível na bateria.

    É a métrica que traduz "sustentabilidade" em um número monitorável.
    """
    if consumo_w <= 0:
        cobertura = 1.0
    else:
        cobertura = min(1.0, geracao_w / consumo_w)
    # 70% do índice vem da cobertura renovável e 30% da reserva armazenada.
    indice = (0.7 * cobertura + 0.3 * (soc_pct / 100.0)) * 100.0
    return round(indice, 1)


def autonomia_bateria(soc_wh: float, p_liquida_w: float) -> float:
    """
    Estima a autonomia restante da bateria, em HORAS.

    - Se o saldo é positivo (carregando), a autonomia é "infinita" -> retorna
      um valor alto simbólico (999).
    - Se há déficit, calcula quanto tempo a energia armazenada dura:

          autonomia = energia_disponivel / potencia_de_deficit
    """
    if p_liquida_w >= 0:
        return 999.0
    deficit = abs(p_liquida_w)
    if deficit == 0:
        return 999.0
    return round(soc_wh / deficit, 2)
