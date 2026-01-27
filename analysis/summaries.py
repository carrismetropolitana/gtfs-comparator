# """
# Este módulo calcula e consolida métricas de circulações, VKM e comparações entre os planos de Oferta e Operação, incluindo alertas de qualidade de dados.

# Funcionalidades principais:
# - Define o schema final do relatório “Total circulações e VKM”, com colunas normalizadas para ambos os planos.
# - Calcula a distância real (km) de cada viagem com base no shape correspondente.
# - Determina o número de dias ativos de cada serviço dentro do período de análise.
# - Calcula os VKM por viagem e serviço, considerando a distância e os dias ativos.
# - Conta as circulações existentes por pattern_id, período do ano e tipo de dia (day_type).
# - Constrói um resumo por plano (Oferta / Operação) agregando circulações, número de paragens e extensão do shape.
# - Calcula o VKM total anual por percurso, a partir da extensão do shape e do número de circulações.
# - Gera alertas sempre que forem detetadas datas com exception_type = 2 nos calendar_dates de qualquer plano.
# - Consolida alertas por plano e cria uma tabela de alertas completa.
# - Gera uma tabela comparativa global entre os planos, normalizando colunas e garantindo o schema final.
# - Cria um resumo de contrato comparando VKM dos planos com o VKM contratado.
# - Produz uma tabela com o período de análise e a data de execução.
# - Fornece os resumos detalhados finais para cada plano.

# Outputs:
# - 1 DataFrame com o resumo de circulações e VKM por percurso, período e dia tipo, para cada plano.
# - 1 DataFrame comparativo consolidado (Oferta vs Operação) com o schema final definido.
# - 1 DataFrame de alertas com todas as inconformidades detetadas.
# - 1 DataFrame com o resumo do contrato (VKM) e diferenças relativas.
# - 1 DataFrame com o período de análise e data de execução.
# """

# import pandas as pd
# from analysis.alerts import add_alert, init_alerts_df
# import numpy as np
# import logging


# # ========================================================================================================================================================
# # 0️⃣ Schema final — folha "Total circulações e VKM"
# # ========================================================================================================================================================

# TOTAL_CIRCULACOES_VKM_COLUMNS = [
#     'Percurso',
#     'Periodo do ano',
#     'Dia tipo',

#     # -------- Oferta --------
#     'Num total circulações ano_POferta',
#     'Num total paragens_POferta',
#     'Sequencia paragens_POferta',
#     'Extensão shape_POferta',
#     'VKM total ano_POferta',

#     # -------- Operação --------
#     'Num total circulações ano_POperação',
#     'Num total paragens_POperação',
#     'Sequencia paragens_POperação',
#     'Extensão shape_POperação',
#     'VKM total ano_POperação',
# ]

# COLUMN_RENAME_MAP = {
#     # -------- Oferta --------
#     'result_POferta': 'Num total circulações ano_POferta',
#     'stop_id_POferta': 'Num total paragens_POferta',
#     'stop_sequence_POferta': 'Sequencia paragens_POferta',
#     'shape_dist_traveled_POferta': 'Extensão shape_POferta',

#     # -------- Operação --------
#     'result_POperação': 'Num total circulações ano_POperação',
#     'stop_id_POperação': 'Num total paragens_POperação',
#     'stop_sequence_POperação': 'Sequencia paragens_POperação',
#     'shape_dist_traveled_POperação': 'Extensão shape_POperação',
# }

# # ========================================================================================================================================================
# # 1️⃣ Calcula a distância real de cada trip
# # ========================================================================================================================================================

# def calculate_trip_distance_km(trips, shapes):
#     shape_dist = (shapes.groupby('shape_id')['shape_dist_traveled'].max().reset_index())
#     shape_dist['distance_km'] = shape_dist['shape_dist_traveled'].apply(lambda x: x / 1000 if x > 1000 else x)

#     return trips.merge(shape_dist[['shape_id', 'distance_km']], on='shape_id', how='left')[['trip_id', 'pattern_id', 'service_id', 'distance_km']]

