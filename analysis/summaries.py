import pandas as pd
from analysis.alerts import add_alert, init_alerts_df
import numpy as np

# ==================================================
# SCHEMA FINAL — folha "Total circulações e VKM"
# ==================================================

TOTAL_CIRCULACOES_VKM_COLUMNS = [
    'Percurso',
    'Periodo do ano',
    'Dia tipo',

    # -------- Oferta --------
    'Num total circulações ano_POferta',
    'Num total paragens_POferta',
    'Sequencia paragens_POferta',
    'Extensão shape_POferta',
    'VKM total ano_POferta',

    # -------- Operação --------
    'Num total circulações ano_POperação',
    'Num total paragens_POperação',
    'Sequencia paragens_POperação',
    'Extensão shape_POperação',
    'VKM total ano_POperação',
]

COLUMN_RENAME_MAP = {
    # -------- Oferta --------
    'result_POferta': 'Num total circulações ano_POferta',
    'stop_id_POferta': 'Num total paragens_POferta',
    'stop_sequence_POferta': 'Sequencia paragens_POferta',
    'shape_dist_traveled_POferta': 'Extensão shape_POferta',

    # -------- Operação --------
    'result_POperação': 'Num total circulações ano_POperação',
    'stop_id_POperação': 'Num total paragens_POperação',
    'stop_sequence_POperação': 'Sequencia paragens_POperação',
    'shape_dist_traveled_POperação': 'Extensão shape_POperação',
}

# ==================================================
# VKM — CÁLCULO CORRETO (BASE TRIP)
# ==================================================

def calculate_trip_distance_km(trips, shapes):
    shape_dist = (
        shapes
        .groupby('shape_id')['shape_dist_traveled']
        .max()
        .reset_index()
    )

    shape_dist['distance_km'] = shape_dist['shape_dist_traveled'].apply(
        lambda x: x / 1000 if x > 1000 else x
    )

    return trips.merge(
        shape_dist[['shape_id', 'distance_km']],
        on='shape_id',
        how='left'
    )[['trip_id', 'pattern_id', 'service_id', 'distance_km']]


def calculate_service_days(calendar_dates, start_date, end_date):
    calendar_dates = calendar_dates.copy()
    calendar_dates['date'] = pd.to_datetime(calendar_dates['date'])

    mask = (
        (calendar_dates['date'] >= pd.to_datetime(start_date)) &
        (calendar_dates['date'] <= pd.to_datetime(end_date))
    )

    return (
        calendar_dates[mask]
        .groupby('service_id')['date']
        .nunique()
        .reset_index(name='n_days')
    )


def calculate_vkm(gtfs, start_date, end_date):
    trips_dist = calculate_trip_distance_km(
        gtfs['trips'],
        gtfs['shapes']
    )

    service_days = calculate_service_days(
        gtfs['calendar_dates'],
        start_date,
        end_date
    )

    return (
        trips_dist
        .merge(service_days, on='service_id', how='inner')
        .assign(vkm=lambda df: df.distance_km * df.n_days)
    )

# ==================================================
# 1️⃣ Cálculo de circulações
# ==================================================

def compute_trips_per_pattern_day_type_period(trips_df, calendar_dates_df):
    trips_calendar = pd.merge(trips_df, calendar_dates_df, on='service_id')

    trips_per_pattern = (
        trips_calendar
        .groupby(['pattern_id', 'service_id', 'period', 'day_type'])['trip_id']
        .nunique()
        .reset_index()
    )

    days_per_pattern = (
        trips_calendar
        .groupby(['pattern_id', 'service_id', 'period', 'day_type'])['date']
        .nunique()
        .reset_index()
        .rename(columns={'date': 'days_count'})
    )

    merged_result = pd.merge(
        days_per_pattern,
        trips_per_pattern,
        on=['pattern_id', 'service_id', 'period', 'day_type'],
        how='left'
    )

    merged_result['result'] = merged_result['days_count'] * merged_result['trip_id']

    return merged_result

# ==================================================
# 2️⃣ Resumo por plano (Oferta / Operação)
# ==================================================

def build_plan_summary(merged_trips_result, stops_comparison_result, extension_df, plan_name):
    pivot_table = (
        merged_trips_result
        .pivot_table(
            index=['pattern_id', 'period', 'day_type'],
            values='result',
            aggfunc='sum'
        )
        .reset_index()
    )

    resumo = pd.merge(
        pivot_table,
        stops_comparison_result,
        on='pattern_id',
        how='outer'
    )

    resumo = pd.merge(
        resumo,
        extension_df,
        on='pattern_id',
        how='outer'
    )

    for col in ['shape_dist_traveled', 'dist_traveled_stops', 'result']:
        if col not in resumo.columns:
            resumo[col] = 0
        resumo[col] = pd.to_numeric(resumo[col], errors='coerce').fillna(0)

    # ⚠️ VKM aqui é apenas INDICATIVO (não contratual)
    resumo['VKM total ano'] = resumo['shape_dist_traveled'] * resumo['result']

    resumo['Plano'] = plan_name

    resumo = pd.merge(
        resumo,
        merged_trips_result[['pattern_id', 'period', 'day_type', 'service_id', 'days_count', 'trip_id']],
        on=['pattern_id', 'period', 'day_type'],
        how='left'
    )

    return resumo

