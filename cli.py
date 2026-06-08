"""
cli.py
======
Painel de monitoramento HELIOS no TERMINAL.

Executa a missão simulada por um número de ciclos e exibe, a cada passo, um
painel organizado com: indicadores de energia, estado dos módulos, alertas
ativos e decisões automatizadas. Funciona em qualquer ambiente com Python
(não exige navegador), sendo a opção mais simples para demonstração.

Uso:
    python cli.py                 # 30 ciclos, com pausa entre eles (modo demo)
    python cli.py --ciclos 60     # define o nº de ciclos
    python cli.py --rapido        # sem pausa entre ciclos
    python cli.py --csv saida.csv # exporta a telemetria para CSV ao final
"""

import argparse
import time

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

from src.monitor import MonitorMissao
from src.modelos import Severidade, StatusOperacional, StatusComunicacao

console = Console()

COR_SAUDE = {"NOMINAL": "bold green", "ATENCAO": "bold yellow", "CRITICO": "bold red"}
COR_SEV = {Severidade.INFO: "cyan", Severidade.ATENCAO: "yellow", Severidade.CRITICO: "red"}


def barra(pct: float, largura: int = 20) -> str:
    """Desenha uma barra de progresso em texto (ex.: bateria)."""
    cheios = int(round(pct / 100 * largura))
    return "█" * cheios + "░" * (largura - cheios)


def painel_energia(leitura) -> Panel:
    """Painel com os indicadores energéticos principais."""
    fase = "ECLIPSE (sem Sol)" if leitura.em_eclipse else "ILUMINADO (gerando)"
    cor_soc = "green" if leitura.soc_pct > 35 else ("yellow" if leitura.soc_pct > 20 else "red")
    aut = "estavel/carregando" if leitura.autonomia_h >= 999 else f"{leitura.autonomia_h*60:.0f} min"

    txt = Text()
    txt.append(f"Fase orbital : {fase}\n")
    txt.append(f"Geracao solar: {leitura.geracao_w:>7.1f} W   (renovavel)\n", style="green")
    txt.append(f"Consumo total: {leitura.consumo_total_w:>7.1f} W\n")
    estilo_liq = "green" if leitura.potencia_liquida_w >= 0 else "red"
    txt.append(f"Saldo energ. : {leitura.potencia_liquida_w:>7.1f} W\n", style=estilo_liq)
    txt.append(f"Bateria SoC  : {leitura.soc_pct:>5.1f}%  ", style=cor_soc)
    txt.append(f"{barra(leitura.soc_pct)}\n", style=cor_soc)
    txt.append(f"Autonomia    : {aut}\n")
    txt.append(f"Sustentab.   : {leitura.indice_sustentabilidade:.1f}%\n", style="green")
    txt.append(f"Saude (IA)   : {leitura.saude_geral}  (risco {leitura.risco_pct:.0f}/100)",
               style=COR_SAUDE.get(leitura.saude_geral, "white"))
    return Panel(txt, title="[bold]ENERGIA & SUSTENTABILIDADE[/bold]", border_style="blue")


def tabela_modulos(leitura) -> Table:
    """Tabela com o estado de cada módulo da missão."""
    t = Table(title="MODULOS DA MISSAO", expand=True)
    t.add_column("Modulo", no_wrap=True)
    t.add_column("Status", justify="center")
    t.add_column("Consumo", justify="right")
    t.add_column("Temp", justify="right")
    t.add_column("Comm", justify="center")
    t.add_column("Crit.", justify="center")

    cor_status = {
        StatusOperacional.NOMINAL: "green",
        StatusOperacional.REDUZIDO: "yellow",
        StatusOperacional.DESLIGADO: "bright_black",
        StatusOperacional.FALHA: "red",
    }
    cor_comm = {
        StatusComunicacao.ONLINE: "green",
        StatusComunicacao.DEGRADADA: "yellow",
        StatusComunicacao.OFFLINE: "red",
    }
    for m in leitura.modulos:
        temp_cor = "red" if m.temperatura >= 70 else ("yellow" if m.temperatura >= 55 else "white")
        t.add_row(
            m.nome,
            Text(m.status.value, style=cor_status[m.status]),
            f"{m.consumo_w:.0f} W",
            Text(f"{m.temperatura:.0f} C", style=temp_cor),
            Text(m.comunicacao.value, style=cor_comm[m.comunicacao]),
            "SIM" if m.critico else "-",
        )
    return t


