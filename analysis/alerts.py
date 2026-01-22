
"""
Este módulo gere a criação e o registo de alertas durante o processamento de dados.

Funcionalidades principais:
- Normaliza os nomes dos planos para garantir uma apresentação consistente nos alertas.
- Inicializa um DataFrame de alertas com uma estrutura predefinida.
- Adiciona alertas de forma incremental, incluindo tipo de erro, gravidade, descrição e percurso associado.

Objetivo:
- Centralizar e padronizar o registo de erros e inconsistências, facilitando a análise, validação e exportação dos alertas gerados.

Outputs:
- 1 tabela com a lista de todos os erros e inconsistências ao longo da comparação de planos.

"""

import pandas as pd

# ========================================================================================================================================================
# 🔧 Padronização de Planos
# ========================================================================================================================================================

def normalize_plan_name(plan_name: str) -> str:
    """Uniformiza o nome do plano para exibição nos alertas."""
    plan_name_lower = plan_name.lower()
    if "oferta" in plan_name_lower:
        return "Plano de Oferta"
    elif "operação" in plan_name_lower or "operacao" in plan_name_lower:
        return "Plano de Operação"
    else:
        return plan_name

# ========================================================================================================================================================
# 🧮 Criação da tabela de alertas
# ========================================================================================================================================================

def init_alerts_df():
    """Cria o DataFrame de alertas vazio."""
    return pd.DataFrame(columns=['Plano', 'Tipo de erro', 'Gravidade', 'Descrição', 'Percurso'])

# ========================================================================================================================================================
# 🚨 Adiciona os alertas
# ========================================================================================================================================================

def add_alert(alerts_df, plan, error_type, grav, description, path):
    """Adiciona um alerta ao DataFrame, normalizando o nome do plano."""
    plan_normalized = normalize_plan_name(plan)
    new_alert = pd.DataFrame({
        'Plano': [plan_normalized],
        'Tipo de erro': [error_type],
        'Gravidade': [grav],
        'Descrição': [description],
        'Percurso': [path]
    })

    return pd.concat([alerts_df, new_alert], ignore_index=True)
