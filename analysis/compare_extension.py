
"""
# Este módulo calcula e compara a extensão dos percursos GTFS.

# Funcionalidades principais:
# - Calcula a extensão de cada percurso (pattern_id) a partir das shapes utilizando o valor máximo de shape_dist_traveled.
# - Calcula a extensão do percurso a partir das paragens (stop_times).
# - Compara as duas extensões dentro do mesmo plano (GTFS) e gera alertas quando a diferença é superior a 1 km.
# - Compara a extensão dos percursos entre os dois planos GTFS (Plano de Oferta vs Plano de Operação).
# - Calcula diferenças absolutas (km) e percentuais (%) e classifica a gravidade da diferença (OK, LIGEIRA, MODERADA, GRAVE).

# Outputs:
# - 1 tabela com a comparação final das extensões por percurso.
# - 1 tabela de alertas com inconsistências detetadas.

"""

import pandas as pd
from analysis.alerts import add_alert

# =================================================================================================
# 1️⃣ Calcula extensões por plano (por pattern_id)
# =================================================================================================

def compare_extension(
    gtfs_trips: pd.DataFrame,
    gtfs_shapes: pd.DataFrame,
    gtfs_stop_times: pd.DataFrame,
    gtfs_name: str,
    alerts_df: pd.DataFrame
):
    """
    Calcula a extensão máxima (km) por pattern_id:
    - a partir das shapes
    - a partir das stop_times

    Retorna SEMPRE:
        extension_shape_df,
        extension_stops_df,
        alerts_df
    """

    # ---------------------------------------------------------------------------------------------
    # 🧩 Todos os pattern_id existentes (base segura)
    # ---------------------------------------------------------------------------------------------
    all_patterns = (
        gtfs_trips[['pattern_id']]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # ---------------------------------------------------------------------------------------------
    # 📌 Extensão pela SHAPE
    # ---------------------------------------------------------------------------------------------
    merged_shapes = (
        gtfs_trips[['trip_id', 'pattern_id', 'shape_id']]
        .merge(
            gtfs_shapes[['shape_id', 'shape_dist_traveled']],
            on='shape_id',
            how='left'
        )
    )

    merged_shapes['shape_dist_traveled'] = pd.to_numeric(
        merged_shapes['shape_dist_traveled'],
        errors='coerce'
    )

    extension_shape = (
        merged_shapes
        .groupby('pattern_id', as_index=False)['shape_dist_traveled']
        .max()
    )

    extension_shape = (
        all_patterns
        .merge(extension_shape, on='pattern_id', how='left')
        .rename(columns={'shape_dist_traveled': f'shape_dist_traveled_{gtfs_name}'})
    )

    # ---------------------------------------------------------------------------------------------
    # 📌 Extensão pelas PARAGENS
    # ---------------------------------------------------------------------------------------------
    merged_stops = (
        gtfs_trips[['trip_id', 'pattern_id']]
        .merge(
            gtfs_stop_times[['trip_id', 'shape_dist_traveled']],
            on='trip_id',
            how='left'
        )
    )

    merged_stops['shape_dist_traveled'] = pd.to_numeric(
        merged_stops['shape_dist_traveled'],
        errors='coerce'
    )

    extension_stops = (
        merged_stops
        .groupby('pattern_id', as_index=False)['shape_dist_traveled']
        .max()
    )

    extension_stops = (
        all_patterns
        .merge(extension_stops, on='pattern_id', how='left')
        .rename(columns={'shape_dist_traveled': f'dist_traveled_stops_{gtfs_name}'})
    )

    # ---------------------------------------------------------------------------------------------
    # 📌 Comparação interna (apenas onde existem valores)
    # ---------------------------------------------------------------------------------------------
    compare_df = (
        extension_shape
        .merge(extension_stops, on='pattern_id', how='inner')
        .dropna(subset=[
            f'shape_dist_traveled_{gtfs_name}',
            f'dist_traveled_stops_{gtfs_name}'
        ])
    )

    compare_df['diff'] = (
        compare_df[f'dist_traveled_stops_{gtfs_name}']
        - compare_df[f'shape_dist_traveled_{gtfs_name}']
    )

    # ---------------------------------------------------------------------------------------------
    # 🚨 Alertas (> 1 km de diferença real)
    # ---------------------------------------------------------------------------------------------
    for pattern_id in compare_df.loc[compare_df['diff'].abs() > 1, 'pattern_id']:
        alerts_df = add_alert(
            alerts_df,
            gtfs_name,
            "Extensões",
            "GRAVE",
            "Diferença > 1 km entre extensão por shape e por paragens",
            str(pattern_id)
        )

    return extension_shape, extension_stops, alerts_df


# =================================================================================================
# 2️⃣ Compara extensões entre planos
# =================================================================================================

def compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df):

    # Oferta
    ext_shape_oferta, ext_stops_oferta, alerts_df = compare_extension(
        gtfs_oferta['trips'],
        gtfs_oferta['shapes'],
        gtfs_oferta['stop_times'],
        'POferta',
        alerts_df
    )

    # Operação
    ext_shape_oper, ext_stops_oper, alerts_df = compare_extension(
        gtfs_operacao['trips'],
        gtfs_operacao['shapes'],
        gtfs_operacao['stop_times'],
        'POperação',
        alerts_df
    )

    # ---------------------------------------------------------------------------------------------
    # Merge global (todos os pattern_id)
    # ---------------------------------------------------------------------------------------------
    df = (
        ext_shape_oferta
        .merge(ext_shape_oper, on='pattern_id', how='outer')
        .merge(ext_stops_oferta, on='pattern_id', how='outer')
        .merge(ext_stops_oper, on='pattern_id', how='outer')
    )

    # ---------------------------------------------------------------------------------------------
    # Diferenças
    # ---------------------------------------------------------------------------------------------
    df['Diferença absoluta (km)'] = (
        df['shape_dist_traveled_POperação']
        - df['shape_dist_traveled_POferta']
    )

    df['Diferença (%)'] = (
        df['Diferença absoluta (km)']
        / df['shape_dist_traveled_POferta']
    ) 

    # ---------------------------------------------------------------------------------------------
    # Classificação
    # ---------------------------------------------------------------------------------------------
    def classificar(x):
        if pd.isna(x):
            return 'N/A'
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

    # ---------------------------------------------------------------------------------------------
    # Output final
    # ---------------------------------------------------------------------------------------------
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
