"""

Este módulo gere a configuração global da aplicação durante a execução.
Permite iniciar a configuração uma única vez e aceder aos seus valores a partir de qualquer ponto do código, 
garantindo que a configuração é explicitamente definida antes de ser utilizada.

"""
_config = None

# ========================================================================================================================================================
# 1️⃣ Inicia a configuração global do módulo
# ========================================================================================================================================================

def init_config(config_dict):
    # Indica que esta função vai alterar a variável global _config
    global _config

    # Guarda o dicionário de configuração fornecido
    _config = config_dict

# ========================================================================================================================================================
# 2️⃣ Função auxiliar para obter um valor da configuração através da respetiva chave
# ========================================================================================================================================================

def get(key):
    # Verifica se a configuração já foi iniciada
    if _config is None:
        # Lança um erro explícito se alguém tentar aceder à configuração antes de ser iniciada
        raise RuntimeError(
            "Configuração não iniciada. "
            "Chama configurar() no run_analysis.py primeiro."
        )

    # Devolve o valor associado à chave solicitada
    return _config[key]