# # ========================================================================================================================================================
# # 2️⃣ Calcula o número de dias que cada serviço esteve ativo
# # ========================================================================================================================================================

# def calculate_service_days(calendar_dates, start_date, end_date):
#     calendar_dates = calendar_dates.copy()
#     calendar_dates['date'] = pd.to_datetime(calendar_dates['date'])

#     mask = (
#         (calendar_dates['date'] >= pd.to_datetime(start_date)) &
#         (calendar_dates['date'] <= pd.to_datetime(end_date))
#     )

#     return (calendar_dates[mask].groupby('service_id')['date'].nunique().reset_index(name='n_days'))

# # ========================================================================================================================================================
# # 3️⃣ Calcula os VKM contratuais
# # ========================================================================================================================================================

# # def calculate_vkm(gtfs, start_date, end_date):
# #     trips_dist = calculate_trip_distance_km(gtfs['trips'], gtfs['shapes'])
# #     service_days = calculate_service_days(gtfs['calendar_dates'], start_date, end_date)

# #     return (trips_dist.merge(service_days, on='service_id', how='inner').assign(vkm=lambda df: df.distance_km * df.n_days))

# def calculate_vkm(gtfs, start_date, end_date):
#     # Distância por viagem (km)
#     trips_dist = calculate_trip_distance_km(gtfs['trips'], gtfs['shapes'])

#     # Dias de serviço no intervalo
#     service_days = calculate_service_days(gtfs['calendar_dates'], start_date, end_date)

#     # --- Validações importantes ---
#     if trips_dist.empty:
#         logging.warning("calculate_vkm: trips_dist está vazio. Verifique trips/shapes.")
#         return pd.DataFrame(columns=['service_id', 'distance_km', 'n_days', 'vkm'])

#     if service_days.empty:
#         logging.warning("calculate_vkm: service_days está vazio. Verifique calendar_dates e o intervalo de datas.")
#         return pd.DataFrame(columns=['service_id', 'distance_km', 'n_days', 'vkm'])

#     if 'service_id' not in trips_dist.columns:
#         logging.error("calculate_vkm: trips_dist não contém 'service_id'. Merge impossível.")
#         return pd.DataFrame(columns=['service_id', 'distance_km', 'n_days', 'vkm'])

#     if 'distance_km' not in trips_dist.columns:
#         logging.error("calculate_vkm: trips_dist não contém 'distance_km'.")
#         return pd.DataFrame(columns=['service_id', 'distance_km', 'n_days', 'vkm'])

#     # Garantir que distance_km é numérico
#     trips_dist['distance_km'] = pd.to_numeric(trips_dist['distance_km'], errors='coerce').fillna(0)

#     # --- Merge e cálculo do VKM ---
#     merged = trips_dist.merge(service_days, on='service_id', how='inner')

#     if merged.empty:
#         logging.warning("calculate_vkm: merge resultou vazio. Verifique service_id entre trips e calendar_dates.")
#         return pd.DataFrame(columns=['service_id', 'distance_km', 'n_days', 'vkm'])

#     return merged.assign(vkm=lambda df: df.distance_km * df.n_days)


# # ========================================================================================================================================================
# # 4️⃣ Calcula as circulações (existentes) por pattern_id; period; e day_type
# # ========================================================================================================================================================

# def compute_trips_per_pattern_day_type_period(trips_df, calendar_dates_df):
#     trips_calendar = pd.merge(trips_df, calendar_dates_df, on='service_id')

#     trips_per_pattern = (trips_calendar.groupby(['pattern_id', 'service_id', 'period', 'day_type'])['trip_id'].nunique().reset_index())
#     days_per_pattern = (trips_calendar.groupby(['pattern_id', 'service_id', 'period', 'day_type'])['date'].nunique().reset_index().rename(columns={'date': 'days_count'}))

#     merged_result = pd.merge(days_per_pattern, trips_per_pattern, on=['pattern_id', 'service_id', 'period', 'day_type'], how='left')
#     merged_result['result'] = merged_result['days_count'] * merged_result['trip_id']

#     return merged_result

