import pandas as pd
from analysis.alerts import add_alert

def compare_stops_between_plans(df_oferta, df_operacao, alerts_df=None):
    """
    Compara paragens entre Plano de Oferta e Plano de Operação.
    Retorna somente as paragens com diferenças e adiciona alertas.
    """

    if alerts_df is None:
        from analysis.alerts import init_alerts_df
        alerts_df = init_alerts_df()

    # Merge das paragens pelo stop_id
    df_merged = pd.merge(
        df_oferta,
        df_operacao,
        on='stop_id',
        how='outer',
        suffixes=('_POferta', '_POperacao')
    )

    # Comparar colunas relevantes
    columns_to_compare = ['stop_name', 'stop_lat', 'stop_lon']
    diffs = pd.DataFrame()

    for col in columns_to_compare:
        mask_diff = df_merged[f"{col}_POferta"] != df_merged[f"{col}_POperacao"]
        diffs = pd.concat([diffs, df_merged[mask_diff]])

        # Adicionar alertas para cada diferença
        for _, row in df_merged[mask_diff].iterrows():
            alerts_df = add_alert(
                alerts_df,
                "Plano de Operação",
                "Paragens",
                "MUITO GRAVE",
                f"Paragens com diferenças: {col}",
                row['stop_id']
            )

    # Remover duplicados, só manter paragens com diferenças
    diffs = diffs.drop_duplicates(subset=['stop_id'])

    return diffs, alerts_df
