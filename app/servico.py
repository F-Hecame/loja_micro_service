"""Regras de negócio da loja para uso pela API HTTP (api.py).

Reaproveita os mesmos arquivos da CLI (produtos_local.txt e Pedidos.txt) e
mantém o formato deles: cada linha de Pedidos.txt é "datahora;[{...itens...}]",
com um item repetido por unidade. Os dados do cliente vão como chaves extras
("cliente", "cpf") em cada item, que a CLI ignora ao somar o pagamento.
"""
import json
import math
import re
import threading
from datetime import datetime

from app.cli import cadastros
from app.cli import catalogo
from app import manipulacaoArquivos

PRECO_PROMOCAO = 60
QTD_MAXIMA = 999
METODOS_PAGAMENTO = {"crédito": "crédito", "credito": "crédito", "débito": "débito", "debito": "débito", "dinheiro": "dinheiro"}

# A persistência é em arquivo, então escritas (ler-alterar-gravar) precisam ser serializadas.
_trava = threading.Lock()


class ErroApi(Exception):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


def cpf_valido(valor):
    d = re.sub(r"\D", "", valor)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        if (soma * 10) % 11 % 10 != int(d[n]):
            return False
    return True


def _formatar_cpf(valor):
    d = re.sub(r"\D", "", valor)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


# ---------- produtos ----------

def listar_produtos(origem=None, promocao=False):
    if origem not in (None, "api", "local"):
        raise ErroApi(422, "origem deve ser 'api' ou 'local'.")

    produtos = []
    api_disponivel = True
    if origem in (None, "api"):
        externos = catalogo.buscar_produtos_api()
        api_disponivel = bool(externos)
        produtos += [{**p, "origem": "api"} for p in externos]
    if origem in (None, "local"):
        produtos += [{**p, "origem": "local"} for p in manipulacaoArquivos.lerProdutosLocais()]
    if promocao:
        produtos = [p for p in produtos if p["price"] < PRECO_PROMOCAO]
    return {"produtos": produtos, "api_externa_disponivel": api_disponivel}


def _validar_produto(dados):
    if not isinstance(dados, dict):
        raise ErroApi(400, "Corpo da requisição deve ser um objeto JSON.")

    title = dados.get("title")
    description = dados.get("description", "")
    price = dados.get("price")

    if not isinstance(title, str) or not title.strip():
        raise ErroApi(422, "Informe o nome (title).")
    if not isinstance(description, str):
        raise ErroApi(422, "description deve ser texto.")
    if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price < 0:
        raise ErroApi(422, "price deve ser um número maior ou igual a zero.")

    title, description = title.strip(), description.strip()
    if len(title) > 120 or len(description) > 500:
        raise ErroApi(422, "Nome (máx. 120) ou descrição (máx. 500) longos demais.")
    # ';' e quebras de linha quebrariam o formato de produtos_local.txt
    for texto in (title, description):
        if ";" in texto or "\n" in texto or "\r" in texto:
            raise ErroApi(422, "Nome e descrição não podem conter ';' nem quebras de linha.")
    return title, float(price), description


def criar_produto(dados):
    title, price, description = _validar_produto(dados)
    with _trava:
        id_ = cadastros.gerar_id_produto()
        manipulacaoArquivos.gravarProdutoFakeStore(id_, title, price, description)
    return {"id": id_, "title": title, "price": price, "description": description, "origem": "local"}


def atualizar_produto(id_, dados):
    title, price, description = _validar_produto(dados)
    with _trava:
        produtos = manipulacaoArquivos.lerProdutosLocais()
        produto = next((p for p in produtos if p["id"] == id_), None)
        if not produto:
            raise ErroApi(404, "Produto local não encontrado.")
        produto.update(title=title, price=price, description=description)
        manipulacaoArquivos.reescreverProdutosLocais(produtos)
    return {**produto, "origem": "local"}


def excluir_produto(id_):
    with _trava:
        produtos = manipulacaoArquivos.lerProdutosLocais()
        if not any(p["id"] == id_ for p in produtos):
            raise ErroApi(404, "Produto local não encontrado.")
        manipulacaoArquivos.reescreverProdutosLocais([p for p in produtos if p["id"] != id_])