# # ========================================================================================================================================================
# # 5️⃣ Constrói o resumo por plano (Oferta / Operação)
# # ========================================================================================================================================================

# def build_plan_summary(merged_trips_result, stops_comparison_result, extension_df, plan_name):
#     pivot_table = (merged_trips_result.pivot_table(index=['pattern_id', 'period', 'day_type'], values='result', aggfunc='sum').reset_index())

#     resumo = pd.merge(pivot_table, stops_comparison_result, on='pattern_id', how='outer')
#     resumo = pd.merge(resumo, extension_df, on='pattern_id', how='outer')

#     for col in ['shape_dist_traveled', 'dist_traveled_stops', 'result']:
#         if col not in resumo.columns:
#             resumo[col] = 0
#         resumo[col] = pd.to_numeric(resumo[col], errors='coerce').fillna(0)

#     resumo['VKM total ano'] = resumo['shape_dist_traveled'] * resumo['result']

#     resumo['Plano'] = plan_name

#     resumo = pd.merge(resumo, merged_trips_result[['pattern_id', 'period', 'day_type', 'service_id', 'days_count', 'trip_id']], on=['pattern_id', 'period', 'day_type'], how='left')

#     return resumo

# # ========================================================================================================================================================
# # 6️⃣ Gera um alerta  sempre que encontrar alguma data classificada com -> exception_type = 2
# # ========================================================================================================================================================

# def add_exception_type_alerts(calendar_dates_gtfs, plan_name, alerts_df):
#     exception_dates = calendar_dates_gtfs[calendar_dates_gtfs['exception_type'] == 2]['date']

#     if not exception_dates.empty:
#         dates_formatted = ', '.join(pd.to_datetime(exception_dates).dt.strftime('%Y-%m-%d'))
#         alerts_df = add_alert(
#             alerts_df,
#             plan_name,
#             "Datas com exception_type 2",
#             "MUITO GRAVE",
#             "Existem datas com exception_type = 2",
#             dates_formatted
#         )

#     return alerts_df

# # ========================================================================================================================================================
# # 7️⃣ Gera um alerta por cada problemática
# # ========================================================================================================================================================

# def build_alerts(calendar_dates_gtfs_POferta, calendar_dates_gtfs_POperação, alerts_df=None):
#     if alerts_df is None:
#         alerts_df = init_alerts_df()

#     for plan_name, df in [
#         ('PLANO DE OFERTA', calendar_dates_gtfs_POferta),
#         ('PLANO DE OPERAÇÃO', calendar_dates_gtfs_POperação)
#     ]:
#         df_excep = df[df.get('exception_type', 0) == 2]

#         for _, row in df_excep.iterrows():
#             alerts_df = add_alert(
#                 alerts_df,
#                 plan_name,
#                 "Exception Type",
#                 'MUITO GRAVE',
#                 "Data classificada com exception_type = 2",
#                 pd.to_datetime(row['date']).strftime('%Y-%m-%d')
#             )

#     return alerts_df

# # ========================================================================================================================================================
# # 8️⃣ Gera uma tabela comparativa - Oferta vs. Operação
# # ========================================================================================================================================================

# def build_global_comparison(resumo_oferta, resumo_operacao):
#     merged_all = pd.merge(
#         resumo_oferta,
#         resumo_operacao,
#         on=['pattern_id', 'period', 'day_type'],
#         how='outer',
#         suffixes=('_POferta', '_POperacao')
#     )

#     merged_all.columns = [
#         col.replace('_POperacao', '_POperação')
#         for col in merged_all.columns
#     ]

#     merged_all.rename(columns={
#         'pattern_id': 'Percurso',
#         'period': 'Periodo do ano',
#         'day_type': 'Dia tipo'
#     }, inplace=True)

#     merged_all.rename(columns=COLUMN_RENAME_MAP, inplace=True)

#     for col in TOTAL_CIRCULACOES_VKM_COLUMNS:
#         if col not in merged_all.columns:
#             merged_all[col] = 0

#     return merged_all[TOTAL_CIRCULACOES_VKM_COLUMNS]

# # ========================================================================================================================================================
# # 9️⃣ Resumo de contrato (VKM)
# # ========================================================================================================================================================

