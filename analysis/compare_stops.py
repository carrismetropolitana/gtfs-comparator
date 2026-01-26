import pandas as pd
from analysis.alerts import add_alert

# ========================================================================================================================================================
# 1️⃣ Compara as paragens entre planos
# ========================================================================================================================================================

def compare_stops_between_plans(df_oferta, df_operacao, alerts_df=None):
    """
    Compara paragens entre Plano de Oferta e Plano de Operação.
    Retorna somente as paragens com diferenças e adiciona alertas.
    """

    if alerts_df is None:
        from analysis.alerts import init_alerts_df
        alerts_df = init_alerts_df()

    # -------------------------------------------------------------------------------------------
    # 📌 Junta as paragens de oferta com operação por stop_id
    # -------------------------------------------------------------------------------------------

    df_merged = pd.merge(
        df_oferta,
        df_operacao,
        on='stop_id',
        how='outer',
        suffixes=('_POferta', '_POperacao')
    )

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
            alerts_df = add_alert(
                alerts_df,
                "Plano de Operação",
                "Paragens",
                "MUITO GRAVE",
                f"Paragens com diferenças: {col}",
                row['stop_id']
            )
            
    # -------------------------------------------------------------------------------------------
    # 📌 Remove duplicados. Lista apenas as paragens com diferenças
    # -------------------------------------------------------------------------------------------

    diffs = diffs.drop_duplicates(subset=['stop_id'])

    return diffs, alerts_df
