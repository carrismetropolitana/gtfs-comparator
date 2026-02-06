"""
Este módulo calcula e consolida métricas de circulações, VKM e comparações entre os planos de Oferta e Operação, incluindo alertas de qualidade de dados.

Funcionalidades principais:
- Define o schema final do relatório “Total circulações e VKM”, com colunas normalizadas para ambos os planos.
- Calcula a distância real (km) de cada viagem com base no shape correspondente.
- Determina o número de dias ativos de cada serviço dentro do período de análise.
- Calcula os VKM por viagem e serviço, considerando a distância e os dias ativos.
- Conta as circulações existentes por pattern_id, período do ano e tipo de dia (day_type).
- Constrói um resumo por plano (Oferta / Operação) agregando circulações, número de paragens e extensão do shape.
- Calcula o VKM total anual por percurso, a partir da extensão do shape e do número de circulações.
- Gera alertas sempre que forem detetadas datas com exception_type = 2 nos calendar_dates de qualquer plano.
- Consolida alertas por plano e cria uma tabela de alertas completa.
- Gera uma tabela comparativa global entre os planos, normalizando colunas e garantindo o schema final.
- Cria um resumo de contrato comparando VKM dos planos com o VKM contratado.
- Produz uma tabela com o período de análise e a data de execução.
- Fornece os resumos detalhados finais para cada plano.

Outputs:
- 1 DataFrame com o resumo de circulações e VKM por percurso, período e dia tipo, para cada plano.
- 1 DataFrame comparativo consolidado (Oferta vs Operação) com o schema final definido.
- 1 DataFrame de alertas com todas as inconformidades detetadas.
- 1 DataFrame com o resumo do contrato (VKM) e diferenças relativas.
- 1 DataFrame com o período de análise e data de execução.
"""

import pandas as pd
from analysis.alerts import add_alert, init_alerts_df
import numpy as np

# ========================================================================================================================================================
# 0️⃣ Preparação — sufixos e mapeamentos
# ========================================================================================================================================================

PLAN_SUFFIX = {
    'PLANO DE OFERTA': 'POferta',
    'PLANO DE OPERAÇÃO': 'POperação',
    'POferta': 'POferta',
    'POperação': 'POperação'
}

TOTAL_CIRCULACOES_VKM_COLUMNS = [
    'Percurso', 'Periodo do ano', 'Dia tipo',
    'Num total circulações ano_POferta', 'Num total paragens_POferta', 'Sequencia paragens_POferta', 'Extensão shape_POferta', 'VKM total ano_POferta',
    'Num total circulações ano_POperação', 'Num total paragens_POperação', 'Sequencia paragens_POperação', 'Extensão shape_POperação', 'VKM total ano_POperação',
]

COLUMN_RENAME_MAP = {
    'result_POferta': 'Num total circulações ano_POferta',
    'stop_id_POferta': 'Num total paragens_POferta',
    'stop_sequence_POferta': 'Sequencia paragens_POferta',
    'shape_dist_traveled_POferta': 'Extensão shape_POferta',
    'result_POperação': 'Num total circulações ano_POperação',
    'stop_id_POperação': 'Num total paragens_POperação',
    'stop_sequence_POperação': 'Sequencia paragens_POperação',
    'shape_dist_traveled_POperação': 'Extensão shape_POperação',
}

# ========================================================================================================================================================
# 1️⃣ Calcula distância de cada trip em km
# ========================================================================================================================================================

def calculate_trip_distance_km(trips, shapes):
    shape_dist = (
        shapes.groupby('shape_id')['shape_dist_traveled']
        .max()
        .reset_index()
        .rename(columns={'shape_dist_traveled':'distance'})
    )
    # Converter metros para km se necessário
    shape_dist['distance_km'] = shape_dist['distance'].apply(lambda x: x/1000 if x>1000 else x)
    return trips.merge(shape_dist[['shape_id','distance_km']], on='shape_id', how='left')[['trip_id','pattern_id','service_id','distance_km']]

# ========================================================================================================================================================
# 2️⃣ Calcula número de dias ativos de cada serviço
# ========================================================================================================================================================

def calculate_service_days(calendar_dates, start_date, end_date):
    calendar_dates = calendar_dates.copy()
    calendar_dates['date'] = pd.to_datetime(calendar_dates['date'])
    mask = (calendar_dates['date'] >= pd.to_datetime(start_date)) & (calendar_dates['date'] <= pd.to_datetime(end_date))
    return calendar_dates[mask].groupby('service_id')['date'].nunique().reset_index(name='n_days')

# ========================================================================================================================================================
# 3️⃣ Calcula VKM
# ========================================================================================================================================================

def calculate_vkm(gtfs, start_date, end_date):
    trips_dist = calculate_trip_distance_km(gtfs['trips'], gtfs['shapes'])
    service_days = calculate_service_days(gtfs['calendar_dates'], start_date, end_date)
    vkm_df = trips_dist.merge(service_days, on='service_id', how='inner')
    vkm_df['vkm'] = vkm_df['distance_km'] * vkm_df['n_days']
    return vkm_df

# ========================================================================================================================================================
# 4️⃣ Calcula o número de trips por pattern/day_type/período
# ========================================================================================================================================================

