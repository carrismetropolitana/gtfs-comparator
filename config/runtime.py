"""

Este módulo gere a configuração global da aplicação durante a execução.
Permite iniciar a configuração uma única vez e aceder aos seus valores a partir de qualquer ponto do código, 
garantindo que a configuração é explicitamente definida antes de ser utilizada.

"""

# ========================================================================================================================================================
# Inicia a None para garantir que a configuração é inicializada explicitamente
# ========================================================================================================================================================

_config = None

# ========================================================================================================================================================
# Inicializa a configuração global do módulo
# ========================================================================================================================================================

def init_config(config_dict):
    # Indica que esta função vai alterar a variável global _config
    global _config

    # Guarda o dicionário de configuração fornecido
    _config = config_dict

# ========================================================================================================================================================
# Função auxiliar para obter um valor da configuração através da respetiva chave
# ========================================================================================================================================================

def get(key):
    # Verifica se a configuração já foi inicializada
    if _config is None:
        # Lança um erro explícito se alguém tentar aceder à configuração
        # antes da sua inicialização
        raise RuntimeError(
            "Configuração não inicializada. "
            "Chama configurar() no run_analysis.py primeiro."
        )

    # Devolve o valor associado à chave solicitada
    return _config[key]