# ==================================================
# 3️⃣ Alertas — exception_type == 2
# ==================================================

def add_exception_type_alerts(calendar_dates_gtfs, plan_name, alerts_df):
    exception_dates = calendar_dates_gtfs[calendar_dates_gtfs['exception_type'] == 2]['date']

    if not exception_dates.empty:
        dates_formatted = ', '.join(pd.to_datetime(exception_dates).dt.strftime('%Y-%m-%d'))
        alerts_df = add_alert(
            alerts_df,
            plan_name,
            "Datas com exception_type 2",
            "MUITO GRAVE",
            "Existem datas com exception_type = 2",
            dates_formatted
        )

    return alerts_df

# ==================================================
# 4️⃣ Alertas gerais
# ==================================================

def build_alerts(calendar_dates_gtfs_POferta, calendar_dates_gtfs_POperação, alerts_df=None):
    if alerts_df is None:
        alerts_df = init_alerts_df()

    for plan_name, df in [
        ('PLANO DE OFERTA', calendar_dates_gtfs_POferta),
        ('PLANO DE OPERAÇÃO', calendar_dates_gtfs_POperação)
    ]:
        df_excep = df[df.get('exception_type', 0) == 2]

        for _, row in df_excep.iterrows():
            alerts_df = add_alert(
                alerts_df,
                plan_name,
                "Exception Type",
                'MUITO GRAVE',
                "Data classificada com exception_type = 2",
                pd.to_datetime(row['date']).strftime('%Y-%m-%d')
            )

    return alerts_df

# ==================================================
# 5️⃣ Comparação global
# ==================================================

def build_global_comparison(resumo_oferta, resumo_operacao):
    merged_all = pd.merge(
        resumo_oferta,
        resumo_operacao,
        on=['pattern_id', 'period', 'day_type'],
        how='outer',
        suffixes=('_POferta', '_POperacao')
    )

    merged_all.columns = [
        col.replace('_POperacao', '_POperação')
        for col in merged_all.columns
    ]

    merged_all.rename(columns={
        'pattern_id': 'Percurso',
        'period': 'Periodo do ano',
        'day_type': 'Dia tipo'
    }, inplace=True)

    merged_all.rename(columns=COLUMN_RENAME_MAP, inplace=True)

    for col in TOTAL_CIRCULACOES_VKM_COLUMNS:
        if col not in merged_all.columns:
            merged_all[col] = 0

    return merged_all[TOTAL_CIRCULACOES_VKM_COLUMNS]

# ==================================================
# 6️⃣ Resumo de contrato (VKM CORRETO)
# ==================================================

def build_contract_summary(
    gtfs_POferta,
    gtfs_POperacao,
    start_date,
    end_date,
    vkm_contrato,
    gtfs_offer_name,
    gtfs_operation_name
):

    vkm_poferta_df = calculate_vkm(gtfs_POferta, start_date, end_date)
    vkm_poperacao_df = calculate_vkm(gtfs_POperacao, start_date, end_date)

    total_vkm_poferta = vkm_poferta_df['vkm'].sum()
    total_vkm_poperacao = vkm_poperacao_df['vkm'].sum()

    diff_poferta_pct = (total_vkm_poferta / vkm_contrato) * 100
    diff_poperacao_pct = (total_vkm_poperacao / vkm_contrato) * 100

    return pd.DataFrame({
        'Designação GTFS': [gtfs_offer_name, gtfs_operation_name, 'Contrato'],
        'VKM\n(do plano)': [total_vkm_poferta, total_vkm_poperacao, vkm_contrato],
        'Diferença relativa ao contrato (%)': [diff_poferta_pct, diff_poperacao_pct, 0]
    })

# ==================================================
# 7️⃣ Período da análise
# ==================================================

def build_analysis_period_table(start_date, end_date):
    return pd.DataFrame({
        'Período da Análise': [
            f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]} "
            f"a {end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        ],
        'Data da Análise': [pd.Timestamp.now().strftime('%d/%m/%Y')]
    })

# ==================================================
# 8️⃣ Ajuste final de resumos
# ==================================================

def build_detailed_plan_summaries(resumo_oferta, resumo_operacao):
    return resumo_oferta.copy(), resumo_operacao.copy()
