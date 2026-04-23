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

import zipfile
import os
import pandas as pd

# ========================================================================================================================================================
# 0️⃣ Função auxiliar para ler tabelas GTFS (pasta ou ZIP)
# ========================================================================================================================================================

def _read_gtfs_table(base_path, table, dtype=None):
    """
    Lê uma tabela GTFS a partir de uma pasta ou de um ficheiro ZIP.
    """
    file_name = f"{table}.txt"

    # Caso seja diretório
    if os.path.isdir(base_path):
        file_path = os.path.join(base_path, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_name} não encontrado em {base_path}")
        return pd.read_csv(file_path, dtype=dtype, encoding="utf-8")

    # Caso seja ficheiro ZIP
    if zipfile.is_zipfile(base_path):
        with zipfile.ZipFile(base_path, "r") as z:
            if file_name not in z.namelist():
                raise FileNotFoundError(f"{file_name} não encontrado no ZIP {base_path}")
            with z.open(file_name) as f:
                return pd.read_csv(f, dtype=dtype)

    raise FileNotFoundError(f"GTFS inválido: {base_path}")


# ========================================================================================================================================================
# 1️⃣ Lê os ficheiros GTFS
# ========================================================================================================================================================

def read_gtfs(file_path, tables=None, calendar_dates_start_date=None, calendar_dates_end_date=None):
    """
    Lê os ficheiros GTFS (pasta ou ZIP) e devolve um dicionário com os DataFrames.
    """

    if not os.path.exists(file_path):
        zip_path = f"{file_path}.zip"
        if os.path.exists(zip_path):
            file_path = zip_path

    if not tables:
        tables = ['stops', 'routes', 'trips', 'stop_times', 'shapes', 'calendar_dates', 'agency']

    gtfs_data = {}

    # Converter datas de input para datetime
    if calendar_dates_start_date is not None:
        calendar_dates_start_date = pd.to_datetime(str(calendar_dates_start_date), format='%Y%m%d')
    if calendar_dates_end_date is not None:
        calendar_dates_end_date = pd.to_datetime(str(calendar_dates_end_date), format='%Y%m%d')

    for table in tables:
        dtype = {'stop_id': str} if table in ['stops', 'stop_times'] else None

        df = _read_gtfs_table(file_path, table, dtype=dtype)

        # Tratamento específico do calendar_dates
        if table == 'calendar_dates':
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')

            if calendar_dates_start_date is not None and calendar_dates_end_date is not None:
                df = df[
                    (df['date'] >= calendar_dates_start_date) &
                    (df['date'] <= calendar_dates_end_date)
                ]

        gtfs_data[table] = df

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
