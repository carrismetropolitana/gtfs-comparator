
# """
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

# """

# import pandas as pd
# from analysis.alerts import add_alert






# # ========================================================================================================================================================
# # 1️⃣ Garante que a distancia do GTFS está em Km
# # ========================================================================================================================================================

# # def _to_km_if_needed(df: pd.DataFrame, col: str) -> pd.DataFrame:
# #     """
# #     Converte metros para km se o valor for > 1000.
# #     """
# #     mask = df[col] > 1000
# #     df.loc[mask, col] = df.loc[mask, col] / 1000
# #     return df

# # ========================================================================================================================================================
# # 2️⃣ Calcula extensões
# # ========================================================================================================================================================
# # def compare_extension(
# #     gtfs_trips: pd.DataFrame,
# #     gtfs_shapes: pd.DataFrame,
# #     gtfs_stop_times: pd.DataFrame,
# #     gtfs_name: str,
# #     alerts_df: pd.DataFrame
# # ):
   
# #     merged_data = gtfs_trips[['trip_id', 'pattern_id', 'shape_id']].merge(gtfs_shapes[['shape_id', 'shape_dist_traveled']], on='shape_id')
# #     merged_data_stop_times = gtfs_trips[['trip_id', 'pattern_id']].merge(gtfs_stop_times[['trip_id', 'shape_dist_traveled']], on='trip_id')

# #     # -------------------------------------------------------------------------------------------
# #     # 📌 Calcula a extensão pela shape
# #     # -------------------------------------------------------------------------------------------
# #     extension = merged_data.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
# #     extension = _to_km_if_needed(extension, 'shape_dist_traveled')
# #     extension.columns = ['pattern_id', f'shape_dist_traveled_{gtfs_name}']

# #     # -------------------------------------------------------------------------------------------
# #     # 📌 Calcula a extensão pr paragens
# #     # -------------------------------------------------------------------------------------------

# #     extension_stop_times = merged_data_stop_times.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
# #     extension_stop_times = _to_km_if_needed(extension_stop_times, 'shape_dist_traveled')
# #     extension_stop_times.columns = ['pattern_id', f'dist_traveled_stops_{gtfs_name}']

# #     # -------------------------------------------------------------------------------------------
# #     # 📌 Compara as distancias entre planos
# #     # -------------------------------------------------------------------------------------------
# #     compare_extensions_in_plan = extension.merge(extension_stop_times, on='pattern_id')
# #     compare_extensions_in_plan['diff'] = (compare_extensions_in_plan[f'dist_traveled_stops_{gtfs_name}'] - compare_extensions_in_plan[f'shape_dist_traveled_{gtfs_name}'])

# #     # -------------------------------------------------------------------------------------------
# #     # 📌 Gera Alertas (diferença > 1km)
# #     # -------------------------------------------------------------------------------------------

# #     mask_alert = compare_extensions_in_plan['diff'].abs() > 1
# #     for pattern_id in compare_extensions_in_plan.loc[mask_alert, 'pattern_id']:
# #         alerts_df = add_alert(
# #             alerts_df,
# #             gtfs_name,
# #             "Extensões",
# #             'GRAVE',
# #             "Diferença entre extensão calculada a partir de shapes e entre paragens nos percursos",
# #             f'{pattern_id}'
# #         )

# #     return extension, extension_stop_times, alerts_df










# def compare_extension(
#     gtfs_trips: pd.DataFrame,
#     gtfs_shapes: pd.DataFrame,
#     gtfs_stop_times: pd.DataFrame,
#     gtfs_name: str,
#     alerts_df: pd.DataFrame
# ):

#     merged_shapes = (
#         gtfs_trips[['trip_id', 'pattern_id', 'shape_id']]
#         .merge(
#             gtfs_shapes[['shape_id', 'shape_dist_traveled']],
#             on='shape_id',
#             how='left'
#         )
#     )

#     merged_stops = (
#         gtfs_trips[['trip_id', 'pattern_id']]
#         .merge(
#             gtfs_stop_times[['trip_id', 'shape_dist_traveled']],
#             on='trip_id',
#             how='left'
#         )
#     )