def painel_alertas(leitura) -> Panel:
    """Painel com os alertas ativos no instante."""
    if not leitura.alertas:
        corpo = Text("Nenhum alerta ativo — operacao nominal.", style="green")
    else:
        corpo = Text()
        for a in leitura.alertas:
            corpo.append(f"[{a.severidade.value}] ", style=COR_SEV[a.severidade])
            corpo.append(f"{a.origem}: {a.mensagem}\n")
    return Panel(corpo, title="[bold]ALERTAS AUTOMATICOS[/bold]", border_style="red")


def painel_decisoes(leitura) -> Panel:
    """Painel com as decisões automatizadas tomadas no instante."""
    if not leitura.decisoes:
        corpo = Text("Sem acoes — sistema estavel.", style="bright_black")
    else:
        corpo = Text()
        for d in leitura.decisoes:
            corpo.append(f"> {d.acao}\n", style="bold cyan")
            corpo.append(f"  motivo: {d.motivo}\n", style="cyan")
    return Panel(corpo, title="[bold]DECISOES AUTOMATIZADAS[/bold]", border_style="cyan")


def render(leitura):
    console.rule(f"[bold]HELIOS  |  T+{leitura.instante_min:.0f} min  |  "
                 f"Saude: [{COR_SAUDE.get(leitura.saude_geral)}]{leitura.saude_geral}[/]")
    console.print(Columns([painel_energia(leitura), painel_alertas(leitura)], expand=True))
    console.print(tabela_modulos(leitura))
    console.print(painel_decisoes(leitura))
    console.print()


def exportar_csv(historico, caminho):
    import csv
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t_min", "eclipse", "irradiancia", "geracao_w", "consumo_w",
                    "saldo_w", "soc_pct", "autonomia_h", "sustentabilidade",
                    "saude", "risco", "n_alertas", "n_decisoes"])
        for l in historico:
            w.writerow([l.instante_min, l.em_eclipse, l.irradiancia_w_m2,
                        l.geracao_w, l.consumo_total_w, l.potencia_liquida_w,
                        l.soc_pct, l.autonomia_h, l.indice_sustentabilidade,
                        l.saude_geral, l.risco_pct, len(l.alertas), len(l.decisoes)])
    console.print(f"[green]Telemetria exportada para {caminho}[/green]")


def main():
    ap = argparse.ArgumentParser(description="HELIOS - Monitor energetico de missao espacial")
    ap.add_argument("--ciclos", type=int, default=45, help="numero de ciclos a simular")
    ap.add_argument("--rapido", action="store_true", help="sem pausa entre ciclos")
    ap.add_argument("--csv", type=str, default=None, help="exportar telemetria ao final")
    ap.add_argument("--soc", type=float, default=None,
                    help="estado de carga inicial em %% (ex.: --soc 25 para cenario critico)")
    args = ap.parse_args()

    console.print(Panel.fit(
        "[bold cyan]HELIOS[/bold cyan]\n"
        "Hub de Energia, Logistica Inteligente e Operacoes Sustentaveis\n"
        "[white]Monitoramento de Sistemas Energeticos | Missao Espacial Experimental[/white]",
        border_style="cyan"))

    from src import config as _cfg
    soc_inicial = (args.soc / 100.0) * _cfg.CAPACIDADE_BATERIA_WH if args.soc else None
    monitor = MonitorMissao(soc_inicial_wh=soc_inicial)
    for _ in range(args.ciclos):
        leitura = monitor.proxima_leitura()
        render(leitura)
        if not args.rapido:
            time.sleep(0.6)

    # Resumo final
    crit = sum(1 for l in monitor.historico for a in l.alertas
               if a.severidade == Severidade.CRITICO)
    dec = sum(len(l.decisoes) for l in monitor.historico)
    console.print(Panel.fit(
        f"Ciclos simulados : {len(monitor.historico)}\n"
        f"Alertas criticos : {crit}\n"
        f"Decisoes tomadas : {dec}\n"
        f"SoC final        : {monitor.historico[-1].soc_pct:.1f}%",
        title="RESUMO DA MISSAO", border_style="green"))

    if args.csv:
        exportar_csv(monitor.historico, args.csv)


if __name__ == "__main__":
    main()