def compute_trips_per_pattern_day_type_period(trips_df, calendar_dates_df):
    trips_calendar = pd.merge(trips_df, calendar_dates_df, on='service_id')
    trips_per_pattern = trips_calendar.groupby(['pattern_id','service_id','period','day_type'])['trip_id'].nunique().reset_index()
    days_per_pattern = trips_calendar.groupby(['pattern_id','service_id','period','day_type'])['date'].nunique().reset_index().rename(columns={'date':'days_count'})
    merged_result = pd.merge(days_per_pattern, trips_per_pattern, on=['pattern_id','service_id','period','day_type'], how='left')
    merged_result['result'] = merged_result['days_count'] * merged_result['trip_id']
    return merged_result

# ========================================================================================================================================================
# 5️⃣ Gera um resumo por plano
# ========================================================================================================================================================

def build_plan_summary(merged_trips_result, stops_count_df, extension_df, plan_name):
    suffix = PLAN_SUFFIX.get(plan_name, plan_name)

    # -------------------------------------------------------------------------------------------
    # 1. Normaliza colunas de paragens
    # -------------------------------------------------------------------------------------------
    stop_cols = stops_count_df.columns.tolist()

    if 'stop_id' in stop_cols:
        stops_count_df = stops_count_df.rename(columns={'stop_id': f'stop_id_{suffix}'})

    if 'stop_sequence' in stop_cols:
        stops_count_df = stops_count_df.rename(columns={'stop_sequence': f'stop_sequence_{suffix}'})

    # -------------------------------------------------------------------------------------------
    # 2. Circulações
    # -------------------------------------------------------------------------------------------
    pivot_table = (
        merged_trips_result
        .pivot_table(
            index=['pattern_id','period','day_type'],
            values='result',
            aggfunc='sum'
        )
        .reset_index()
    )

    resumo = pd.merge(pivot_table, stops_count_df, on='pattern_id', how='left')
    resumo = pd.merge(resumo, extension_df, on='pattern_id', how='left')

    # -------------------------------------------------------------------------------------------
    # 3. Garante valores numéricos
    # -------------------------------------------------------------------------------------------
    resumo['result'] = pd.to_numeric(resumo['result'], errors='coerce').fillna(0)

    for col in [
        f'stop_id_{suffix}',
        f'stop_sequence_{suffix}',
        f'shape_dist_traveled_{suffix}'
    ]:
        if col in resumo.columns:
            resumo[col] = pd.to_numeric(resumo[col], errors='coerce').fillna(0)

    # -------------------------------------------------------------------------------------------
    # 4. VKM
    # -------------------------------------------------------------------------------------------
    resumo[f'VKM total ano_{suffix}'] = (
        resumo['result'] * resumo[f'shape_dist_traveled_{suffix}']
    )

    # -------------------------------------------------------------------------------------------
    # 5. Final
    # -------------------------------------------------------------------------------------------
    resumo = resumo.rename(columns={
        'result': f'result_{suffix}'
    })

    resumo['Plano'] = plan_name
    return resumo

# ========================================================================================================================================================
# 6️⃣ Comparação global Oferta vs Operação
# ========================================================================================================================================================

def build_global_comparison(resumo_oferta, resumo_operacao):
    # Não usar 'suffixes' porque as colunas já têm os sufixos finais
    merged_all = pd.merge(resumo_oferta, resumo_operacao, on=['pattern_id','period','day_type'], how='outer')
    
    # Ajustar nomes de colunas
    merged_all.rename(columns={'pattern_id':'Percurso','period':'Periodo do ano','day_type':'Dia tipo'}, inplace=True)
    merged_all.rename(columns=COLUMN_RENAME_MAP, inplace=True)
    
    # Garantir que todas as colunas do schema final existam
    for col in TOTAL_CIRCULACOES_VKM_COLUMNS:
        if col not in merged_all.columns:
            merged_all[col] = 0
            
    return merged_all[TOTAL_CIRCULACOES_VKM_COLUMNS]

# ========================================================================================================================================================
# 7️⃣ Resumo de contrato (VKM)
# ========================================================================================================================================================

def build_contract_summary(gtfs_POferta, gtfs_POperacao, start_date, end_date, vkm_contrato, gtfs_offer_name, gtfs_operation_name):
    vkm_POferta_df = calculate_vkm(gtfs_POferta, start_date, end_date)
    vkm_POperacao_df = calculate_vkm(gtfs_POperacao, start_date, end_date)
    total_vkm_POferta = vkm_POferta_df['vkm'].sum()
    total_vkm_POperacao = vkm_POperacao_df['vkm'].sum()
    return pd.DataFrame({
        '': ['Plano de Oferta','Plano de Operação','Contrato'],
        'Designação GTFS':[gtfs_offer_name, gtfs_operation_name,''],
        'VKM':[total_vkm_POferta,total_vkm_POperacao,vkm_contrato],
        'Diferença relativa ao contrato':[total_vkm_POferta/vkm_contrato, total_vkm_POperacao/vkm_contrato,'-']
    })

# ========================================================================================================================================================
# 8️⃣ Período da análise
# ========================================================================================================================================================

def build_analysis_period_table(start_date,end_date):
    return pd.DataFrame({
        'Período da Análise':[f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]} a {end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"],
        'Data da Análise':[pd.Timestamp.now().strftime('%d/%m/%Y')]
    })
