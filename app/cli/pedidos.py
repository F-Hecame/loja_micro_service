from datetime import datetime
from app import manipulacaoArquivos
import requests
import json
from app.cli import interface

listaPedido = []

def menu_pedidos():
    while True:
        opcoes = [
            "Adicionar ao Pedido",
            "Finalizar Pedido",
            "Ver Itens do Pedido",
            "Remover Item do Pedido",
            "Voltar"
        ]
        interface.mostrar_menu(opcoes, "📋 MENU DE PEDIDOS")
        opcao = input()

        if opcao == "1":
            adicionar_pedido()
        elif opcao == "2":
            fechar_pedido()
        elif opcao == "3":
            listar_pedidos()
        elif opcao == "4":
            remover_item_pedido()
        elif opcao == "5":
            break
        else:
            interface.mensagem_alerta("❌ Opção inválida.")
            interface.pausar()

def adicionar_pedido():
    global listaPedido
    interface.limpar_tela()
    try:
        res = requests.get("https://fakestoreapi.com/products")
        produtos_api = res.json() if res.status_code == 200 else []
    except:
        produtos_api = []

    produtos_locais = manipulacaoArquivos.lerProdutosLocais()
    todos = produtos_api + produtos_locais

    interface.mostrar_tabela_produtos(todos)

    try:
        id_produto = int(input("Digite o ID do produto desejado: "))
        produto = next((p for p in todos if p["id"] == id_produto), None)
        if produto:
            listaPedido.append((produto["id"], produto["title"], produto["price"]))
            interface.mensagem_sucesso("✅ Produto adicionado ao pedido.")
        else:
            interface.mensagem_alerta("❌ Produto não encontrado.")
    except ValueError:
        interface.mensagem_alerta("❌ Entrada inválida.")
    interface.pausar()

def fechar_pedido():
    global listaPedido
    interface.limpar_tela()
    if not listaPedido:
        interface.mensagem_alerta("⚠️ Nenhum item no pedido.")
        interface.pausar()
        return

    nome = input("Nome do cliente: ")
    cpf = input("CPF do cliente: ")
    now = datetime.now()
    manipulacaoArquivos.gravarPedidos(listaPedido, now)
    listaPedido = []
    interface.mensagem_sucesso("✅ Pedido finalizado.")
    interface.pausar()

def listar_pedidos():
    interface.limpar_tela()
    if not listaPedido:
        interface.mensagem_alerta("📭 Nenhum item adicionado.")
    else:
        interface.mostrar_tabela_pedidos(listaPedido)
    interface.pausar()

def remover_item_pedido():
    global listaPedido
    interface.limpar_tela()
    if not listaPedido:
        interface.mensagem_alerta("⚠️ Nenhum item no pedido.")
        interface.pausar()
        return

    interface.mostrar_tabela_pedidos(listaPedido)

    try:
        opcao = int(input("Digite o número do item que deseja remover (ou 0 para cancelar): "))
        if opcao == 0:
            interface.mensagem_alerta("❌ Remoção cancelada.")
        elif 1 <= opcao <= len(listaPedido):
            removido = listaPedido.pop(opcao - 1)
            interface.mensagem_sucesso(f"✅ Item removido: {removido[1]}")
        else:
            interface.mensagem_alerta("❌ Número inválido.")
    except ValueError:
        interface.mensagem_alerta("❌ Entrada inválida.")
    interface.pausar()
