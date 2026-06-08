"""
modelos.py
==========
Estruturas de dados do HELIOS.

Usamos `dataclasses` para representar de forma clara e organizada:
- EstadoModulo: situação atual de cada módulo (ligado/desligado, temperatura...).
- Leitura: um "retrato" (snapshot) de toda a telemetria em um instante.
- Alerta: um aviso gerado quando uma condição crítica é detectada.
- Decisao: uma ação automatizada tomada pelo sistema.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Severidade(Enum):
    """Nível de gravidade de um alerta."""
    INFO = "INFO"
    ATENCAO = "ATENCAO"
    CRITICO = "CRITICO"


class StatusOperacional(Enum):
    """Status operacional de um módulo."""
    NOMINAL = "NOMINAL"      # operando normalmente
    REDUZIDO = "REDUZIDO"    # operando em potência reduzida (economia)
    DESLIGADO = "DESLIGADO"  # desligado por decisão automatizada
    FALHA = "FALHA"          # condição de falha detectada


class StatusComunicacao(Enum):
    ONLINE = "ONLINE"
    DEGRADADA = "DEGRADADA"
    OFFLINE = "OFFLINE"


@dataclass
class EstadoModulo:
    """Situação atual de um módulo da missão."""
    nome: str
    critico: bool
    pode_reduzir: bool
    potencia_nominal_w: float
    temp_base: float = 20.0
    ligado: bool = True
    reduzido: bool = False
    temperatura: float = 20.0
    consumo_w: float = 0.0
    status: StatusOperacional = StatusOperacional.NOMINAL
    comunicacao: StatusComunicacao = StatusComunicacao.ONLINE


@dataclass
class Alerta:
    """Aviso automático gerado pelo sistema."""
    severidade: Severidade
    origem: str          # módulo ou subsistema que originou o alerta
    mensagem: str
    instante_min: float


@dataclass
class Decisao:
    """Ação automatizada tomada pelo motor de decisão."""
    acao: str
    motivo: str
    instante_min: float


@dataclass
class Leitura:
    """
    Snapshot completo da telemetria em um instante da missão.
    É a unidade básica que percorre todo o pipeline:
    simulador -> monitor -> IA -> alertas -> decisão -> visualização.
    """
    instante_min: float
    em_eclipse: bool
    irradiancia_w_m2: float
    geracao_w: float                # potência gerada pelos painéis (renovável)
    consumo_total_w: float          # potência consumida por todos os módulos
    potencia_liquida_w: float       # geração - consumo (saldo)
    soc_wh: float                   # energia armazenada na bateria
    soc_pct: float                  # estado de carga (%)
    autonomia_h: float              # horas de autonomia restante (previsão)
    indice_sustentabilidade: float  # % do consumo coberto por energia renovável
    modulos: List[EstadoModulo] = field(default_factory=list)
    alertas: List[Alerta] = field(default_factory=list)
    decisoes: List[Decisao] = field(default_factory=list)
    anomalias: List[str] = field(default_factory=list)
    saude_geral: str = "NOMINAL"     # classificação da IA: NOMINAL/ATENCAO/CRITICO
    risco_pct: float = 0.0           # pontuação de risco da IA (0-100)
