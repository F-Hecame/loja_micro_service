import pytest
from app.cli import cadastros
from app.cli import interface
from unittest.mock import call

@pytest.mark.unitarios_cadastro
def test_cadastrar_item(mocker):
    """
    Testa o cenário de cadastro de item correto
    """
    mocker.patch('builtins.input', side_effect = ['1', 'TESTE', '25.00', 'TESTE'])
    mocker.patch('app.cli.cadastros.gerar_id_produto', return_value = 123)
    mocker_gravar = mocker.patch('app.manipulacaoArquivos.gravarProdutoFakeStore')
    mocker_mensagem = mocker.patch('app.cli.interface.mensagem_sucesso')
    
    
    mocker.patch('app.cli.interface.pausar')
    mocker.patch('app.cli.interface.titulo')
    mocker.patch('app.cli.interface.limpar_tela')

    cadastros.cadastrar_item()

    mocker_gravar.assert_called_once_with(123, 'TESTE', 25.00, 'TESTE')
    mocker_mensagem.assert_called_once_with("✅ Produto 'TESTE' cadastrado com sucesso.")

    print("\n✅ Teste cadastro passou com sucesso!")

@pytest.mark.unitarios_exclusao
def test_excluir_item(mocker):
    """
    Testa o cenário de exclusao de item já registrado
    """
    lista_falsa = [
    {"id": 1, "title": "Produto A para Excluir", "price": 10.0, "description": "Desc A"},
    {"id": 2, "title": "Produto B para Manter", "price": 20.0, "description": "Desc B"}
    ]
    mocker.patch('app.manipulacaoArquivos.lerProdutosLocais', return_value = lista_falsa)
    mocker.patch('builtins.input', side_effect = ['1', 'S'])
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    mocker.patch('app.cli.interface.limpar_tela')
    mocker.patch('app.cli.interface.titulo')
    mocker.patch('app.cli.interface.mostrar_tabela_produtos')
    mocker.patch('app.cli.interface.mensagem_sucesso')
    mocker.patch('app.cli.interface.pausar')

    cadastros.excluir_item()

    mock_open.assert_called_once_with("produtos_local.txt", "w")

    handle = mock_open()
    handle.write.assert_called_once_with('2;Produto B para Manter;20.0;Desc B\n')

    print("\n✅ Teste exclusao passou com sucesso!")

@pytest.mark.unitarios_editar
def test_editar_item(mocker):
    """
    Testa o cenário de alterar item já registrado
    """
    lista_falsa = [
    {"id": 1, "title": "Produto A para Editar", "price": 10.0, "description": "Desc A"},
    {"id": 2, "title": "Produto B para Manter", "price": 20.0, "description": "Desc B"}
    ]
    mocker.patch('app.manipulacaoArquivos.lerProdutosLocais', return_value = lista_falsa)
    mocker.patch('builtins.input', side_effect = ['1', 'TESTE', '0.0', 'TESTE'])
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    mocker.patch('app.cli.interface.limpar_tela')
    mocker.patch('app.cli.interface.titulo')
    mocker.patch('app.cli.interface.mostrar_tabela_produtos')
    mocker.patch('app.cli.interface.mensagem_sucesso')
    mocker.patch('app.cli.interface.pausar')

    cadastros.editar_item()

    mock_open.assert_called_once_with("produtos_local.txt", "w")

    handle = mock_open()

    chamadas_esperadas = [
        call('1;TESTE;0.0;TESTE\n'),
        call('2;Produto B para Manter;20.0;Desc B\n')
    ]
    
    handle.write.assert_has_calls(chamadas_esperadas)

    print("\n✅ Teste editar passou com sucesso!")

