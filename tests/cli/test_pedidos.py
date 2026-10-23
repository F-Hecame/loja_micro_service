import pytest
from app.cli import pedidos
from app import manipulacaoArquivos
from app.cli import interface
from unittest.mock import ANY
from datetime import datetime

@pytest.mark.unitario_pedidos_adicionar
def test_adicionar_pedido(mocker):
    """

    Testa o cenário de adicionar um pedido.

    """

    mocker.patch('app.cli.pedidos.listaPedido', [])

    # 2. Simulamos a resposta da API e dos ficheiros locais
    produtos_api_falsos = [
        {"id": 1, "title": "Produto API A", "price": 10.0},
        {"id": 2, "title": "Produto API B", "price": 20.0} # Vamos escolher este
    ]
    produtos_locais_falsos = [{"id": 101, "title": "Produto Local", "price": 15.0}]
    
    # Mock para a chamada de rede
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = produtos_api_falsos
    mocker.patch('app.cli.pedidos.requests.get', return_value=mock_response)
    
    # Mock para a leitura de ficheiro local
    mocker.patch('app.manipulacaoArquivos.lerProdutosLocais', return_value=produtos_locais_falsos)

    # 3. Simulamos o input do utilizador a escolher o produto com ID 2
    mocker.patch('builtins.input', side_effect=['2'])

    # 4. Mocks para as funções de interface
    mocker.patch('app.cli.interface.limpar_tela')
    mocker.patch('app.cli.interface.mostrar_tabela_produtos')
    mock_mensagem_sucesso = mocker.patch('app.cli.interface.mensagem_sucesso')
    mocker.patch('app.cli.interface.pausar')

    # --- ACT ---
    pedidos.adicionar_pedido()

    # --- ASSERT ---
    # Verifica se a lista tem o produto escolhido
    assert len(pedidos.listaPedido) == 1
    assert pedidos.listaPedido[0] == (2, "Produto API B", 20.0)
    mock_mensagem_sucesso.assert_called_once_with("✅ Produto adicionado ao pedido.")

    print("\n✅ Teste adicionar pedido passou com sucesso!")

@pytest.mark.unitario_pedidos_fechar
def test_fechar_pedido(mocker):
    """
    Testa o cenário de fechar um pedido.

    """
    # --- ARRANGE (Preparar o Cenário) ---

    # 1. Preparamos uma lista de pedidos falsa
    pedido_falso_em_andamento = [
        (1, 'Produto A', 10.0),
        (2, 'Produto B', 20.50)
    ]
    # Forçar a variável global a ter este valor no início do teste.
    mocker.patch('app.cli.pedidos.listaPedido', pedido_falso_em_andamento)

    # 2. Simular o input do utilizador para o nome e CPF.
    mocker.patch('builtins.input', side_effect=['Cliente Teste', '123.456.789-00'])

    # 3. Mockar a data e hora.
    timestamp_falso = datetime(2025, 8, 19, 17, 30, 0) 
    mock_datetime = mocker.patch('app.cli.pedidos.datetime') 
    mock_datetime.now.return_value = timestamp_falso 

    # 4. Preparamos o nosso espião para a função que grava no ficheiro.
    mock_gravar = mocker.patch('app.manipulacaoArquivos.gravarPedidos')

    # 5. Mocks para as funções de interface.
    mocker.patch('app.cli.interface.limpar_tela')
    mocker.patch('app.cli.interface.mensagem_sucesso')
    mocker.patch('app.cli.interface.pausar')

    # --- ACT (Executar a Ação) ---
    pedidos.fechar_pedido()

    # --- ASSERT (Verificar os Resultados) ---

    # 1. Verificar se a função de gravar foi chamada com os dados corretos.
    mock_gravar.assert_called_once_with(pedido_falso_em_andamento, timestamp_falso)

    # 2. Verificar se a lista de pedidos foi limpa após o fecho.
    assert pedidos.listaPedido == []

    print("\n✅ Teste fechar pedido passou com sucesso!")

@pytest.mark.unitario_pedidos_remover_item
def test_remover_item_pedido(mocker):
    """

    Testa o cenário de remover um item do pedido.

    """

    # --- ARRANGE (Preparar o Cenário) ---

    # 1. Preparamos uma lista de pedidos com dois itens.
    pedido_falso_com_dois_itens = [
        (1, 'Produto A', 10.0),
        (2, 'Produto B', 20.0)  # <-- Este será removido
    ]
    mocker.patch('app.cli.pedidos.listaPedido', pedido_falso_com_dois_itens)

    # 2. Simula o input do utilizador.
    mocker.patch('builtins.input', return_value='2')

    # 3. Mocks para as funções de interface.
    mocker.patch('app.cli.interface.limpar_tela')
    mocker.patch('app.cli.interface.mostrar_tabela_pedidos')
    mock_mensagem_sucesso = mocker.patch('app.cli.interface.mensagem_sucesso')
    mocker.patch('app.cli.interface.pausar')


    # --- ACT (Executar a Ação) ---
    pedidos.remover_item_pedido()


    # --- ASSERT (Verificar os Resultados) ---

    # 1. Verifica se a lista de pedidos agora tem apenas um item.
    assert len(pedidos.listaPedido) == 1

    # 2. Verifica se o item que sobrou é o Produto A.
    assert pedidos.listaPedido[0] == (1, 'Produto A', 10.0)

    # 3. Verifica se a mensagem de sucesso correta foi mostrada.
    mock_mensagem_sucesso.assert_called_once_with("✅ Item removido: Produto B")

    print("\n✅ Teste remover item do pedido passou com sucesso!")

@pytest.mark.unitario_pedidos_listar
def test_listar_pedido(mocker):
    """

    Testa o cenário de listar o pedido.

    """

    # --- ARRANGE ---
    # 1. Preparar uma lista de pedidos com alguns itens.
    pedido_falso = [
        (1, 'Produto A', 10.0),
        (2, 'Produto B', 20.0)
    ]
    mocker.patch('app.cli.pedidos.listaPedido', pedido_falso)

    # 2. Preparar as duas funções de interface que podem ser chamadas.
    mock_mostrar_tabela = mocker.spy(interface, 'mostrar_tabela_pedidos')
    mock_mensagem_alerta = mocker.patch('app.cli.interface.mensagem_alerta')

    # Mock para a função de pausa no final.
    mocker.patch('app.cli.interface.pausar')
    mocker.patch('app.cli.interface.limpar_tela')

    # --- ACT ---
    pedidos.listar_pedidos()

    # --- ASSERT ---
    # 1. Verifica se a função para MOSTRAR A TABELA foi chamada com a lista falsa.
    mock_mostrar_tabela.assert_called_once_with(pedido_falso)

    # 2. Verifica se a função de MENSAGEM DE ALERTA (para lista vazia) NÃO foi chamada.
    mock_mensagem_alerta.assert_not_called()
    
    interface.mostrar_tabela_pedidos(pedido_falso)
    print("\n✅ Teste Listar Pedido passou com sucesso!")