#     # 📌 Extensão pela shape (EM KM, SEM CONVERSÕES)
#     extension_shape = (
#         merged_shapes
#         .groupby('pattern_id')['shape_dist_traveled']
#         .max()
#         .reset_index()
#         .rename(columns={'shape_dist_traveled': f'shape_dist_traveled_{gtfs_name}'})
#     )

#     # 📌 Extensão pelas paragens (EM KM, SEM CONVERSÕES)
#     extension_stops = (
#         merged_stops
#         .groupby('pattern_id')['shape_dist_traveled']
#         .max()
#         .reset_index()
#         .rename(columns={'shape_dist_traveled': f'dist_traveled_stops_{gtfs_name}'})
#     )

#     # 📌 Comparação interna
#     compare_df = extension_shape.merge(extension_stops, on='pattern_id', how='inner')

#     compare_df['diff'] = (
#         compare_df[f'dist_traveled_stops_{gtfs_name}']
#         - compare_df[f'shape_dist_traveled_{gtfs_name}']
#     )

#     # 📌 Alertas (>1 km reais)
#     for pattern_id in compare_df.loc[compare_df['diff'].abs() > 1, 'pattern_id']:
#         alerts_df = add_alert(
#             alerts_df,
#             gtfs_name,
#             "Extensões",
#             "GRAVE",
#             "Diferença > 1 km entre extensão por shape e por paragens",
#             str(pattern_id)
#         )

#     return extension_shape, extension_stops, alerts_df


# # ========================================================================================================================================================
# # 3️⃣ Compara extensões entre planos
# # ========================================================================================================================================================

# def compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df):
    
#     # Extensões – Plano de Oferta
#     ext_shape_oferta, ext_stops_oferta, alerts_df = compare_extension(
#         gtfs_oferta['trips'],
#         gtfs_oferta['shapes'],
#         gtfs_oferta['stop_times'],
#         'POferta',
#         alerts_df
#     )

#     # Extensões – Plano de Operação
#     ext_shape_oper, ext_stops_oper, alerts_df = compare_extension(
#         gtfs_operacao['trips'],
#         gtfs_operacao['shapes'],
#         gtfs_operacao['stop_times'],
#         'POperação',
#         alerts_df
#     )

#     df = (
#         ext_shape_oferta
#         .merge(ext_shape_oper, on='pattern_id', how='inner')
#         .merge(ext_stops_oferta, on='pattern_id', how='inner')
#         .merge(ext_stops_oper, on='pattern_id', how='inner')
#     )

#     # -------------------------------------------------------------------------------------------
#     # 📌 Calcula a diferença absoluta (km)
#     # -------------------------------------------------------------------------------------------
#     df['Diferença absoluta (km)'] = (df['shape_dist_traveled_POperação'] - df['shape_dist_traveled_POferta'])

#     # -------------------------------------------------------------------------------------------
#     # 📌 Calcula a diferença percentual (%)
#     # -------------------------------------------------------------------------------------------
#     df['Diferença (%)'] = (df['Diferença absoluta (km)'] / df['shape_dist_traveled_POferta']) * 100

#     # -------------------------------------------------------------------------------------------
#     # 📌 Classes de alerta
#     # -------------------------------------------------------------------------------------------
#     def classificar(x):
#         x = abs(x)
#         if x <= 1:
#             return 'OK'
#         elif x <= 5:
#             return 'LIGEIRA'
#         elif x <= 10:
#             return 'MODERADA'
#         else:
#             return 'GRAVE'

#     df['Classe de diferença'] = df['Diferença (%)'].apply(classificar)

#     # -------------------------------------------------------------------------------------------
#     # 📌 Formatação final
#     # -------------------------------------------------------------------------------------------
#     df = df.rename(columns={
#         'pattern_id': 'Percurso',
#         'shape_dist_traveled_POferta': 'Extensão shape_POferta',
#         'shape_dist_traveled_POperação': 'Extensão shape_POperação',
#         'dist_traveled_stops_POferta': 'Extensão entre paragens_POferta',
#         'dist_traveled_stops_POperação': 'Extensão entre paragens_POperação'
#     })

