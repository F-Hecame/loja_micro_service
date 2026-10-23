from app.cli import menu_principal
from app import manipulacaoArquivos
import atexit

# Limpeza automática ao sair do programa
atexit.register(manipulacaoArquivos.apagarArquivosTemporarios)

if __name__ == "__main__":
    menu_principal.exibir_menu_principal()
