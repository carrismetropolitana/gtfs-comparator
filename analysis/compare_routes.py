
"""
Este módulo compara as rotas (routes.txt) entre dois planos GTFS.

Funcionalidades principais:
- Identifica rotas que existem no Plano de Oferta e não existem no Plano de Operação e vice-versa.
- Normaliza os tipos de dados dos campos relevantes para evitar inconsistências de comparação.
- Compara os atributos das rotas comuns aos dois planos (ex.: line_id, agency_id, nomes, tipo de rota, cores).
- Deteta diferenças campo a campo entre os dois planos para a mesma rota.
- Gera alertas de gravidade "MUITO GRAVE" para rotas em falta ou com atributos divergentes.

Outputs:
- 1 tabela com as rotas combinadas dos dois planos GTFS (merge por route_id).
- 1 tabela de alertas com todas as inconsistências detetadas entre os planos.

"""

import pandas as pd
from analysis.alerts import add_alert

# ========================================================================================================================================================
# 1️⃣ Processa os dados
# ========================================================================================================================================================

def compare_routes(gtfs_POferta_path, gtfs_POperação_path, alerts_df):
    routes_gtfs_POferta = gtfs_POferta_path
    routes_gtfs_POperação = gtfs_POperação_path

    # Extract unique route IDs
    unique_routes_gtfs_POferta = set(routes_gtfs_POferta['route_id'])
    unique_routes_gtfs_POperação = set(routes_gtfs_POperação['route_id'])

    # -------------------------------------------------------------------------------------------
    # 📌 Deteta rotas em falta
    # -------------------------------------------------------------------------------------------
    missing_routes_gtfs_POferta = unique_routes_gtfs_POperação - unique_routes_gtfs_POferta
    missing_routes_gtfs_POperação = unique_routes_gtfs_POferta - unique_routes_gtfs_POperação

    # -------------------------------------------------------------------------------------------
    # 📌 Gera um alerta se alguma rota estiver em falta
    # -------------------------------------------------------------------------------------------
    # Alerts for missing routes
    if missing_routes_gtfs_POferta:
        alerts_df = add_alert(
            alerts_df,
            "PLANO DE OFERTA",
            "Rotas",
            'MUITO GRAVE',
            "As seguintes rotas não existem no Plano de Oferta:",
            f'{missing_routes_gtfs_POferta}'
        )

    if missing_routes_gtfs_POperação:
        alerts_df = add_alert(
            alerts_df,
            "PLANO DE OPERAÇÃO",
            "Rotas",
            'MUITO GRAVE',
            "As seguintes rotas não existem no Plano de Operação:",
            f'{missing_routes_gtfs_POperação}'
        )

    # -------------------------------------------------------------------------------------------
    # 📌 Normaliza os dados
    # -------------------------------------------------------------------------------------------
    dtype_mapping = {
        'line_id': str, 'line_short_name': str, 'line_long_name': str,
        'agency_id': str, 'route_short_name': str, 'route_long_name': str,
        'route_type': str, 'path_type': str, 'route_color': str, 'route_text_color': str
    }

    routes_gtfs_POferta = routes_gtfs_POferta.astype(dtype_mapping)
    routes_gtfs_POperação = routes_gtfs_POperação.astype(dtype_mapping)
   
    # -------------------------------------------------------------------------------------------
    # 📌 Junta as rotas dos dois GTFS
    # -------------------------------------------------------------------------------------------
    merged_routes = pd.merge(
        routes_gtfs_POferta,
        routes_gtfs_POperação,
        on='route_id',
        suffixes=('_POferta', '_POperação'),
        how='outer'
    )

    # -------------------------------------------------------------------------------------------
    # 📌 Campos a comparar
    # -------------------------------------------------------------------------------------------

    fields_to_compare = [
        'line_id', 'line_short_name', 'line_long_name',
        'agency_id', 'route_short_name', 'route_long_name',
        'route_type', 'path_type', 'route_color',
        'route_text_color'
    ]
   
    # -------------------------------------------------------------------------------------------
    # 📌 Filtra apenas pelas rotas válidas
    # -------------------------------------------------------------------------------------------
    valid_routes_mask = ~merged_routes['route_id'].isin(missing_routes_gtfs_POferta | missing_routes_gtfs_POperação)
    merged_routes_valid = merged_routes[valid_routes_mask]

    # -------------------------------------------------------------------------------------------
    # 📌 Compara campo a campo
    # -------------------------------------------------------------------------------------------
  
    for field in fields_to_compare:
        col_POferta = f'{field}_POferta'
        col_POperação = f'{field}_POperação'

        diff_mask = merged_routes_valid[col_POferta].astype(str) != merged_routes_valid[col_POperação].astype(str)

        if diff_mask.any():
            differing_routes = merged_routes_valid.loc[diff_mask, 'route_id']
            for route_id in differing_routes:
                alerts_df = add_alert(
                    alerts_df,
                    "PLANO DE OPERAÇÃO",
                    "Rotas",
                    'MUITO GRAVE',
                    f"Existem diferenças nos campos {field} para as seguintes rotas:",
                    f'{route_id}'
                )

    return merged_routes, alerts_df
