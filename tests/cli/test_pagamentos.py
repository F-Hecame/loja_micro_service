import pytest
from app.cli import pagamentos
from app.cli import interface
from app import manipulacaoArquivos
from unittest.mock import ANY

@pytest.mark.unitario_pagamento
def test_realizar_pagamento(mocker):
    """
    Testa o cenário de realizar pagamento.

    """
    pedidos_falsos = (
    '2025-08-18;[{"id": 1, "nome": "Produto A", "preco": 10.0}]\n'
    '2025-08-18;[{"id": 2, "nome": "Produto B", "preco": 20.0}, {"id": 3, "nome": "Produto C", "preco": 5.50}]'
    )

    mocker.patch('app.manipulacaoArquivos.lerArquivo', mocker.mock_open(read_data = pedidos_falsos))
    mock_abrir_arquivo = mocker.patch('builtins.open', mocker.mock_open())
    
    mocker.patch('builtins.input', return_value='crédito')
    mock_mensagem_sucesso = mocker.patch('app.cli.interface.mensagem_sucesso')

    mocker.patch('app.cli.interface.limpar_tela')
    mocker.patch('app.cli.interface.titulo')
    mocker.patch('app.cli.interface.pausar')

    pagamentos.realizar_pagamento()
    mock_mensagem_sucesso.assert_any_call("✅ Pagamento de R$ 35.50 realizado via CRÉDITO!")

    mock_abrir_arquivo.assert_called_once_with("Pedidos.txt", "w")

    handle = mock_abrir_arquivo()
    handle.truncate.assert_called_once()

    print("\n✅ O teste de realizar pagamento passou com sucesso")


