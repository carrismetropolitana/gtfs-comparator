
"""
Este módulo extrai e organiza os horários de partida (primeira paragem) a partir de um plano GTFS.

Funcionalidades principais:
- Lê e valida os ficheiros GTFS essenciais (stops, stop_times, trips e calendar_dates).
- Verifica a existência das colunas obrigatórias para garantir a integridade dos dados.
- Normaliza o nome do plano para assegurar consistência no processamento e nos logs.
- Identifica, para cada data ativa, os serviços e viagens válidos no plano GTFS.
- Determina corretamente a primeira paragem de cada viagem com base no stop_sequence.
- Associa cada viagem ao respetivo padrão (pattern_id) e ao nome da paragem inicial.
- Organiza os horários de partida por data, padrão e hora.

Outputs:
- 1 tabela com os horários de partida da primeira paragem, por data e pattern_id (campos: date, pattern_id, departure_time, stop_name).

"""

import pandas as pd
import os
from analysis.alerts import add_alert, normalize_plan_name

# ========================================================================================================================================================
# 1️⃣ Compara horários entre planos de oferta e de operação
# ========================================================================================================================================================

def get_departure_times_for_all_patterns_and_dates(gtfs_path, plan_name, alerts_df):
    """
    Extrai os horários de partida (primeira paragem) para todos os padrões e datas do GTFS.
    """
    plan_name = normalize_plan_name(plan_name)

    try:
        stops_df = pd.read_csv(os.path.join(gtfs_path, "stops.txt"))
        stop_times_df = pd.read_csv(os.path.join(gtfs_path, "stop_times.txt"))
        trips_df = pd.read_csv(os.path.join(gtfs_path, "trips.txt"))
        calendar_dates_df = pd.read_csv(os.path.join(gtfs_path, "calendar_dates.txt"))
    except FileNotFoundError as e:
        print(f"⚠️ Arquivo GTFS não encontrado: {e}")
        return pd.DataFrame(), alerts_df
    except pd.errors.EmptyDataError as e:
        print(f"⚠️ Arquivo GTFS vazio: {e}")
        return pd.DataFrame(), alerts_df

    # -------------------------------------------------------------------------------------------
    # 📌 Verifica se existem todas as colunas necessárias
    # -------------------------------------------------------------------------------------------
    
    required_cols = {
        'stops.txt': ['stop_id', 'stop_name'],
        'stop_times.txt': ['trip_id', 'stop_id', 'departure_time'],
        'trips.txt': ['trip_id', 'pattern_id', 'service_id'],
        'calendar_dates.txt': ['date', 'service_id']
    }

    dfs = {
        'stops.txt': stops_df,
        'stop_times.txt': stop_times_df,
        'trips.txt': trips_df,
        'calendar_dates.txt': calendar_dates_df
    }

    for fname, cols in required_cols.items():
        missing = set(cols) - set(dfs[fname].columns)
        if missing:
            print(f"⚠️ Colunas ausentes em {fname}: {missing}")
            return pd.DataFrame(), alerts_df

    # -------------------------------------------------------------------------------------------
    # 📌 Se necessário, converte 'date' em datetime
    # -------------------------------------------------------------------------------------------

    calendar_dates_df['date'] = pd.to_datetime(calendar_dates_df['date'], errors='coerce')
    calendar_dates_df = calendar_dates_df.dropna(subset=['date'])
    
    # -------------------------------------------------------------------------------------------
    # 📌 Cria uma lista temporária para armazenar os DataFrames
    # -------------------------------------------------------------------------------------------
    
    results_list = []

    # Itera pelas datas únicas
    for date, group_dates in calendar_dates_df.groupby('date'):
        service_ids_for_date = group_dates['service_id'].dropna().unique()
        trips_for_date_df = trips_df[trips_df['service_id'].isin(service_ids_for_date)]

        if trips_for_date_df.empty:
            continue 

        # Obtém a primeira paragem de cada viagem
        first_stop_times_df = (
            stop_times_df.sort_values(['trip_id', 'stop_sequence'])
            .groupby('trip_id', as_index=False)
            .first()
        )

        # Merge para obter pattern_id
        merged_df = pd.merge(first_stop_times_df, trips_for_date_df, on='trip_id', how='inner')

        if merged_df.empty:
            continue  

        # Merge para obter stop_name
        merged_with_stops_df = pd.merge(merged_df, stops_df, on='stop_id', how='left')

        merged_with_stops_df['date'] = date

        departure_times_for_date = merged_with_stops_df[
            ['date', 'pattern_id', 'departure_time', 'stop_name']
        ].sort_values(by=['pattern_id', 'departure_time'])

        results_list.append(departure_times_for_date)

    # -------------------------------------------------------------------------------------------
    # 📌 Concatena todos os resultados 
    # -------------------------------------------------------------------------------------------
    
    if results_list:
        all_patterns_dates_results = pd.concat(results_list, ignore_index=True)
    else:
        all_patterns_dates_results = pd.DataFrame(
            columns=['date', 'pattern_id', 'departure_time', 'stop_name']
        )
        print(f"⚠️ Nenhum horário de partida encontrado para {plan_name}")

    return all_patterns_dates_results, alerts_df