# # def build_contract_summary(
# #     gtfs_POferta,
# #     gtfs_POperacao,
# #     start_date,
# #     end_date,
# #     vkm_contrato,
# #     gtfs_offer_name,
# #     gtfs_operation_name
# # ):

# #     vkm_poferta_df = calculate_vkm(gtfs_POferta, start_date, end_date)
# #     vkm_poperacao_df = calculate_vkm(gtfs_POperacao, start_date, end_date)

# #     total_vkm_poferta = vkm_poferta_df['vkm'].sum()
# #     total_vkm_poperacao = vkm_poperacao_df['vkm'].sum()

# #     diff_poferta_pct = (total_vkm_poferta / vkm_contrato) * 100
# #     diff_poperacao_pct = (total_vkm_poperacao / vkm_contrato) * 100

# #     return pd.DataFrame({
# #         'Designação GTFS': [gtfs_offer_name, gtfs_operation_name, 'Contrato'],
# #         'VKM\n(do plano)': [total_vkm_poferta, total_vkm_poperacao, vkm_contrato],
# #         'Diferença relativa ao contrato (%)': [diff_poferta_pct, diff_poperacao_pct, 0]
# #     })

# def build_contract_summary(
#     gtfs_POferta,
#     gtfs_POperacao,
#     start_date,
#     end_date,
#     vkm_contrato,
#     gtfs_offer_name,
#     gtfs_operation_name
# ):

#     # Calcular VKM para cada plano
#     vkm_poferta_df = calculate_vkm(gtfs_POferta, start_date, end_date)
#     vkm_poperacao_df = calculate_vkm(gtfs_POperacao, start_date, end_date)

#     # Garantir que a coluna existe e tratar NaNs
#     total_vkm_poferta = vkm_poferta_df.get('vkm', pd.Series(dtype=float)).fillna(0).sum()
#     total_vkm_poperacao = vkm_poperacao_df.get('vkm', pd.Series(dtype=float)).fillna(0).sum()

#     # Garantir que o VKM do contrato é válido
#     vkm_contrato = float(vkm_contrato) if vkm_contrato not in [None, 0, np.nan] else 0

#     # Evitar divisão por zero
#     diff_poferta_pct = (total_vkm_poferta / vkm_contrato) * 100 if vkm_contrato else 0
#     diff_poperacao_pct = (total_vkm_poperacao / vkm_contrato) * 100 if vkm_contrato else 0

#     return pd.DataFrame({
#         'Designação GTFS': [gtfs_offer_name, gtfs_operation_name, 'Contrato'],
#         'VKM\n(do plano)': [total_vkm_poferta, total_vkm_poperacao, vkm_contrato],
#         'Diferença relativa ao contrato (%)': [diff_poferta_pct, diff_poperacao_pct, 0]
#     })


# # ========================================================================================================================================================
# # 1️⃣0️⃣ Período da análise
# # ========================================================================================================================================================

# def build_analysis_period_table(start_date, end_date):
#     return pd.DataFrame({
#         'Período da Análise': [
#             f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]} "
#             f"a {end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
#         ],
#         'Data da Análise': [pd.Timestamp.now().strftime('%d/%m/%Y')]
#     })

# # ========================================================================================================================================================
# # 1️⃣1️⃣ Estutura final
# # ========================================================================================================================================================

# def build_detailed_plan_summaries(resumo_oferta, resumo_operacao):
#     return resumo_oferta.copy(), resumo_operacao.copy()

# """
# Este módulo calcula e consolida métricas de circulações, VKM e comparações entre os planos de Oferta e Operação, incluindo alertas de qualidade de dados.
# """

# import pandas as pd
# import numpy as np
# import logging
# from analysis.alerts import add_alert, init_alerts_df

# # ========================================================================================================================================================
# # 0️⃣ Schema final — folha "Total circulações e VKM"
# # ========================================================================================================================================================

# TOTAL_CIRCULACOES_VKM_COLUMNS = [
#     'Percurso',
#     'Periodo do ano',
#     'Dia tipo',