#     df = df[
#         [
#             'Percurso',
#             'Extensão shape_POferta',
#             'Extensão shape_POperação',
#             'Extensão entre paragens_POferta',
#             'Extensão entre paragens_POperação',
#             'Diferença absoluta (km)',
#             'Diferença (%)',
#             'Classe de diferença'
#         ]
#     ].sort_values('Percurso').reset_index(drop=True)

#     return df, alerts_df


"""
Este módulo calcula e compara a extensão dos percursos GTFS.

Funcionalidades principais:
- Calcula a extensão de cada percurso (pattern_id) a partir das shapes utilizando o valor máximo de shape_dist_traveled.
- Calcula a extensão do percurso a partir das paragens (stop_times).
- Compara as duas extensões dentro do mesmo plano (GTFS) e gera alertas quando a diferença é superior a 1 km.
- Compara a extensão dos percursos entre os dois planos GTFS (Plano de Oferta vs Plano de Operação).
- Calcula diferenças absolutas (km) e percentuais (%) e classifica a gravidade da diferença (OK, LIGEIRA, MODERADA, GRAVE).

Outputs:
- 1 tabela com a comparação final das extensões por percurso.
- 1 tabela de alertas com inconsistências detetadas.
"""

# import pandas as pd
# from analysis.alerts import add_alert


# # ========================================================================================================================================================
# # 1️⃣ Calcula extensões por plano
# # ========================================================================================================================================================

# def compare_extension(
#     gtfs_trips: pd.DataFrame,
#     gtfs_shapes: pd.DataFrame,
#     gtfs_stop_times: pd.DataFrame,
#     gtfs_name: str,
#     alerts_df: pd.DataFrame
# ):

#     # -------------------------------------------------------------------------------------------
#     # 📌 Merge trips + shapes
#     # -------------------------------------------------------------------------------------------
#     merged_shapes = (
#         gtfs_trips[['trip_id', 'pattern_id', 'shape_id']]
#         .merge(
#             gtfs_shapes[['shape_id', 'shape_dist_traveled']],
#             on='shape_id',
#             how='left'
#         )
#     )

#     # -------------------------------------------------------------------------------------------
#     # 📌 Merge trips + stop_times
#     # -------------------------------------------------------------------------------------------
#     merged_stops = (
#         gtfs_trips[['trip_id', 'pattern_id']]
#         .merge(
#             gtfs_stop_times[['trip_id', 'shape_dist_traveled']],
#             on='trip_id',
#             how='left'
#         )
#     )

#     # -------------------------------------------------------------------------------------------
#     # 📌 Normalização de unidades → KM
#     # -------------------------------------------------------------------------------------------
#     merged_shapes['shape_dist_traveled'] = pd.to_numeric(merged_shapes['shape_dist_traveled'], errors='coerce')

#     merged_stops['shape_dist_traveled'] = (pd.to_numeric(merged_stops['shape_dist_traveled'], errors='coerce') )#/ 1000 )

#     # -------------------------------------------------------------------------------------------
#     # 📌 Validação defensiva (evita zeros silenciosos)
#     # -------------------------------------------------------------------------------------------
#     if merged_shapes['shape_dist_traveled'].isna().all():
#         raise ValueError(f"[{gtfs_name}] shape_dist_traveled vazio após merge com shapes")

#     if merged_stops['shape_dist_traveled'].isna().all():
#         raise ValueError(f"[{gtfs_name}] shape_dist_traveled vazio após merge com stop_times")

#     # -------------------------------------------------------------------------------------------
#     # 📌 Extensão pela shape (KM)
#     # -------------------------------------------------------------------------------------------
#     extension_shape = (
#         merged_shapes
#         .groupby('pattern_id')['shape_dist_traveled']
#         .max()
#         .reset_index()
#         .rename(columns={'shape_dist_traveled': f'shape_dist_traveled_{gtfs_name}'})
#     )

#     # -------------------------------------------------------------------------------------------
#     # 📌 Extensão pelas paragens (KM)
#     # -------------------------------------------------------------------------------------------
#     extension_stops = (
#         merged_stops
#         .groupby('pattern_id')['shape_dist_traveled']
#         .max()
#         .reset_index()
#         .rename(columns={'shape_dist_traveled': f'dist_traveled_stops_{gtfs_name}'})
#     )

