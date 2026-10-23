import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")

def titulo(texto):
    panel = Panel.fit(
        f"[bold cyan]{texto}[/bold cyan]",
        border_style="cyan",
        padding=(1, 4),
        title="🛍️ Nova Loja em Microsserviços",
        subtitle="Tópicos de Eng. de Software"
    )
    console.print(panel)

def mostrar_menu(opcoes, titulo_menu="MENU"):
    limpar_tela()
    titulo(titulo_menu)
    for i, opcao in enumerate(opcoes, 1):
        console.print(f"[green]{i}[/green] - {opcao}")
    console.print("[yellow]Escolha uma opção: [/yellow]", end="")

def mostrar_tabela_produtos(produtos):
    table = Table(title="📦 Produtos Disponíveis", header_style="bold magenta")
    table.add_column("ID", justify="center")
    table.add_column("Nome")
    table.add_column("Preço (R$)", justify="right")

    for p in produtos:
        table.add_row(str(p["id"]), p["title"], f"R$ {p['price']:.2f}")

    console.print(table)

def mostrar_tabela_pedidos(pedidos):
    table = Table(title="🧾 Itens no Pedido", header_style="bold yellow")
    table.add_column("#", justify="center")
    table.add_column("Nome")
    table.add_column("Preço (R$)", justify="right")

    for i, item in enumerate(pedidos, 1):
        table.add_row(str(i), item[1], f"R$ {item[2]:.2f}")

    console.print(table)

def mensagem_alerta(texto):
    console.print(f"[bold red]{texto}[/bold red]")

def mensagem_sucesso(texto):
    console.print(f"[bold green]{texto}[/bold green]")

def pausar():
    console.print("\n[dim]Pressione [bold]Enter[/bold] para continuar...[/dim]")
    input()
