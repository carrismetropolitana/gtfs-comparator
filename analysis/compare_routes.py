import pandas as pd
from analysis.alerts import add_alert

# COMPARE ROUTE FILES BETWEEN OFFER AND OPERATION PLANS
def compare_routes(gtfs_POferta_path, gtfs_POperação_path, alerts_df):
    # Read routes files from both GTFS datasets
    routes_gtfs_POferta = gtfs_POferta_path
    routes_gtfs_POperação = gtfs_POperação_path

    # Extract unique route IDs from both datasets
    unique_routes_gtfs_POferta = set(routes_gtfs_POferta['route_id'])
    unique_routes_gtfs_POperação = set(routes_gtfs_POperação['route_id'])

    # Find routes that are missing in one of the datasets
    missing_routes_gtfs_POferta = unique_routes_gtfs_POperação - unique_routes_gtfs_POferta
    missing_routes_gtfs_POperação = unique_routes_gtfs_POferta - unique_routes_gtfs_POperação

   # print(missing_routes_gtfs_POferta)

    # Print alerts for missing routes
    if missing_routes_gtfs_POferta:
        alerts_df = add_alert(
            alerts_df,
            "PLANO DE OFERTA",
            "Rotas",
            'MUITO GRAVE',
            f"As seguintes rotas não existem no Plano de Oferta:",
            f'{missing_routes_gtfs_POferta}'
        )

    if missing_routes_gtfs_POperação:
        alerts_df = add_alert(
            alerts_df,
            "PLANO DE OPERAÇÃO",
            "Rotas",
            'MUITO GRAVE',
            f"As seguintes rotas não existem no Plano de Operação:",
            f'{missing_routes_gtfs_POperação}'
        )

    dtype_mapping = {
        'line_id': str, 'line_short_name': str, 'line_long_name': str,
        'agency_id': str, 'route_short_name': str, 'route_long_name': str,
        'route_type': str, 'path_type': str, 'route_color': str, 'route_text_color': str
    }

    routes_gtfs_POferta = routes_gtfs_POferta.astype(dtype_mapping)
    routes_gtfs_POperação = routes_gtfs_POperação.astype(dtype_mapping)

    # Merge routes data based on 'route_id'
    merged_routes = pd.merge(
        routes_gtfs_POferta,
        routes_gtfs_POperação,
        on='route_id',
        suffixes=('_POferta', '_POperação'),
        how='outer'
    )

    fields_to_compare = [
        'line_id', 'line_short_name', 'line_long_name',
        'agency_id', 'route_short_name', 'route_long_name',
        'route_type', 'path_type', 'route_color',
        'route_text_color'
    ]

    # Iterate over each field and compare values
    for index, row in merged_routes.iterrows():
        route_id = row['route_id']
        # Skip processing if the route_id is already in the missing routes
        if route_id in missing_routes_gtfs_POferta or route_id in missing_routes_gtfs_POperação:
            continue

        for field in fields_to_compare:
            value_POferta = str(row[f'{field}_POferta'])
            value_POperação = str(row[f'{field}_POperação'])

            if value_POferta != value_POperação:
                alerts_df = add_alert(
                    alerts_df,
                    "PLANO DE OPERAÇÃO",
                    "Rotas",
                    'MUITO GRAVE',
                    f"Existem diferenças nos campos {field} para as seguintes rotas:",
                    f'{route_id}'
                )

    return merged_routes, alerts_df