#     # -------- Oferta --------
#     'Num total circulações ano_POferta',
#     'Num total paragens_POferta',
#     'Sequencia paragens_POferta',
#     'Extensão shape_POferta',
#     'VKM total ano_POferta',

#     # -------- Operação --------
#     'Num total circulações ano_POperação',
#     'Num total paragens_POperação',
#     'Sequencia paragens_POperação',
#     'Extensão shape_POperação',
#     'VKM total ano_POperação',
# ]

# COLUMN_RENAME_MAP = {
#     'result_POferta': 'Num total circulações ano_POferta',
#     'stop_id_POferta': 'Num total paragens_POferta',
#     'stop_sequence_POferta': 'Sequencia paragens_POferta',
#     'shape_dist_traveled_POferta': 'Extensão shape_POferta',
#     'VKM total ano_POferta': 'VKM total ano_POferta',

#     'result_POperação': 'Num total circulações ano_POperação',
#     'stop_id_POperação': 'Num total paragens_POperação',
#     'stop_sequence_POperação': 'Sequencia paragens_POperação',
#     'shape_dist_traveled_POperação': 'Extensão shape_POperação',
#     'VKM total ano_POperação': 'VKM total ano_POperação',
# }

# # ========================================================================================================================================================
# # 1️⃣ Circulações por pattern_id, período e dia tipo
# # ========================================================================================================================================================

# def compute_trips_per_pattern_day_type_period(trips_df, calendar_dates_df):
#     logging.info("A calcular circulações por pattern, período e dia tipo...")

#     trips_calendar = trips_df.merge(calendar_dates_df, on='service_id', how='inner')

#     trips_per_day = (
#         trips_calendar
#         .groupby(['pattern_id', 'service_id', 'period', 'day_type'])['trip_id']
#         .nunique()
#         .reset_index(name='trips_per_day')
#     )

#     days_count = (
#         trips_calendar
#         .groupby(['pattern_id', 'service_id', 'period', 'day_type'])['date']
#         .nunique()
#         .reset_index(name='days_count')
#     )

#     merged = trips_per_day.merge(
#         days_count,
#         on=['pattern_id', 'service_id', 'period', 'day_type'],
#         how='inner'
#     )

#     merged['result'] = merged['trips_per_day'] * merged['days_count']

#     return merged

# # ========================================================================================================================================================
# # 2️⃣ Resumo por plano (Oferta / Operação)
# # ========================================================================================================================================================

# def build_plan_summary(merged_trips_result, stops_count_df, extension_df, plan_name):
#     logging.info(f"A construir resumo do {plan_name}...")

#     pivot = (
#         merged_trips_result
#         .pivot_table(
#             index=['pattern_id', 'period', 'day_type'],
#             values='result',
#             aggfunc='sum'
#         )
#         .reset_index()
#     )

#     resumo = pivot.merge(stops_count_df, on='pattern_id', how='left')
#     resumo = resumo.merge(extension_df, on='pattern_id', how='left')

#     for col in ['shape_dist_traveled', 'result']:
#         if col not in resumo.columns:
#             resumo[col] = 0
#         resumo[col] = pd.to_numeric(resumo[col], errors='coerce').fillna(0)

#     resumo['VKM total ano'] = resumo['shape_dist_traveled'] * resumo['result']
#     resumo['Plano'] = plan_name

#     logging.info(f"Resumo do {plan_name} concluído.")
#     return resumo


# # ========================================================================================================================================================
# # 3️⃣ Alertas – exception_type = 2
# # ========================================================================================================================================================

# def add_exception_type_alerts(calendar_dates_gtfs, plan_name, alerts_df):
#     exception_dates = calendar_dates_gtfs[calendar_dates_gtfs['exception_type'] == 2]['date']

#     if not exception_dates.empty:
#         alerts_df = add_alert(
#             alerts_df,
#             plan_name,
#             "Datas com exception_type 2",
#             "MUITO GRAVE",
#             "Existem datas com exception_type = 2",
#             ', '.join(pd.to_datetime(exception_dates).dt.strftime('%Y-%m-%d'))
#         )

