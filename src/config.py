"""
config.py
=========
Parâmetros centrais do sistema HELIOS.

Aqui ficam concentradas todas as constantes físicas, as definições dos
módulos da missão e os limiares (thresholds) usados na geração de alertas.
Centralizar a configuração facilita a manutenção e deixa o resto do código
livre de "números mágicos".

Conceitos de energia/potência aplicados:
- Constante solar (irradiância média recebida na órbita da Terra).
- Geração fotovoltaica (fonte de energia RENOVÁVEL da missão).
- Capacidade de armazenamento da bateria (em Watt-hora).
"""

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# CONSTANTES FÍSICAS / AMBIENTAIS
# ---------------------------------------------------------------------------
CONSTANTE_SOLAR = 1361.0      # W/m^2 — irradiância solar média próxima à Terra
AREA_PAINEL_M2 = 2.0          # m^2  — área total do arranjo de painéis solares
EFICIENCIA_PAINEL = 0.30      # 30%  — eficiência de células solares de uso espacial

# Bateria (armazenamento de energia renovável captada nos painéis)
CAPACIDADE_BATERIA_WH = 2000.0   # Wh — capacidade total de armazenamento
SOC_INICIAL_WH = 1200.0          # Wh — carga inicial (60%, missão em andamento)

# Dinâmica orbital simulada
PERIODO_ORBITAL_MIN = 90.0    # min — período de uma órbita
FRACAO_ECLIPSE = 0.38         # ~38% da órbita na sombra da Terra (sem Sol)
PASSO_TEMPO_MIN = 3.0         # min — duração de cada "tick" da simulação

# ---------------------------------------------------------------------------
# LIMIARES DE ALERTA (usados pelo motor de alertas e de decisão)
# ---------------------------------------------------------------------------
# Estado de carga da bateria (State of Charge)
SOC_ATENCAO_PCT = 35.0        # abaixo disso: ATENÇÃO
SOC_CRITICO_PCT = 20.0        # abaixo disso: CRÍTICO (aciona corte de carga)
SOC_EMERGENCIA_PCT = 10.0     # abaixo disso: modo de sobrevivência

# Temperatura dos equipamentos (°C)
TEMP_MIN_SEGURA = -20.0
TEMP_MAX_ATENCAO = 55.0
TEMP_MAX_CRITICA = 70.0

# Detecção de anomalia por IA (z-score sobre janela móvel)
ZSCORE_ANOMALIA = 2.5         # leituras acima desse desvio são marcadas anômalas
JANELA_IA = 8                 # nº de leituras usadas pela IA (janela móvel)


@dataclass
class EspecModulo:
    """Especificação de um módulo da missão espacial."""
    nome: str
    potencia_nominal_w: float   # consumo nominal em Watts
    critico: bool               # True = não pode ser desligado (suporte à vida etc.)
    pode_reduzir: bool          # True = pode operar em potência reduzida
    temp_base: float            # temperatura de operação típica (°C)


# Lista dos módulos monitorados na missão.
# A ordem importa para o corte de carga: os NÃO críticos são desligados primeiro.
MODULOS_MISSAO = [
    EspecModulo("Suporte a Vida",      120.0, critico=True,  pode_reduzir=False, temp_base=22.0),
    EspecModulo("Comunicacao",          60.0, critico=True,  pode_reduzir=True,  temp_base=18.0),
    EspecModulo("Navegacao e Controle", 45.0, critico=True,  pode_reduzir=False, temp_base=20.0),
    EspecModulo("Controle Termico",     70.0, critico=True,  pode_reduzir=True,  temp_base=15.0),
    EspecModulo("Propulsao",            80.0, critico=False, pode_reduzir=True,  temp_base=25.0),
    EspecModulo("Carga Cientifica",    150.0, critico=False, pode_reduzir=True,  temp_base=30.0),
]

# Fator de potência quando um módulo opera em modo reduzido (economia de energia)
FATOR_REDUCAO = 0.5
