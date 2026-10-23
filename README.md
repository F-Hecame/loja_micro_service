# Restaurante
Pequeno sistema de Restaurante em python, usando apenas manipulação de arquivos.

O mesmo sistema pode ser usado de duas formas: pela **CLI** (menu no terminal) ou pela **API HTTP**
(usada pelo front-end em [`loja_frontend`](../loja_frontend)). As duas compartilham a camada de
arquivos e os mesmos dados (`produtos_local.txt` e `Pedidos.txt`).

## Estrutura

```
loja.py                     ponto de entrada da CLI
api.py                      ponto de entrada da API
app/
  manipulacaoArquivos.py    leitura e escrita dos arquivos (usada pela CLI e pela API)
  servico.py                regras de negócio e validações da API
  cli/                      interface de terminal
    menu_principal.py         menus
    interface.py              telas e tabelas (rich)
    cadastros.py  catalogo.py  pedidos.py  pagamentos.py
  web/
    servidor.py             servidor HTTP: rotas, JSON e CORS
tests/
  cli/                      testes da CLI (pytest + mocks)
  web/                      testes da API (sobem um servidor real)
```

## Instalação

```bash
pip install -r requirements.txt        # requests e rich
pip install -r requirements-dev.txt    # + pytest e pytest-mock, para os testes
```

Sempre rode os comandos abaixo de dentro desta pasta: os dados ficam no diretório atual.

## CLI

```bash
python3 loja.py
```

Atenção: a CLI apaga `produtos_local.txt` e `Pedidos.txt` ao sair; a API não.

## API HTTP

```bash
python3 api.py     # http://127.0.0.1:8000
```

| Método e rota           | O que faz |
| ----------------------- | --------- |
| `GET /produtos`         | Fake Store API + produtos locais. Filtros: `?origem=api\|local`, `?promocao=true` (preço < 60). Resposta: `{produtos, api_externa_disponivel}` |
| `POST /produtos`        | Cadastra produto local `{title, price, description}` → 201 |
| `PUT /produtos/{id}`    | Edita produto local → 200 (404 se não for local) |
| `DELETE /produtos/{id}` | Exclui produto local → 204 |
| `GET /pedidos`          | Pedidos pendentes de pagamento e o total |
| `POST /pedidos`         | Finaliza pedido `{cliente: {nome, cpf}, itens: [{id, qtd}]}` → 201. Preços vêm do servidor; CPF é validado |
| `POST /pagamentos`      | `{metodo: "crédito"\|"débito"\|"dinheiro"}` quita todos os pedidos pendentes (409 se não houver) |

Erros voltam como `{"erro": "mensagem"}` com o status HTTP adequado (400, 404, 405, 409, 422).

Configuração opcional por variáveis de ambiente: `LOJA_HOST`, `LOJA_PORT` e `LOJA_CORS_ORIGINS`
(origens do front autorizadas; o padrão é o Vite em `localhost:5173` e `:4173`).

## Testes

```bash
python3 -m pytest                          # todos (precisa do requirements-dev.txt)
PYTHONPATH=. python3 tests/web/test_api.py # só a API, sem dependências extras
```

O `tests/cli/test_integracao_api.py` faz uma chamada real à Fake Store API e precisa de internet.
