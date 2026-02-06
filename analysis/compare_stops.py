"""
Este módulo compara as paragens entre o Plano de Oferta e o Plano de Operação.

Funcionalidades principais:
- Junta as paragens dos dois planos com base no stop_id, garantindo a deteção de paragens em falta ou divergentes.
- Compara os atributos principais das paragens (stop_name, stop_lat e stop_lon).
- Identifica diferenças de nomenclatura e de localização geográfica entre os planos.
- Isola apenas as paragens que apresentam inconsistências entre Oferta e Operação.
- Gera alertas associados ao Plano de Operação sempre que são detetadas diferenças.
- Classifica todas as inconsistências como de gravidade “MUITO GRAVE”.

Outputs:
- 1 tabela com a lista de paragens que apresentam diferenças entre os planos.
- Atualização da tabela de alertas com o detalhe das inconsistências por stop_id.
"""

import pandas as pd
from analysis.alerts import add_alert

# ========================================================================================================================================================
# 1️⃣ Compara as paragens entre planos
# ========================================================================================================================================================

def compare_stops_between_plans(df_oferta, df_operacao, alerts_df=None):
    """
    Compara paragens entre Plano de Oferta e Plano de Operação.
    Devolve apenas as paragens com diferenças e adiciona alertas.
    """

    if alerts_df is None:
        from analysis.alerts import init_alerts_df
        alerts_df = init_alerts_df()

    # -------------------------------------------------------------------------------------------
    # 📌 Junta as paragens de oferta com operação por stop_id
    # -------------------------------------------------------------------------------------------

    df_merged = pd.merge(df_oferta, df_operacao, on='stop_id', how='outer', suffixes=('_POferta', '_POperacao'))

    # -------------------------------------------------------------------------------------------
    # 📌 Compara os campos: stop_name; stop_lat; stop_lon
    # -------------------------------------------------------------------------------------------
 
    columns_to_compare = ['stop_name', 'stop_lat', 'stop_lon']
    diffs = pd.DataFrame()

    for col in columns_to_compare:
        mask_diff = df_merged[f"{col}_POferta"] != df_merged[f"{col}_POperacao"]
        diffs = pd.concat([diffs, df_merged[mask_diff]])

    # -------------------------------------------------------------------------------------------
    # 📌 Adiciona alertas de acordo com as diferenças encontradas
    # -------------------------------------------------------------------------------------------
        
        for _, row in df_merged[mask_diff].iterrows():
            alerts_df = add_alert(alerts_df, "Plano de Operação", "Paragens", "MUITO GRAVE", f"Paragens com diferenças: {col}", row['stop_id'])

    # -------------------------------------------------------------------------------------------
    # 📌 Remove duplicados. Lista apenas as paragens com diferenças
    # -------------------------------------------------------------------------------------------

    diffs = diffs.drop_duplicates(subset=['stop_id'])

    return diffs, alerts_df
