"""Servidor HTTP da loja (rotas e CORS). Uso: python3 api.py  (http://127.0.0.1:8000)

Rode a partir desta pasta: os dados ficam em produtos_local.txt e Pedidos.txt
no diretório atual, os mesmos arquivos usados pela CLI (loja.py).

Variáveis de ambiente: LOJA_HOST, LOJA_PORT, LOJA_CORS_ORIGINS (lista separada por vírgula).
"""
import json
import os
import re
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app import servico
from app.servico import ErroApi

ORIGENS_PERMITIDAS = {
    o.strip()
    for o in os.environ.get(
        "LOJA_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
    ).split(",")
    if o.strip()
}
TAMANHO_MAXIMO_CORPO = 1_000_000


def _produtos_get(m, q, corpo):
    promocao = q.get("promocao", ["false"])[0].lower() in ("1", "true", "sim")
    return 200, servico.listar_produtos(origem=q.get("origem", [None])[0], promocao=promocao)


# (método, padrão do caminho, função(match, query, corpo) -> (status, payload))
ROTAS = [
    ("GET", r"/produtos", _produtos_get),
    ("POST", r"/produtos", lambda m, q, c: (201, servico.criar_produto(c))),
    ("PUT", r"/produtos/(\d+)", lambda m, q, c: (200, servico.atualizar_produto(int(m[1]), c))),
    ("DELETE", r"/produtos/(\d+)", lambda m, q, c: (204, servico.excluir_produto(int(m[1])))),
    ("GET", r"/pedidos", lambda m, q, c: (200, servico.listar_pedidos())),
    ("POST", r"/pedidos", lambda m, q, c: (201, servico.criar_pedido(c))),
    ("POST", r"/pagamentos", lambda m, q, c: (200, servico.pagar(c))),
]


class Handler(BaseHTTPRequestHandler):
    server_version = "LojaAPI/1.0"

    def do_GET(self): self._tratar("GET")
    def do_POST(self): self._tratar("POST")
    def do_PUT(self): self._tratar("PUT")
    def do_DELETE(self): self._tratar("DELETE")

    def do_OPTIONS(self):
        self._responder(204, None)

    def _ler_corpo(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > TAMANHO_MAXIMO_CORPO:
            raise ErroApi(413, "Corpo da requisição grande demais.")
        if not tamanho:
            return None
        try:
            return json.loads(self.rfile.read(tamanho))
        except ValueError:
            raise ErroApi(400, "JSON inválido.")

    def _tratar(self, metodo):
        url = urlparse(self.path)
        caminho = url.path.rstrip("/") or "/"
        try:
            casou = False
            for m, padrao, funcao in ROTAS:
                match = re.fullmatch(padrao, caminho)
                if not match:
                    continue
                casou = True
                if m == metodo:
                    status, payload = funcao(match, parse_qs(url.query), self._ler_corpo() if metodo in ("POST", "PUT") else None)
                    return self._responder(status, payload)
            raise ErroApi(405, "Método não permitido.") if casou else ErroApi(404, "Rota não encontrada.")
        except ErroApi as e:
            self._responder(e.status, {"erro": e.mensagem})
        except Exception:
            traceback.print_exc()
            self._responder(500, {"erro": "Erro interno do servidor."})

    def _cabecalhos_cors(self):
        origem = self.headers.get("Origin")
        if origem in ORIGENS_PERMITIDAS:
            self.send_header("Access-Control-Allow-Origin", origem)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Vary", "Origin")

    def _responder(self, status, payload):
        corpo = b"" if payload is None or status == 204 else json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self._cabecalhos_cors()
        if corpo:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def criar_servidor(host="127.0.0.1", porta=8000):
    return ThreadingHTTPServer((host, porta), Handler)


def main():
    host = os.environ.get("LOJA_HOST", "127.0.0.1")
    porta = int(os.environ.get("LOJA_PORT", "8000"))
    servidor = criar_servidor(host, porta)
    print(f"API da loja em http://{host}:{porta}  (dados em {os.getcwd()})", file=sys.stderr)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.", file=sys.stderr)
