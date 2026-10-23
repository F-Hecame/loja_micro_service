import pytest
from app.cli.catalogo import buscar_produtos_api

@pytest.mark.unitarios
def test_buscar_produtos_api_sucesso(mocker):
    """
    Testa o cenário onde a API responde com sucesso (status 200).
    """
    mock_resposta_api = [
        {"id": 1, "title": "Produto Falso 1", "price": 50.0},
        {"id": 2, "title": "Produto Falso 2", "price": 150.0}
    ]

    mock_response = mocker.Mock()
    mock_response.json.return_value = mock_resposta_api 
    mock_response.raise_for_status.return_value = None 

    mocker.patch('app.cli.catalogo.requests.get', return_value=mock_response)

    resultado = buscar_produtos_api()

    assert resultado == mock_resposta_api
    print("\n✅ Teste de mock do catálogo executado com sucesso!")