#     return alerts_df

# # ========================================================================================================================================================
# # 4️⃣ Comparação global Oferta vs Operação
# # ========================================================================================================================================================

# def build_global_comparison(resumo_oferta, resumo_operacao):
#     logging.info("A construir comparação global Oferta vs Operação...")

#     merged = resumo_oferta.merge(
#         resumo_operacao,
#         on=['pattern_id', 'period', 'day_type'],
#         how='outer',
#         suffixes=('_POferta', '_POperação')
#     )

#     merged.rename(columns={
#         'pattern_id': 'Percurso',
#         'period': 'Periodo do ano',
#         'day_type': 'Dia tipo'
#     }, inplace=True)

#     merged.rename(columns=COLUMN_RENAME_MAP, inplace=True)

#     for col in TOTAL_CIRCULACOES_VKM_COLUMNS:
#         if col not in merged.columns:
#             merged[col] = 0

#     return merged[TOTAL_CIRCULACOES_VKM_COLUMNS]

# # ========================================================================================================================================================
# # 5️⃣ Resumo de contrato (VKM)
# # ========================================================================================================================================================

# def build_contract_summary(
#     *,
#     gtfs_POferta,
#     gtfs_POperacao,
#     start_date,
#     end_date,
#     vkm_contrato,
#     gtfs_offer_name,
#     gtfs_operation_name
# ):
#     logging.info("A calcular resumo contratual (VKM)...")

#     vkm_poferta_df = calculate_vkm(gtfs_POferta, start_date, end_date)
#     vkm_poperacao_df = calculate_vkm(gtfs_POperacao, start_date, end_date)

#     total_vkm_poferta = (
#         vkm_poferta_df['vkm'].sum()
#         if 'vkm' in vkm_poferta_df.columns else 0
#     )

#     total_vkm_poperacao = (
#         vkm_poperacao_df['vkm'].sum()
#         if 'vkm' in vkm_poperacao_df.columns else 0
#     )

#     vkm_contrato = float(vkm_contrato) if vkm_contrato not in [None, 0, np.nan] else 0

#     diff_poferta_pct = (total_vkm_poferta / vkm_contrato) * 100 if vkm_contrato else 0
#     diff_poperacao_pct = (total_vkm_poperacao / vkm_contrato) * 100 if vkm_contrato else 0

#     logging.info("Resumo contratual calculado com sucesso.")

#     return pd.DataFrame({
#         'Designação GTFS': [
#             gtfs_offer_name,
#             gtfs_operation_name,
#             'Contrato'
#         ],
#         'VKM\n(do plano)': [
#             total_vkm_poferta,
#             total_vkm_poperacao,
#             vkm_contrato
#         ],
#         'Diferença relativa ao contrato (%)': [
#             diff_poferta_pct,
#             diff_poperacao_pct,
#             0
#         ]
#     })


# # ========================================================================================================================================================
# # 6️⃣ Período da análise
# # ========================================================================================================================================================

# def build_analysis_period_table(start_date, end_date):
#     return pd.DataFrame({
#         'Período da Análise': [
#             f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]} "
#             f"a {end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
#         ],
#         'Data da Análise': [pd.Timestamp.now().strftime('%d/%m/%Y')]
#     })

# # ========================================================================================================================================================
# # 7️⃣ Estrutura final
# # ========================================================================================================================================================

# def build_detailed_plan_summaries(resumo_oferta, resumo_operacao):
#     return resumo_oferta.copy(), resumo_operacao.copy()

import logging
import pandas as pd
import numpy as np

from analysis.vkm import calculate_vkm

# =====================================================================================
# 🔧 Configuração de logging (narrativo, sem timestamps)
# =====================================================================================

logger = logging.getLogger(__name__)

# =====================================================================================
# 🔁 Utilitários internos
# =====================================================================================

def _safe_numeric(value):
    """
    Conversão segura para float (Series ou escalar).
    """
    if isinstance(value, pd.Series):
        return pd.to_numeric(value, errors="coerce").fillna(0)
    try:
        return float(value)
    except Exception:
        return 0.0

