"""
Este módulo trata da leitura dos ficheiros GTFS e do cálculo de parâmetros contratuais associados.

Funcionalidades principais:
- Lê os ficheiros GTFS a partir de um diretório de entrada.
- Permite definir dinamicamente quais as tabelas GTFS a carregar.
- Garante a correta leitura de identificadores (ex.: stop_id) como texto.
- Filtra o ficheiro calendar_dates por um intervalo temporal específico, quando definido.
- Converte automaticamente as datas do calendário para o formato de data.
- Devolve um dicionário com os DataFrames GTFS carregados em memória.
- Analisa o ficheiro agency para identificar o contrato associado ao plano.
- Determina o valor de Veículos-Kilómetro (VKM) contratados com base no agency_id.

Outputs:
- 1 dicionário com os DataFrames GTFS carregados (stops, routes, trips, stop_times, shapes, calendar_dates, agency).
- 1 valor numérico correspondente aos VKM do contrato identificado.

"""

import os
import pandas as pd

# ========================================================================================================================================================
# 1️⃣ Lê os ficheiros GTFS
# ========================================================================================================================================================

def read_gtfs(file_path, tables=None, calendar_dates_start_date=None, calendar_dates_end_date=None):
    """
    Lê os ficheiros GTFS e devolve um dicionário com os dataframes.
    """
    if not tables:
        tables = ['stops', 'routes', 'trips', 'stop_times', 'shapes', 'calendar_dates','agency']

    gtfs_data = {}

    # Converter datas de input para datetime (para comparação correta)
    if calendar_dates_start_date is not None:
        calendar_dates_start_date = pd.to_datetime(str(calendar_dates_start_date), format='%Y%m%d')
    if calendar_dates_end_date is not None:
        calendar_dates_end_date = pd.to_datetime(str(calendar_dates_end_date), format='%Y%m%d')

    for table in tables:
        file_name = f"{table}.txt"
        file_path_table = os.path.join(file_path, file_name)

        dtype = {'stop_id': str} if table in ['stops', 'stop_times'] else None

        if table == 'calendar_dates':
            gtfs_data[table] = pd.read_csv(file_path_table, dtype=dtype, encoding='utf-8')
            gtfs_data[table]['date'] = pd.to_datetime(gtfs_data[table]['date'], format='%Y%m%d')

            # Filtra por período, se definido
            if calendar_dates_start_date is not None and calendar_dates_end_date is not None:
                gtfs_data[table] = gtfs_data[table][
                    (gtfs_data[table]['date'] >= calendar_dates_start_date) &
                    (gtfs_data[table]['date'] <= calendar_dates_end_date)
                ]

        else:
            gtfs_data[table] = pd.read_csv(file_path_table, dtype=dtype, encoding='utf-8')

    return gtfs_data


# ========================================================================================================================================================
# 2️⃣ Calcula os VKM do contrato
# ========================================================================================================================================================

def process_agency_file(agency_df):
    """
    Devolve o número de VKM do contrato com base no agency_id.
    """
    vkm_contrato = None
    if (agency_df['agency_id'] == 41).any():
        vkm_contrato = 28527689
    elif (agency_df['agency_id'] == 42).any():
        vkm_contrato = 25799790
    elif (agency_df['agency_id'] == 43).any():
        vkm_contrato = 19004512
    elif (agency_df['agency_id'] == 44).any():
        vkm_contrato = 15128877
    return vkm_contrato
