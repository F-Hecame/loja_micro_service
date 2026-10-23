import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

from app.web import servidor as api

CPF_OK = "529.982.247-25"
PRODUTOS_API = [
    {"id": 1, "title": "Mochila", "price": 109.95, "description": "d", "category": "x", "image": "i"},
    {"id": 2, "title": "Camiseta", "price": 22.3, "description": "d", "category": "x", "image": "i"},
]


class ApiTestCase(unittest.TestCase):
    """Sobe a API de verdade numa porta livre, num diretório temporário, e fala HTTP com ela."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        patcher = mock.patch("app.cli.catalogo.buscar_produtos_api", return_value=list(PRODUTOS_API))
        self.api_externa = patcher.start()
        self.addCleanup(patcher.stop)
        silencio = mock.patch.object(api.Handler, "log_message", lambda *a, **k: None)
        silencio.start()
        self.addCleanup(silencio.stop)

        self.servidor = api.criar_servidor("127.0.0.1", 0)
        self.base = f"http://127.0.0.1:{self.servidor.server_address[1]}"
        threading.Thread(target=self.servidor.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def req(self, metodo, caminho, corpo=None, headers=None):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        r = urllib.request.Request(self.base + caminho, data=dados, method=metodo, headers=headers or {})
        try:
            with urllib.request.urlopen(r) as resp:
                texto = resp.read()
                return resp.status, (json.loads(texto) if texto else None), resp.headers
        except urllib.error.HTTPError as e:
            texto = e.read()
            return e.code, (json.loads(texto) if texto else None), e.headers

    def novo_produto(self, title="Bife", price=20, description="Com arroz"):
        status, body, _ = self.req("POST", "/produtos", {"title": title, "price": price, "description": description})
        self.assertEqual(status, 201)
        return body


class TestProdutos(ApiTestCase):
    def test_lista_api_e_locais_com_origem(self):
        self.novo_produto()
        status, body, _ = self.req("GET", "/produtos")
        self.assertEqual(status, 200)
        self.assertEqual([p["origem"] for p in body["produtos"]], ["api", "api", "local"])
        self.assertTrue(body["api_externa_disponivel"])

    def test_filtros_origem_e_promocao(self):
        self.novo_produto(price=20)
        self.novo_produto(title="Caro", price=99)
        _, body, _ = self.req("GET", "/produtos?origem=local")
        self.assertEqual([p["title"] for p in body["produtos"]], ["Bife", "Caro"])
        _, body, _ = self.req("GET", "/produtos?promocao=true")
        self.assertEqual([p["title"] for p in body["produtos"]], ["Camiseta", "Bife"])
        self.assertEqual(self.req("GET", "/produtos?origem=xyz")[0], 422)

    def test_api_externa_fora_do_ar_nao_derruba_a_listagem(self):
        self.api_externa.return_value = []
        self.novo_produto()
        _, body, _ = self.req("GET", "/produtos")
        self.assertFalse(body["api_externa_disponivel"])
        self.assertEqual(len(body["produtos"]), 1)

    def test_criar_gera_ids_a_partir_de_21(self):
        self.assertEqual(self.novo_produto()["id"], 21)
        self.assertEqual(self.novo_produto()["id"], 22)

    def test_editar_e_excluir(self):
        p = self.novo_produto()
        status, body, _ = self.req("PUT", f"/produtos/{p['id']}", {"title": "Bife 2", "price": 25.5, "description": "x"})
        self.assertEqual((status, body["title"], body["price"]), (200, "Bife 2", 25.5))
        self.assertEqual(self.req("DELETE", f"/produtos/{p['id']}")[0], 204)
        self.assertEqual(self.req("GET", "/produtos?origem=local")[1]["produtos"], [])

    def test_nao_edita_nem_exclui_produto_da_api_ou_inexistente(self):
        self.assertEqual(self.req("DELETE", "/produtos/1")[0], 404)
        self.assertEqual(self.req("PUT", "/produtos/1", {"title": "x", "price": 1})[0], 404)

    def test_validacao(self):
        for corpo in (
            {"title": "", "price": 1},
            {"title": "ok", "price": -1},
            {"title": "ok", "price": "10"},
            {"title": "ok", "price": True},
            {"title": "a;b", "price": 1},
            {"title": "ok", "price": 1, "description": "linha1\nlinha2"},
        ):
            with self.subTest(corpo=corpo):
                self.assertEqual(self.req("POST", "/produtos", corpo)[0], 422)

    def test_json_invalido_e_rotas_desconhecidas(self):
        r = urllib.request.Request(self.base + "/produtos", data=b"{nope", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(r)
        self.assertEqual(ctx.exception.code, 400)
        self.assertEqual(self.req("GET", "/nada")[0], 404)
        self.assertEqual(self.req("DELETE", "/pedidos")[0], 405)


class TestPedidosEPagamentos(ApiTestCase):
    def pedido(self, itens=None, nome="Ana", cpf=CPF_OK):
        return self.req("POST", "/pedidos", {"cliente": {"nome": nome, "cpf": cpf}, "itens": [{"id": 1, "qtd": 2}] if itens is None else itens})

    def test_criar_pedido_usa_precos_do_servidor_e_agrupa_quantidades(self):
        local = self.novo_produto(price=20)
        status, body, _ = self.pedido([{"id": 2, "qtd": 1}, {"id": local["id"], "qtd": 3}, {"id": 2, "qtd": 1}])
        self.assertEqual(status, 201)
        self.assertEqual(body["cliente"], {"nome": "Ana", "cpf": CPF_OK})
        self.assertEqual({i["id"]: i["qtd"] for i in body["itens"]}, {2: 2, local["id"]: 3})
        self.assertEqual(body["total"], 104.6)
        self.assertEqual(self.req("GET", "/pedidos")[1]["total"], 104.6)

    def test_pedido_invalido(self):
        casos = [
            self.pedido(cpf="111.111.111-11"),
            self.pedido(nome="  "),
            self.pedido(itens=[]),
            self.pedido(itens=[{"id": 1, "qtd": 0}]),
            self.pedido(itens=[{"id": 999, "qtd": 1}]),
        ]
        self.assertEqual([c[0] for c in casos], [422] * 5)
        self.assertEqual(self.req("GET", "/pedidos")[1]["pedidos"], [])

    def test_arquivo_continua_compativel_com_a_cli(self):
        self.pedido([{"id": 1, "qtd": 2}])
        with open("Pedidos.txt") as f:
            linha = f.read().strip()
        datahora, resto = linha.split(";", 1)
        self.assertEqual(sum(float(i["preco"]) for i in json.loads(resto)), 219.9)  # mesma soma de pagamentos.py

    def test_pagamento_quita_todos_os_pedidos(self):
        self.pedido([{"id": 1, "qtd": 1}])
        self.pedido([{"id": 2, "qtd": 1}])
        status, body, _ = self.req("POST", "/pagamentos", {"metodo": "Crédito"})
        self.assertEqual((status, body), (200, {"total": 132.25, "metodo": "crédito", "pedidos_quitados": 2}))
        self.assertEqual(self.req("GET", "/pedidos")[1], {"pedidos": [], "total": 0})

    def test_pagamento_sem_pedidos_ou_metodo_invalido(self):
        self.assertEqual(self.req("POST", "/pagamentos", {"metodo": "dinheiro"})[0], 409)
        self.pedido()
        self.assertEqual(self.req("POST", "/pagamentos", {"metodo": "pix"})[0], 422)
        self.assertEqual(len(self.req("GET", "/pedidos")[1]["pedidos"]), 1)


class TestCors(ApiTestCase):
    def test_origem_permitida_recebe_cabecalho_e_preflight_funciona(self):
        origem = {"Origin": "http://localhost:5173"}
        status, _, h = self.req("OPTIONS", "/produtos", headers=origem)
        self.assertEqual(status, 204)
        self.assertEqual(h["Access-Control-Allow-Origin"], "http://localhost:5173")

    def test_origem_desconhecida_nao_recebe_cabecalho(self):
        _, _, h = self.req("GET", "/produtos", headers={"Origin": "http://evil.example"})
        self.assertIsNone(h["Access-Control-Allow-Origin"])


if __name__ == "__main__":
    unittest.main()