#     # -------------------------------------------------------------------------------------------
#     # 📌 Comparação interna (shape vs paragens)
#     # -------------------------------------------------------------------------------------------
#     compare_df = extension_shape.merge(extension_stops, on='pattern_id', how='inner')

#     compare_df['diff'] = (
#         compare_df[f'dist_traveled_stops_{gtfs_name}']
#         - compare_df[f'shape_dist_traveled_{gtfs_name}']
#     )

#     # -------------------------------------------------------------------------------------------
#     # 📌 Alertas (> 1 km reais)
#     # -------------------------------------------------------------------------------------------
#     for pattern_id in compare_df.loc[compare_df['diff'].abs() > 1, 'pattern_id']:
#         alerts_df = add_alert(
#             alerts_df,
#             gtfs_name,
#             "Extensões",
#             "GRAVE",
#             "Diferença > 1 km entre extensão por shape e por paragens",
#             str(pattern_id)
#         )

#     return extension_shape, extension_stops, alerts_df


# # ========================================================================================================================================================
# # 2️⃣ Compara extensões entre planos
# # ========================================================================================================================================================

# def compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df):

#     # Extensões – Plano de Oferta
#     ext_shape_oferta, ext_stops_oferta, alerts_df = compare_extension(
#         gtfs_oferta['trips'],
#         gtfs_oferta['shapes'],
#         gtfs_oferta['stop_times'],
#         'POferta',
#         alerts_df
#     )

#     # Extensões – Plano de Operação
#     ext_shape_oper, ext_stops_oper, alerts_df = compare_extension(
#         gtfs_operacao['trips'],
#         gtfs_operacao['shapes'],
#         gtfs_operacao['stop_times'],
#         'POperação',
#         alerts_df
#     )

#     df = (
#         ext_shape_oferta
#         .merge(ext_shape_oper, on='pattern_id', how='inner')
#         .merge(ext_stops_oferta, on='pattern_id', how='inner')
#         .merge(ext_stops_oper, on='pattern_id', how='inner')
#     )

#     # -------------------------------------------------------------------------------------------
#     # 📌 Diferença absoluta (km)
#     # -------------------------------------------------------------------------------------------
#     df['Diferença absoluta (km)'] = (
#         df['shape_dist_traveled_POperação']
#         - df['shape_dist_traveled_POferta']
#     )

#     # -------------------------------------------------------------------------------------------
#     # 📌 Diferença percentual (%)
#     # -------------------------------------------------------------------------------------------
#     df['Diferença (%)'] = (
#         df['Diferença absoluta (km)']
#         / df['shape_dist_traveled_POferta']
#     ) * 100

#     # -------------------------------------------------------------------------------------------
#     # 📌 Classificação
#     # -------------------------------------------------------------------------------------------
#     def classificar(x):
#         x = abs(x)
#         if x <= 1:
#             return 'OK'
#         elif x <= 5:
#             return 'LIGEIRA'
#         elif x <= 10:
#             return 'MODERADA'
#         else:
#             return 'GRAVE'

#     df['Classe de diferença'] = df['Diferença (%)'].apply(classificar)

#     # -------------------------------------------------------------------------------------------
#     # 📌 Formatação final
#     # -------------------------------------------------------------------------------------------
#     df = df.rename(columns={
#         'pattern_id': 'Percurso',
#         'shape_dist_traveled_POferta': 'Extensão shape_POferta',
#         'shape_dist_traveled_POperação': 'Extensão shape_POperação',
#         'dist_traveled_stops_POferta': 'Extensão entre paragens_POferta',
#         'dist_traveled_stops_POperação': 'Extensão entre paragens_POperação'
#     })

#     df = df[
#         [
#             'Percurso',
#             'Extensão shape_POferta',
#             'Extensão shape_POperação',
#             'Extensão entre paragens_POferta',
#             'Extensão entre paragens_POperação',
#             'Diferença absoluta (km)',
#             'Diferença (%)',
#             'Classe de diferença'
#         ]
#     ].sort_values('Percurso').reset_index(drop=True)

