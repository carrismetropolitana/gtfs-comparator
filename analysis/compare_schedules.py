import pandas as pd
import os
from analysis.alerts import add_alert, normalize_plan_name

# # ========================================================================================================================================================
# # 1️⃣ Compara calendários, entre oferta e operação
# # ========================================================================================================================================================

# def get_departure_times_for_all_patterns_and_dates(gtfs_file, alerts_df):
#     stops_df = pd.read_csv(gtfs_file + '/stops.txt')
#     stop_times_df = pd.read_csv(gtfs_file + '/stop_times.txt')
#     trips_df = pd.read_csv(gtfs_file + '/trips.txt')
#     calendar_dates_df = pd.read_csv(gtfs_file + '/calendar_dates.txt')

#     # -------------------------------------------------------------------------------------------
#     # 📌 Obtem todas as datas únicas
#     # -------------------------------------------------------------------------------------------
    
#     unique_dates = calendar_dates_df['date'].unique()

#     # Initialize an empty dataframe to store results for all patterns and dates
#     all_patterns_dates_results = pd.DataFrame(columns=['date', 'pattern_id', 'departure_time', 'stop_name'])

#     # Iterate through each date
#     for date in unique_dates:
#         # Filter trips based on service_ids for the given date
#         service_ids_for_date = calendar_dates_df[calendar_dates_df['date'] == date]['service_id']
#         trips_for_date_df = trips_df[trips_df['service_id'].isin(service_ids_for_date)]

#         # Filter stop_times to get only the first stop for each trip
#         first_stop_times_df = stop_times_df.groupby('trip_id').first().reset_index()

#         # Merge first_stop_times with filtered trips to get pattern_id
#         merged_df = pd.merge(first_stop_times_df, trips_for_date_df, on='trip_id')

#         # Merge with stops_df to get stop_name for the first stop
#         merged_with_stops_df = pd.merge(merged_df, stops_df, on='stop_id')

#         # Add 'date' column
#         merged_with_stops_df['date'] = date

#         # Select necessary columns and sort by pattern_id and departure_time
#         departure_times_for_date = merged_with_stops_df[['date', 'pattern_id', 'departure_time', 'stop_name']].sort_values(by=['pattern_id', 'departure_time'])

#         # Append the result to all_patterns_dates_results dataframe
#         all_patterns_dates_results = all_patterns_dates_results.append(departure_times_for_date, ignore_index=True)
#     return all_patterns_dates_results, alerts_df


# ==================================================
# COMPARAÇÃO DE HORÁRIOS ENTRE PLANOS DE OFERTA E OPERAÇÃO
# ==================================================
def get_departure_times_for_all_patterns_and_dates(gtfs_path, plan_name, alerts_df):
    """
    Extrai os horários de partida (primeira paragem) para todos os padrões e datas do GTFS.
    """
    plan_name = normalize_plan_name(plan_name)

    # ================================
    # Carregar arquivos GTFS com proteção
    # ================================
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

    # ================================
    # Verificar colunas essenciais
    # ================================
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

    # Converter 'date' para datetime
    calendar_dates_df['date'] = pd.to_datetime(calendar_dates_df['date'], errors='coerce')
    calendar_dates_df = calendar_dates_df.dropna(subset=['date'])

    # Lista temporária para armazenar DataFrames
    results_list = []

    # Iterar pelas datas únicas
    for date, group_dates in calendar_dates_df.groupby('date'):
        service_ids_for_date = group_dates['service_id'].dropna().unique()
        trips_for_date_df = trips_df[trips_df['service_id'].isin(service_ids_for_date)]

        if trips_for_date_df.empty:
            continue  # Nenhuma viagem para esta data

        # Obter a primeira paragem de cada viagem
        first_stop_times_df = (
            stop_times_df.sort_values(['trip_id', 'stop_sequence'])
            .groupby('trip_id', as_index=False)
            .first()
        )

        # Merge para obter pattern_id
        merged_df = pd.merge(first_stop_times_df, trips_for_date_df, on='trip_id', how='inner')

        if merged_df.empty:
            continue  # Nenhuma correspondência

        # Merge para obter stop_name
        merged_with_stops_df = pd.merge(merged_df, stops_df, on='stop_id', how='left')

        merged_with_stops_df['date'] = date

        departure_times_for_date = merged_with_stops_df[
            ['date', 'pattern_id', 'departure_time', 'stop_name']
        ].sort_values(by=['pattern_id', 'departure_time'])

        results_list.append(departure_times_for_date)

    # Concatenar todos os resultados
    if results_list:
        all_patterns_dates_results = pd.concat(results_list, ignore_index=True)
    else:
        all_patterns_dates_results = pd.DataFrame(
            columns=['date', 'pattern_id', 'departure_time', 'stop_name']
        )
        print(f"⚠️ Nenhum horário de partida encontrado para {plan_name}")

    return all_patterns_dates_results, alerts_df