# ---------- pedidos ----------

def _montar_pedido(linha):
    datahora, resto = linha.split(";", 1)
    unidades = json.loads(resto)
    itens = {}
    for u in unidades:
        item = itens.setdefault(u["id"], {"id": u["id"], "nome": u["nome"], "preco": float(u["preco"]), "qtd": 0})
        item["qtd"] += 1
    primeiro = unidades[0] if unidades else {}
    return {
        "id": datahora,
        "criado_em": datahora,
        # pedidos criados pela CLI não guardam o cliente
        "cliente": {"nome": primeiro.get("cliente"), "cpf": primeiro.get("cpf")},
        "itens": list(itens.values()),
        "total": round(sum(i["preco"] * i["qtd"] for i in itens.values()), 2),
    }


def listar_pedidos():
    pedidos = []
    for linha in manipulacaoArquivos.lerLinhasPedidos():
        try:
            pedidos.append(_montar_pedido(linha))
        except (ValueError, KeyError, TypeError):
            continue  # linha corrompida: ignora em vez de derrubar a listagem
    return {"pedidos": pedidos, "total": round(sum(p["total"] for p in pedidos), 2)}


def criar_pedido(dados):
    if not isinstance(dados, dict):
        raise ErroApi(400, "Corpo da requisição deve ser um objeto JSON.")

    cliente = dados.get("cliente")
    if not isinstance(cliente, dict):
        raise ErroApi(422, "Informe o cliente (nome e cpf).")
    nome, cpf = cliente.get("nome"), cliente.get("cpf")
    if not isinstance(nome, str) or not nome.strip() or len(nome.strip()) > 100:
        raise ErroApi(422, "Informe o nome do cliente (máx. 100 caracteres).")
    if not isinstance(cpf, str) or not cpf_valido(cpf):
        raise ErroApi(422, "CPF inválido.")

    itens = dados.get("itens")
    if not isinstance(itens, list) or not itens:
        raise ErroApi(422, "O pedido precisa ter ao menos um item.")
    quantidades = {}
    for item in itens:
        id_ = item.get("id") if isinstance(item, dict) else None
        qtd = item.get("qtd") if isinstance(item, dict) else None
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (id_, qtd)) or not 1 <= qtd <= QTD_MAXIMA:
            raise ErroApi(422, f"Cada item precisa de id e qtd inteiros (qtd de 1 a {QTD_MAXIMA}).")
        quantidades[id_] = quantidades.get(id_, 0) + qtd

    # preço e nome vêm sempre do servidor, nunca do cliente
    produtos = {p["id"]: p for p in manipulacaoArquivos.lerProdutosLocais()}
    if any(id_ not in produtos for id_ in quantidades):
        produtos.update({p["id"]: p for p in catalogo.buscar_produtos_api()})
    ausentes = [id_ for id_ in quantidades if id_ not in produtos]
    if ausentes:
        raise ErroApi(422, f"Produto(s) não encontrado(s): {', '.join(map(str, ausentes))}.")

    cliente_gravado = {"cliente": nome.strip(), "cpf": _formatar_cpf(cpf)}
    unidades = [
        {"id": id_, "nome": produtos[id_]["title"], "preco": produtos[id_]["price"], **cliente_gravado}
        for id_, qtd in quantidades.items()
        for _ in range(qtd)
    ]
    datahora = datetime.now().isoformat()
    with _trava:
        manipulacaoArquivos.gravarLinhaPedido(datahora, unidades)
    return _montar_pedido(f"{datahora};{json.dumps(unidades)}")


# ---------- pagamentos ----------

def pagar(dados):
    metodo = METODOS_PAGAMENTO.get(str(dados.get("metodo", "")).strip().lower()) if isinstance(dados, dict) else None
    if not metodo:
        raise ErroApi(422, "metodo deve ser 'crédito', 'débito' ou 'dinheiro'.")

    with _trava:
        resumo = listar_pedidos()
        if not resumo["pedidos"]:
            raise ErroApi(409, "Nenhum pedido pendente para pagar.")
        manipulacaoArquivos.limparPedidos()
    return {"total": resumo["total"], "metodo": metodo, "pedidos_quitados": len(resumo["pedidos"])}