# =====================================================================================
# 🚍 Circulações por pattern / período / dia tipo
# =====================================================================================

def compute_trips_per_pattern_day_type_period(trips_df, calendar_dates_df):
    logger.info("🚍 A calcular circulações por percurso, tipo de dia e período")

    df = trips_df.merge(calendar_dates_df[["service_id", "period", "day_type", "date"]], on="service_id", how="inner")

    grouped = (df.groupby(["pattern_id", "period", "day_type"], dropna=False)["trip_id"].nunique().reset_index(name="n_trips"))

    days = (df.groupby(["pattern_id", "period", "day_type"],dropna=False)["date"].nunique().reset_index(name="n_days"))

    result = grouped.merge(days, on=["pattern_id", "period", "day_type"], how="left")

    result["total_circulacoes"] = (result["n_trips"] * result["n_days"])

    return result

# =====================================================================================
# 📊 Resumo por plano (operacional)
# =====================================================================================

def build_plan_summary(
    merged_trips_df,
    stops_count_df,
    extension_df,
    plan_name
):
    logger.info(f"📊 A construir resumo do {plan_name}")

    resumo = {
        "Plano": plan_name,
        "Total circulações": _safe_numeric(
            merged_trips_df["total_circulacoes"].sum()
        )
    }

    # Número médio de paragens
    if (stops_count_df is not None
        and "n_stops" in stops_count_df.columns
    ):
        resumo["Número médio de paragens"] = _safe_numeric(
            stops_count_df["n_stops"].mean()
        )
    else:
        resumo["Número médio de paragens"] = 0

    # Extensão média dos percursos
    if (
        extension_df is not None
        and "extension_km" in extension_df.columns
    ):
        resumo["Extensão média dos percursos (km)"] = _safe_numeric(
            extension_df["extension_km"].mean()
        )
    else:
        resumo["Extensão média dos percursos (km)"] = 0

    return pd.DataFrame([resumo])

# =====================================================================================
# 🌍 Comparação global entre planos
# =====================================================================================

def build_global_comparison(resumo_oferta, resumo_operacao):
    logger.info("🌍 A construir comparação global Oferta vs Operação")

    return pd.concat([resumo_oferta, resumo_operacao], ignore_index=True)

# =====================================================================================
# 📐 Resumo contratual (VKM OFICIAL)
# =====================================================================================

def build_contract_summary(
    gtfs_POferta,
    gtfs_POperacao,
    start_date,
    end_date,
    vkm_contrato,
    gtfs_offer_name,
    gtfs_operation_name
):
    logger.info("📐 A calcular resumo contratual (VKM)")

    vkm_poferta_df = calculate_vkm(
        gtfs_POferta,
        start_date,
        end_date
    )

    vkm_poperacao_df = calculate_vkm(
        gtfs_POperacao,
        start_date,
        end_date
    )

    total_vkm_poferta = _safe_numeric(
        vkm_poferta_df["vkm"].sum()
    )
    total_vkm_poperacao = _safe_numeric(
        vkm_poperacao_df["vkm"].sum()
    )

    vkm_contrato = _safe_numeric(vkm_contrato)

    diff_poferta_pct = (
        (total_vkm_poferta / vkm_contrato) * 100
        if vkm_contrato else 0
    )
    diff_poperacao_pct = (
        (total_vkm_poperacao / vkm_contrato) * 100
        if vkm_contrato else 0
    )

    return pd.DataFrame({
        "Designação GTFS": [
            gtfs_offer_name,
            gtfs_operation_name,
            "Contrato"
        ],
        "VKM\n(do plano)": [
            total_vkm_poferta,
            total_vkm_poperacao,
            vkm_contrato
        ],
        "Diferença relativa ao contrato (%)": [
            diff_poferta_pct,
            diff_poperacao_pct,
            0
        ]
    })

# =====================================================================================
# 📅 Tabela do período de análise
# =====================================================================================

def build_analysis_period_table(start_date, end_date):
    logger.info("📅 A construir tabela do período de análise")

    return pd.DataFrame({"Data início": [start_date], "Data fim": [end_date]})