#     return df, alerts_df






# import pandas as pd
# from analysis.alerts import add_alert

# # ========================================================================================================================================================
# # 1️⃣ Calcula extensões por plano
# # ========================================================================================================================================================

# def compare_extension(gtfs_trips: pd.DataFrame, gtfs_shapes: pd.DataFrame, gtfs_stop_times: pd.DataFrame,
#                       gtfs_name: str, alerts_df: pd.DataFrame):

#     # Merge trips + shapes
#     merged_shapes = gtfs_trips[['trip_id', 'pattern_id', 'shape_id']].merge(
#         gtfs_shapes[['shape_id', 'shape_dist_traveled']],
#         on='shape_id',
#         how='left'
#     )

#     # Merge trips + stop_times
#     merged_stops = gtfs_trips[['trip_id', 'pattern_id']].merge(
#         gtfs_stop_times[['trip_id', 'shape_dist_traveled']],
#         on='trip_id',
#         how='left'
#     )

#     # Garantir numérico e lidar com NA
#     merged_shapes['shape_dist_traveled'] = pd.to_numeric(merged_shapes['shape_dist_traveled'], errors='coerce').fillna(0)
#     merged_stops['shape_dist_traveled'] = pd.to_numeric(merged_stops['shape_dist_traveled'], errors='coerce').fillna(0)

#     # Extensão pela shape (KM)
#     extension_shape = merged_shapes.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
#     extension_shape = extension_shape.rename(columns={'shape_dist_traveled': f'shape_dist_traveled_{gtfs_name}'})

#     # Extensão pelas paragens (KM)
#     extension_stops = merged_stops.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
#     extension_stops = extension_stops.rename(columns={'shape_dist_traveled': f'dist_traveled_stops_{gtfs_name}'})

#     # Comparação interna (shape vs paragens)
#     compare_df = extension_shape.merge(extension_stops, on='pattern_id', how='inner')
#     compare_df['diff'] = compare_df[f'dist_traveled_stops_{gtfs_name}'] - compare_df[f'shape_dist_traveled_{gtfs_name}']

#     # Alertas (>1 km reais)
#     for pattern_id in compare_df.loc[compare_df['diff'].abs() > 1, 'pattern_id']:
#         alerts_df = add_alert(
#             alerts_df,
#             gtfs_name,
#             "Extensões",
#             "GRAVE",
#             "Diferença > 1 km entre extensão por shape e por paragens",
#             str(pattern_id)
#         )

#     return extension_shape, extension_stops, alerts_df

# # ========================================================================================================================================================
# # 2️⃣ Compara extensões entre planos
# # ========================================================================================================================================================

# def compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df):

#     # Extensões – Plano de Oferta
#     ext_shape_oferta, ext_stops_oferta, alerts_df = compare_extension(
#         gtfs_oferta['trips'], gtfs_oferta['shapes'], gtfs_oferta['stop_times'], 'POferta', alerts_df
#     )

#     # Extensões – Plano de Operação
#     ext_shape_oper, ext_stops_oper, alerts_df = compare_extension(
#         gtfs_operacao['trips'], gtfs_operacao['shapes'], gtfs_operacao['stop_times'], 'POperação', alerts_df
#     )

#     # Merge de todas as extensões
#     df = ext_shape_oferta.merge(ext_shape_oper, on='pattern_id', how='outer') \
#                          .merge(ext_stops_oferta, on='pattern_id', how='outer') \
#                          .merge(ext_stops_oper, on='pattern_id', how='outer')

#     # Diferença absoluta e percentual
#     df['Diferença absoluta (km)'] = df['shape_dist_traveled_POperação'] - df['shape_dist_traveled_POferta']
#     df['Diferença (%)'] = (df['Diferença absoluta (km)'] / df['shape_dist_traveled_POferta'].replace(0, pd.NA)) * 100

#     # Classificação das diferenças
#     def classificar(x):
#         if pd.isna(x):
#             return 'N/A'
#         x = abs(x)
#         if x <= 1:
#             return 'OK'
#         elif x <= 5:
#             return 'LIGEIRA'
#         elif x <= 10:
#             return 'MODERADA'
#         else:
#             return 'GRAVE'

