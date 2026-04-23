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

# ========================================================================================================================================================
# 🔧 UTILITÁRIO: Auto-detetar metros vs km
# ========================================================================================================================================================

def auto_convert_to_km_by_pattern(df, dist_col, pattern_col):
    """
    Converte shape_dist_traveled para km DETETANDO por pattern_id.
    Se p95 > 1000 assume metros nesse pattern.
    """
    df[dist_col] = pd.to_numeric(df[dist_col], errors='coerce')

    for pid, g in df.groupby(pattern_col):
        q95 = g[dist_col].quantile(0.95)

        # assume metros nesse percurso
        if pd.notna(q95) and q95 > 1000:
            df.loc[g.index, dist_col] = df.loc[g.index, dist_col] / 1000

    return df


# ========================================================================================================================================================
# 1️⃣ Calcula extensões por plano (por pattern_id)
# ========================================================================================================================================================

def compare_extension(
    gtfs_trips: pd.DataFrame,
    gtfs_shapes: pd.DataFrame,
    gtfs_stop_times: pd.DataFrame,
    gtfs_name: str,
    alerts_df: pd.DataFrame
):
    """
    Calcula extensão máxima (km) por pattern_id:
    - através das shapes
    - através da distancia entre paragens (stop_times)
    """

    # -------------------------------------------------------------------------------------------
    # 🧩 Todos os pattern_id existentes
    # -------------------------------------------------------------------------------------------
    all_patterns = gtfs_trips[['pattern_id']].drop_duplicates().reset_index(drop=True)

    # -------------------------------------------------------------------------------------------
    # 📌 SHAPES
    # -------------------------------------------------------------------------------------------
    merged_shapes = (
        gtfs_trips[['trip_id', 'pattern_id', 'shape_id']]
        .merge(gtfs_shapes[['shape_id', 'shape_dist_traveled']], on='shape_id', how='left')
    )

    merged_shapes['shape_dist_traveled'] = pd.to_numeric(
        merged_shapes['shape_dist_traveled'], errors='coerce'
    )
    # merged_shapes['shape_dist_traveled'] = auto_convert_to_km(merged_shapes['shape_dist_traveled'])

    merged_shapes = auto_convert_to_km_by_pattern(
    merged_shapes, 'shape_dist_traveled', 'pattern_id'
)


    extension_shape = (
        merged_shapes
        .groupby('pattern_id', as_index=False)['shape_dist_traveled']
        .max()
        .merge(all_patterns, on='pattern_id', how='right')
        .rename(columns={'shape_dist_traveled': f'shape_dist_traveled_{gtfs_name}'})
    )

    # -------------------------------------------------------------------------------------------
    # 📌 STOP TIMES
    # -------------------------------------------------------------------------------------------
    
    merged_stops = (gtfs_trips[['trip_id', 'pattern_id']].merge(gtfs_stop_times[['trip_id', 'shape_dist_traveled']], on='trip_id', how='left'))

    merged_stops['shape_dist_traveled'] = pd.to_numeric(merged_stops['shape_dist_traveled'], errors='coerce')
   
    merged_stops = auto_convert_to_km_by_pattern(merged_stops, dist_col="shape_dist_traveled", pattern_col="trip_id")

    extension_stops = (
        merged_stops
        .groupby('pattern_id', as_index=False)['shape_dist_traveled']
        .max()
        .merge(all_patterns, on='pattern_id', how='right')
        .rename(columns={'shape_dist_traveled': f'dist_traveled_stops_{gtfs_name}'})
    )

    # -------------------------------------------------------------------------------------------
    # 📌 Comparação interna
    # -------------------------------------------------------------------------------------------
    
    compare_df = (
        extension_shape
        .merge(extension_stops, on='pattern_id', how='inner')
        .dropna()
    )

    compare_df['diff'] = (
        compare_df[f'dist_traveled_stops_{gtfs_name}']
        - compare_df[f'shape_dist_traveled_{gtfs_name}']
    )

    # -------------------------------------------------------------------------------------------
    # 🚨 Alertas internos
    # -------------------------------------------------------------------------------------------
    
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


# ========================================================================================================================================================
# 2️⃣ Compara extensões entre planos
# ========================================================================================================================================================

def compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df):

    # -------------------------------------------------------------------------------------------
    # Oferta
    # -------------------------------------------------------------------------------------------
    
    ext_shape_oferta, ext_stops_oferta, alerts_df = compare_extension(
        gtfs_oferta['trips'],
        gtfs_oferta['shapes'],
        gtfs_oferta['stop_times'],
        'POferta',
        alerts_df
    )

    # -------------------------------------------------------------------------------------------
    # Operação
    # -------------------------------------------------------------------------------------------
    
    ext_shape_oper, ext_stops_oper, alerts_df = compare_extension(
        gtfs_operacao['trips'],
        gtfs_operacao['shapes'],
        gtfs_operacao['stop_times'],
        'POperação',
        alerts_df
    )

    # -------------------------------------------------------------------------------------------
    # Merge global
    # -------------------------------------------------------------------------------------------
    
    df = (
        ext_shape_oferta
        .merge(ext_shape_oper, on='pattern_id', how='outer')
        .merge(ext_stops_oferta, on='pattern_id', how='outer')
        .merge(ext_stops_oper, on='pattern_id', how='outer')
    )

    # -------------------------------------------------------------------------------------------
    # Diferenças
    # -------------------------------------------------------------------------------------------
    
    df['Diferença absoluta (km)'] = (
        df['shape_dist_traveled_POperação'] - df['shape_dist_traveled_POferta']
    )

    df['Diferença (%)'] = (
        df['Diferença absoluta (km)'] / df['shape_dist_traveled_POferta']
    )

    # -------------------------------------------------------------------------------------------
    # Classificação (CORRIGIDA PARA %)
    # -------------------------------------------------------------------------------------------
    
    def classificar(x):
        if pd.isna(x):
            return 'N/A'
        x = abs(x)
        if x <= 0.01:
            return 'OK'
        elif x <= 0.05:
            return 'LIGEIRA'
        elif x <= 0.10:
            return 'MODERADA'
        else:
            return 'GRAVE'

    df['Classe de diferença'] = df['Diferença (%)'].apply(classificar)

    # -------------------------------------------------------------------------------------------
    # Adiciona colunas novas diretamente do stop_times
    # -------------------------------------------------------------------------------------------
    
    df['Extensão stop_times_POferta'] = df['dist_traveled_stops_POferta']
    df['Extensão stop_times_POperação'] = df['dist_traveled_stops_POperação']

    # -------------------------------------------------------------------------------------------
    # Renomeia colunas para relatório final
    # -------------------------------------------------------------------------------------------
    
    df = df.rename(columns={
        'pattern_id': 'Percurso',
        'shape_dist_traveled_POferta': 'Extensão shape_POferta',
        'shape_dist_traveled_POperação': 'Extensão shape_POperação',
        'dist_traveled_stops_POferta': 'Extensão entre paragens_POferta',
        'dist_traveled_stops_POperação': 'Extensão entre paragens_POperação'
    })

    # -------------------------------------------------------------------------------------------
    # Ordena e seleciona colunas finais
    # -------------------------------------------------------------------------------------------
    
    df = df[
        [
            'Percurso',
            'Extensão shape_POferta',
            'Extensão shape_POperação',
            'Extensão entre paragens_POferta',
            'Extensão entre paragens_POperação',
            'Extensão stop_times_POferta',
            'Extensão stop_times_POperação',
            'Diferença absoluta (km)',
            'Diferença (%)',
            'Classe de diferença'
        ]
    ].sort_values('Percurso').reset_index(drop=True)

    return df, alerts_df
# ========================================================================================================================================================
# 3️⃣ Compara total de circulações entre planos
# ========================================================================================================================================================

def compare_circulations_between_plans(df_oferta, df_operacao, alerts_df):
    """
    Compara o total de circulações por percurso entre POferta e POperação.
    - df_oferta e df_operacao devem conter as colunas:
        'Percurso' e 'Num total circulações ano'
    - Gera alertas se houver diferença
    """

    # Renomeia colunas para evitar conflito
    df_oferta = df_oferta[['Percurso', 'Num total circulações ano']].rename(
        columns={'Num total circulações ano': 'Circulacoes_POferta'}
    )
    df_operacao = df_operacao[['Percurso', 'Num total circulações ano']].rename(
        columns={'Num total circulações ano': 'Circulacoes_POperacao'}
    )

    # Merge dos dois planos
    df = df_oferta.merge(df_operacao, on='Percurso', how='outer')

    # Calcula diferença
    df['Diferenca_circulacoes'] = df['Circulacoes_POperacao'] - df['Circulacoes_POferta']

    # Classificação de alerta
    def classificar_circ(x):
        if pd.isna(x):
            return 'N/A'
        elif x == 0:
            return 'OK'
        else:
            return 'GRAVE'

    df['Classe_diferenca'] = df['Diferenca_circulacoes'].apply(classificar_circ)

    # Adiciona alertas
    for idx, row in df.loc[df['Diferenca_circulacoes'] != 0].iterrows():
        alerts_df = add_alert(
            alerts_df,
            "Circulações",
            "Diferença total anual",
            "GRAVE",
            f"Diferença de {row['Diferenca_circulacoes']} circulações entre POferta e POperação",
            row['Percurso']
        )

    # Ordena colunas para relatório final
    df = df[[
        'Percurso',
        'Circulacoes_POferta',
        'Circulacoes_POperacao',
        'Diferenca_circulacoes',
        'Classe_diferenca'
    ]].sort_values('Percurso').reset_index(drop=True)

    return df, alerts_df
