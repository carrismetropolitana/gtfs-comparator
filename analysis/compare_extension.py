import pandas as pd
from analysis.alerts import add_alert

# ========================================================================================================================================================
# Garante que a distancia do GTFS está em Km
# ========================================================================================================================================================

def _to_km_if_needed(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Converte metros para km se o valor for > 1000.
    """
    mask = df[col] > 1000
    df.loc[mask, col] = df.loc[mask, col] / 1000
    return df

# ========================================================================================================================================================
# Calcula extensões
# ========================================================================================================================================================
def compare_extension(
    gtfs_trips: pd.DataFrame,
    gtfs_shapes: pd.DataFrame,
    gtfs_stop_times: pd.DataFrame,
    gtfs_name: str,
    alerts_df: pd.DataFrame
):
   
    merged_data = gtfs_trips[['trip_id', 'pattern_id', 'shape_id']].merge(gtfs_shapes[['shape_id', 'shape_dist_traveled']], on='shape_id')
    merged_data_stop_times = gtfs_trips[['trip_id', 'pattern_id']].merge(gtfs_stop_times[['trip_id', 'shape_dist_traveled']], on='trip_id')

    # -------------------------------------------------------------------------------------------
    # Calcula a extensão pela shape
    # -------------------------------------------------------------------------------------------
    extension = merged_data.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
    extension = _to_km_if_needed(extension, 'shape_dist_traveled')
    extension.columns = ['pattern_id', f'shape_dist_traveled_{gtfs_name}']

    # -------------------------------------------------------------------------------------------
    # Calcula a extensão pr paragens
    # -------------------------------------------------------------------------------------------

    extension_stop_times = merged_data_stop_times.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
    extension_stop_times = _to_km_if_needed(extension_stop_times, 'shape_dist_traveled')
    extension_stop_times.columns = ['pattern_id', f'dist_traveled_stops_{gtfs_name}']

    # -------------------------------------------------------------------------------------------
    # Compara as distancias entre planos
    # -------------------------------------------------------------------------------------------
    compare_extensions_in_plan = extension.merge(extension_stop_times, on='pattern_id')
    compare_extensions_in_plan['diff'] = (compare_extensions_in_plan[f'dist_traveled_stops_{gtfs_name}'] - compare_extensions_in_plan[f'shape_dist_traveled_{gtfs_name}'])

    # -------------------------------------------------------------------------------------------
    # Gera Alertas (diferença > 1km)
    # -------------------------------------------------------------------------------------------

    mask_alert = compare_extensions_in_plan['diff'].abs() > 1
    for pattern_id in compare_extensions_in_plan.loc[mask_alert, 'pattern_id']:
        alerts_df = add_alert(
            alerts_df,
            gtfs_name,
            "Extensões",
            'GRAVE',
            "Diferença entre extensão calculada a partir de shapes e entre paragens nos percursos",
            f'{pattern_id}'
        )

    return extension, extension_stop_times, alerts_df

# ========================================================================================================================================================
# Compara extensões entre planos
# ========================================================================================================================================================

def compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df):
    
    # Extensões – Plano de Oferta
    ext_shape_oferta, ext_stops_oferta, alerts_df = compare_extension(
        gtfs_oferta['trips'],
        gtfs_oferta['shapes'],
        gtfs_oferta['stop_times'],
        'POferta',
        alerts_df
    )

    # Extensões – Plano de Operação
    ext_shape_oper, ext_stops_oper, alerts_df = compare_extension(
        gtfs_operacao['trips'],
        gtfs_operacao['shapes'],
        gtfs_operacao['stop_times'],
        'POperação',
        alerts_df
    )

    # ---------------------------------------
    # Juntar tudo por percurso (inner merge)
    # ---------------------------------------
    df = (
        ext_shape_oferta
        .merge(ext_shape_oper, on='pattern_id', how='inner')
        .merge(ext_stops_oferta, on='pattern_id', how='inner')
        .merge(ext_stops_oper, on='pattern_id', how='inner')
    )

    # ---------------------------------------
    # Diferença absoluta (km)
    # ---------------------------------------
    df['Diferença absoluta (km)'] = (
        df['shape_dist_traveled_POperação']
        - df['shape_dist_traveled_POferta']
    )

    # ---------------------------------------
    # Diferença percentual (%)
    # ---------------------------------------
    df['Diferença (%)'] = (
        df['Diferença absoluta (km)']
        / df['shape_dist_traveled_POferta']
    ) * 100

    # ---------------------------------------
    # Classe da diferença
    # ---------------------------------------
    def classificar(x):
        x = abs(x)
        if x <= 1:
            return 'OK'
        elif x <= 5:
            return 'LIGEIRA'
        elif x <= 10:
            return 'MODERADA'
        else:
            return 'GRAVE'

    df['Classe de diferença'] = df['Diferença (%)'].apply(classificar)

    # ---------------------------------------
    # Formato final
    # ---------------------------------------
    df = df.rename(columns={
        'pattern_id': 'Percurso',
        'shape_dist_traveled_POferta': 'Extensão shape_POferta',
        'shape_dist_traveled_POperação': 'Extensão shape_POperação',
        'dist_traveled_stops_POferta': 'Extensão entre paragens_POferta',
        'dist_traveled_stops_POperação': 'Extensão entre paragens_POperação'
    })

    df = df[
        [
            'Percurso',
            'Extensão shape_POferta',
            'Extensão shape_POperação',
            'Extensão entre paragens_POferta',
            'Extensão entre paragens_POperação',
            'Diferença absoluta (km)',
            'Diferença (%)',
            'Classe de diferença'
        ]
    ].sort_values('Percurso').reset_index(drop=True)

    return df, alerts_df