#     df['Classe de diferença'] = df['Diferença (%)'].apply(classificar)

#     # Renomeação para output final
#     df = df.rename(columns={
#         'pattern_id': 'Percurso',
#         'shape_dist_traveled_POferta': 'Extensão shape_POferta',
#         'shape_dist_traveled_POperação': 'Extensão shape_POperação',
#         'dist_traveled_stops_POferta': 'Extensão entre paragens_POferta',
#         'dist_traveled_stops_POperação': 'Extensão entre paragens_POperação'
#     })

#     df = df[['Percurso', 'Extensão shape_POferta', 'Extensão shape_POperação',
#              'Extensão entre paragens_POferta', 'Extensão entre paragens_POperação',
#              'Diferença absoluta (km)', 'Diferença (%)', 'Classe de diferença']] \
#         .sort_values('Percurso').reset_index(drop=True)

#     return df, alerts_df





# import pandas as pd
# from analysis.alerts import add_alert

# # ========================================================================================================================================================
# # 1️⃣ Calcula extensões por plano
# # ========================================================================================================================================================

# def compare_extension(gtfs_trips: pd.DataFrame, gtfs_shapes: pd.DataFrame, gtfs_stop_times: pd.DataFrame,
#                       gtfs_name: str, alerts_df: pd.DataFrame):

#     # Todos os pattern_id existentes no trips
#     all_patterns = pd.DataFrame({'pattern_id': gtfs_trips['pattern_id'].unique()})

#     # Merge trips + shapes
#     merged_shapes = gtfs_trips[['trip_id', 'pattern_id', 'shape_id']].merge(
#         gtfs_shapes[['shape_id', 'shape_dist_traveled']],
#         on='shape_id',
#         how='left'
#     )
#     merged_shapes['shape_dist_traveled'] = pd.to_numeric(merged_shapes['shape_dist_traveled'], errors='coerce')

#     # Agrupa por pattern_id e preenche NA com 0
#     extension_shape = merged_shapes.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
#     extension_shape = all_patterns.merge(extension_shape, on='pattern_id', how='left').fillna(0)
#     extension_shape = extension_shape.rename(columns={'shape_dist_traveled': f'shape_dist_traveled_{gtfs_name}'})

#     # Merge trips + stop_times
#     merged_stops = gtfs_trips[['trip_id', 'pattern_id']].merge(
#         gtfs_stop_times[['trip_id', 'shape_dist_traveled']],
#         on='trip_id',
#         how='left'
#     )
#     merged_stops['shape_dist_traveled'] = pd.to_numeric(merged_stops['shape_dist_traveled'], errors='coerce')

#     extension_stops = merged_stops.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
#     extension_stops = all_patterns.merge(extension_stops, on='pattern_id', how='left').fillna(0)
#     extension_stops = extension_stops.rename(columns={'shape_dist_traveled': f'dist_traveled_stops_{gtfs_name}'})

#     # Comparação interna (shape vs paragens)
#     compare_df = extension_shape.merge(extension_stops, on='pattern_id', how='inner')
#     compare_df['diff'] = compare_df[f'dist_traveled_stops_{gtfs_name}'] - compare_df[f'shape_dist_traveled_{gtfs_name}']

#     # Alertas (>1 km reais)
#     for pattern_id in compare_df.loc[compare_df['diff'].abs() > 1, 'pattern_id']:
#         alerts_df = add_alert(
#             alerts_df,
#             gtfs_name,
#             "Extensões",
#             "GRAVE",
#             "Diferença > 1 km entre extensão por shape e por paragens",
#             str(pattern_id)
#         )

#     return extension_shape, extension_stops, alerts_df


# # ========================================================================================================================================================
# # 2️⃣ Compara extensões entre planos
# # ========================================================================================================================================================

# def compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df):

#     # Extensões – Plano de Oferta
#     ext_shape_oferta, ext_stops_oferta, alerts_df = compare_extension(
#         gtfs_oferta['trips'], gtfs_oferta['shapes'], gtfs_oferta['stop_times'], 'POferta', alerts_df
#     )

