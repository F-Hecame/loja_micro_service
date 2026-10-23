import requests
from app import manipulacaoArquivos
from app.cli import interface

def buscar_produtos_api():
    try:
        res = requests.get("https://fakestoreapi.com/products")
        res.raise_for_status()
        return res.json()
    except:
        return []
    
def exibir_catalogo():
    interface.limpar_tela()
    interface.titulo("🛍️ CATÁLOGO DE PRODUTOS")
    promocao = input("Deseja ver o catálogo promocional (preço < R$60)? [S/N]: ").strip().upper()

    produtos_api = buscar_produtos_api()
    if not produtos_api:
        interface.mensagem_alerta("❌ Erro ao acessar a Fake Store API.")

    produtos_locais = manipulacaoArquivos.lerProdutosLocais()
    todos_produtos = produtos_api + produtos_locais

    if not todos_produtos:
        interface.mensagem_alerta("Nenhum produto para exibir.")
        interface.pausar()
        return
    
    filtrados = [p for p in todos_produtos if p["price"] < 60] if promocao == "S" else todos_produtos

    interface.mostrar_tabela_produtos(filtrados)
    interface.pausar()