#     # Extensões – Plano de Operação
#     ext_shape_oper, ext_stops_oper, alerts_df = compare_extension(
#         gtfs_operacao['trips'], gtfs_operacao['shapes'], gtfs_operacao['stop_times'], 'POperação', alerts_df
#     )

#     # Merge de todas as extensões (outer garante todos os pattern_id)
#     df = ext_shape_oferta.merge(ext_shape_oper, on='pattern_id', how='outer') \
#                          .merge(ext_stops_oferta, on='pattern_id', how='outer') \
#                          .merge(ext_stops_oper, on='pattern_id', how='outer')

#     # Preenche NA com 0 para cálculos
#     df[['shape_dist_traveled_POferta', 'shape_dist_traveled_POperação',
#         'dist_traveled_stops_POferta', 'dist_traveled_stops_POperação']] = \
#         df[['shape_dist_traveled_POferta', 'shape_dist_traveled_POperação',
#             'dist_traveled_stops_POferta', 'dist_traveled_stops_POperação']].fillna(0)

#     # Diferença absoluta e percentual
#     df['Diferença absoluta (km)'] = df['shape_dist_traveled_POperação'] - df['shape_dist_traveled_POferta']
#     df['Diferença (%)'] = df['Diferença absoluta (km)'] / df['shape_dist_traveled_POferta'].replace(0, pd.NA) * 100

#     # Classificação das diferenças
#     def classificar(x):
#         if pd.isna(x):
#             return 'N/A'
#         x = abs(x)
#         if x <= 1:
#             return 'OK'
#         elif x <= 5:
#             return 'LIGEIRA'
#         elif x <= 10:
#             return 'MODERADA'
#         else:
#             return 'GRAVE'

#     df['Classe de diferença'] = df['Diferença (%)'].apply(classificar)

#     # Renomeação para output final
#     df = df.rename(columns={
#         'pattern_id': 'Percurso',
#         'shape_dist_traveled_POferta': 'Extensão shape_POferta',
#         'shape_dist_traveled_POperação': 'Extensão shape_POperação',
#         'dist_traveled_stops_POferta': 'Extensão entre paragens_POferta',
#         'dist_traveled_stops_POperação': 'Extensão entre paragens_POperação'
#     })

#     df = df[['Percurso', 'Extensão shape_POferta', 'Extensão shape_POperação',
#              'Extensão entre paragens_POferta', 'Extensão entre paragens_POperação',
#              'Diferença absoluta (km)', 'Diferença (%)', 'Classe de diferença']] \
#         .sort_values('Percurso').reset_index(drop=True)

#     return df, alerts_df




# import pandas as pd
# from analysis.alerts import add_alert

# # ========================================================================================================================================================
# # 1️⃣ Calcula extensões por plano
# # ========================================================================================================================================================

# def compare_extension(gtfs_trips: pd.DataFrame, gtfs_shapes: pd.DataFrame, gtfs_stop_times: pd.DataFrame,
#                       gtfs_name: str, alerts_df: pd.DataFrame):

#     # Garantir colunas necessárias
#     trips = gtfs_trips.copy()
#     trips['periodo_ano'] = trips.get('periodo_ano', 1)
#     trips['dia_tipo'] = trips.get('dia_tipo', 1)
#     trips['num_circulacoes'] = trips.get('num_circulacoes', 1)

#     # Merge trips + shapes
#     merged_shapes = trips.merge(
#         gtfs_shapes[['shape_id', 'shape_dist_traveled']],
#         on='shape_id',
#         how='left'
#     )
#     merged_shapes['shape_dist_traveled'] = pd.to_numeric(merged_shapes['shape_dist_traveled'], errors='coerce').fillna(0)

#     # Extensão por percurso + periodo + dia
#     extension_shape = merged_shapes.groupby(['pattern_id', 'periodo_ano', 'dia_tipo'])['shape_dist_traveled'].max().reset_index()
#     extension_shape = extension_shape.rename(columns={'shape_dist_traveled': f'Extensão shape_{gtfs_name}'})

#     # Merge trips + stop_times
#     merged_stops = trips.merge(
#         gtfs_stop_times[['trip_id', 'shape_dist_traveled']],
#         on='trip_id',
#         how='left'
#     )
#     merged_stops['shape_dist_traveled'] = pd.to_numeric(merged_stops['shape_dist_traveled'], errors='coerce').fillna(0)

#     # Extensão entre paragens
#     extension_stops = merged_stops.groupby(['pattern_id', 'periodo_ano', 'dia_tipo'])['shape_dist_traveled'].max().reset_index()
#     extension_stops = extension_stops.rename(columns={'shape_dist_traveled': f'Extensão entre paragens_{gtfs_name}'})

#     # Sequência de paragens (count)
#     sequencia = merged_stops.groupby(['pattern_id', 'periodo_ano', 'dia_tipo']).size().reset_index(name=f'Sequencia paragens_{gtfs_name}')

#     # Número total de paragens (sum de stops por percurso)
#     num_paragens = merged_stops.groupby(['pattern_id', 'periodo_ano', 'dia_tipo'])['shape_dist_traveled'].count().reset_index()
#     num_paragens = num_paragens.rename(columns={'shape_dist_traveled': f'Num total paragens_{gtfs_name}'})

#     # Merge tudo
#     df = extension_shape.merge(extension_stops, on=['pattern_id','periodo_ano','dia_tipo'], how='outer') \
#                         .merge(sequencia, on=['pattern_id','periodo_ano','dia_tipo'], how='outer') \
#                         .merge(num_paragens, on=['pattern_id','periodo_ano','dia_tipo'], how='outer') \
#                         .merge(trips[['pattern_id','periodo_ano','dia_tipo','num_circulacoes']], on=['pattern_id','periodo_ano','dia_tipo'], how='left') \
#                         .fillna(0)

#     # VKM total
#     df[f'VKM total ano_{gtfs_name}'] = df['num_circulacoes'] * df[f'Extensão shape_{gtfs_name}']

#     # Alertas (>1 km reais)
#     df['diff'] = df[f'Extensão entre paragens_{gtfs_name}'] - df[f'Extensão shape_{gtfs_name}']
#     for idx in df.index[df['diff'].abs() > 1]:
#         alerts_df = add_alert(
#             alerts_df,
#             gtfs_name,
#             "Extensões",
#             "GRAVE",
#             "Diferença > 1 km entre extensão por shape e por paragens",
#             str(df.loc[idx, 'pattern_id'])
#         )

#     return df, alerts_df


# # ========================================================================================================================================================
# # 2️⃣ Compara extensões entre planos
# # ========================================================================================================================================================

# def compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df):

#     df_oferta, alerts_df = compare_extension(
#         gtfs_oferta['trips'], gtfs_oferta['shapes'], gtfs_oferta['stop_times'], 'POferta', alerts_df
#     )

#     df_oper, alerts_df = compare_extension(
#         gtfs_operacao['trips'], gtfs_operacao['shapes'], gtfs_operacao['stop_times'], 'POperação', alerts_df
#     )

#     # Merge de ambos planos
#     df = df_oferta.merge(df_oper, on=['pattern_id','periodo_ano','dia_tipo'], how='outer', suffixes=('_POferta','_POperação')).fillna(0)

#     # Diferença absoluta e percentual
#     df['Diferença absoluta (km)'] = df['Extensão shape_POperação'] - df['Extensão shape_POferta']
#     df['Diferença (%)'] = df['Diferença absoluta (km)'] / df['Extensão shape_POferta'].replace(0, pd.NA) * 100

#     # Classificação das diferenças
#     def classificar(x):
#         if pd.isna(x):
#             return 'N/A'
#         x = abs(x)
#         if x <= 1:
#             return 'OK'
#         elif x <= 5:
#             return 'LIGEIRA'
#         elif x <= 10:
#             return 'MODERADA'
#         else:
#             return 'GRAVE'

#     df['Classe de diferença'] = df['Diferença (%)'].apply(classificar)

#     # Ordenação final
#     df = df.sort_values(['pattern_id','periodo_ano','dia_tipo']).reset_index(drop=True)

#     return df, alerts_df




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
    ) #* 100

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
