"""
Este módulo valida e compara as circulações por hora entre o Plano de Oferta e o Plano de Operação com base em dados GTFS.

Funcionalidades principais:
- Lê ficheiros GTFS (trips, stop_times e calendar_dates) a partir de pastas ou ficheiros ZIP.
- Extrai, para cada trip, a hora de início da circulação com base na primeira paragem válida.
- Associa cada circulação a uma data real através do service_id e do ficheiro calendar_dates.
- Reduz os dados a circulações únicas por dia, percurso (pattern_id) e hora, ignorando o trip_id, garantindo uma comparação lógica entre planos.
- Normaliza e valida os tipos de dados de data e hora, removendo valores inválidos e ordenando corretamente os dados para comparação temporal.
- Associa cada circulação do Plano de Oferta à circulação mais próxima do Plano de Operação, no mesmo dia e percurso, utilizando merge_asof com tolerância temporal configurada (±30 minutos).
- Calcula a diferença horária (em minutos) entre a Oferta e a Operação para cada circulação emparelhada.
- Identifica e classifica inconsistências, incluindo:
    - Circulações previstas que não ocorreram na Operação.
    - Diferenças de horário entre os dois planos.
- Gera alertas automáticos com diferentes níveis de severidade (GRAVE e MUITO GRAVE), de acordo com a magnitude das discrepâncias detetadas.

Outputs:
- 1 tabela consolidada com a comparação das circulações por dia, percurso e hora (Oferta vs Operação), incluindo a diferença em minutos.
- Atualização da tabela de alertas com a identificação das circulações problemáticas, o tipo de inconsistência e a respetiva severidade.

"""

import os
import pandas as pd
import numpy as np
import zipfile
from analysis.alerts import add_alert, normalize_plan_name

# ========================================================================================================================================================
# 1️⃣ Lê GTFS
# ========================================================================================================================================================

def read_gtfs_file(path, filename):
    """
    Lê um ficheiro GTFS que pode estar dentro de uma pasta ou dentro de um zip.
    """
    if os.path.isdir(path):
        return pd.read_csv(os.path.join(path, filename))

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as z:
            with z.open(filename) as f:
                return pd.read_csv(f)

    raise FileNotFoundError(f"Não foi possível ler {filename} em {path}")

# ========================================================================================================================================================
# 2️⃣ Formata a hora
# ========================================================================================================================================================

def format_timedelta(td):
    if pd.isna(td):
        return ""
    total_sec = int(td.total_seconds())
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    return f"{h:02d}:{m:02d}"

# ========================================================================================================================================================
# 3️⃣ Extrai a hora de início da circulação
# ========================================================================================================================================================

def prepare_df(dfs, label):
    trips = dfs["trips.txt"][["trip_id", "pattern_id", "service_id"]].copy()
    stop_times = dfs["stop_times.txt"][["trip_id", "arrival_time", "stop_sequence"]].copy()

    stop_times["arrival_time"] = pd.to_timedelta(stop_times["arrival_time"], errors="coerce")

    start_times = (
        stop_times.dropna(subset=["arrival_time"])
        .sort_values(["trip_id", "stop_sequence"])
        .groupby("trip_id", as_index=False)["arrival_time"]
        .first()
    )

    df = trips.merge(start_times, on="trip_id", how="inner")
    df = df.rename(columns={"arrival_time": f"Hora_{label}"})

    return df[["trip_id", "service_id", "pattern_id", f"Hora_{label}"]]

# ========================================================================================================================================================
# 4️⃣ Associa as circulações às datas
# ========================================================================================================================================================

def add_date_to_df(df, calendar_dates_df):
    """
    Adiciona ao ficheiro o dia (date) a partir do service_id.
    """
    calendar_dates_df["date"] = pd.to_datetime(calendar_dates_df["date"], format="%Y%m%d", errors="coerce")
    calendar_dates_df = calendar_dates_df[calendar_dates_df["exception_type"] == 1]

    return df.merge(calendar_dates_df[["service_id", "date"]], on="service_id", how="left")

# ========================================================================================================================================================
# 5️⃣ Processamento
# ========================================================================================================================================================

def compare_circulations_by_hour(gtfs_oferta, gtfs_operacao, alerts_df):
    plan_oferta = normalize_plan_name("Oferta")
    plan_operacao = normalize_plan_name("Operacao")

    # -------------------------------------------------------------------------------------------
    # 1️⃣ Prepara os dataframes
    # -------------------------------------------------------------------------------------------
    required_files = {"trips.txt": "trips", "stop_times.txt": "stop_times", "calendar_dates.txt": "calendar_dates"}
    dfs_oferta, dfs_operacao = {}, {}

    for gtfs, dfs, plano in [(gtfs_oferta, dfs_oferta, "Plano de Oferta"),
                             (gtfs_operacao, dfs_operacao, "Plano de Operação")]:
        for fname, key in required_files.items():
            try:
                dfs[fname] = gtfs[key].copy()
            except KeyError:
                add_alert(alerts_df, plano, "Circulações por hora", "MUITO GRAVE",
                          f"DataFrame '{key}' em falta no GTFS", plano)
                return pd.DataFrame(), alerts_df

    # -------------------------------------------------------------------------------------------
    # 2️⃣ Prepara dataframes base
    # -------------------------------------------------------------------------------------------
    df_oferta = prepare_df(dfs_oferta, plan_oferta)
    df_operacao = prepare_df(dfs_operacao, plan_operacao)

    # -------------------------------------------------------------------------------------------
    # 3️⃣ Adiciona a data
    # -------------------------------------------------------------------------------------------
    df_oferta = add_date_to_df(df_oferta, dfs_oferta["calendar_dates.txt"]).dropna(subset=["date"])
    df_operacao = add_date_to_df(df_operacao, dfs_operacao["calendar_dates.txt"]).dropna(subset=["date"])

    # -------------------------------------------------------------------------------------------
    # 4️⃣ Identifica circulações únicas por dia + percurso + hora
    # -------------------------------------------------------------------------------------------
    df_oferta = df_oferta.drop_duplicates(subset=["date", "pattern_id", f"Hora_{plan_oferta}"])\
                         .rename(columns={f"Hora_{plan_oferta}": "hora_oferta"}).reset_index(drop=True)
    df_operacao = df_operacao.drop_duplicates(subset=["date", "pattern_id", f"Hora_{plan_operacao}"])\
                             .rename(columns={f"Hora_{plan_operacao}": "hora_operacao"}).reset_index(drop=True)

    # ⚡ Soma total de circulações únicas para print no run_analysis
    total_circulacoes_oferta = len(df_oferta)
    total_circulacoes_operacao = len(df_operacao)

    # -------------------------------------------------------------------------------------------
    # 5️⃣ Pré-processamento merge_asof
    # -------------------------------------------------------------------------------------------
    df_oferta["date"] = pd.to_datetime(df_oferta["date"], errors="coerce")
    df_operacao["date"] = pd.to_datetime(df_operacao["date"], errors="coerce")
    df_oferta["hora_oferta"] = pd.to_timedelta(df_oferta["hora_oferta"], errors="coerce")
    df_operacao["hora_operacao"] = pd.to_timedelta(df_operacao["hora_operacao"], errors="coerce")

    df_oferta = df_oferta.dropna(subset=["hora_oferta"]).sort_values(["hora_oferta", "date", "pattern_id"]).reset_index(drop=True)
    df_operacao = df_operacao.dropna(subset=["hora_operacao"]).sort_values(["hora_operacao", "date", "pattern_id"]).reset_index(drop=True)

    if df_oferta.empty or df_operacao.empty:
        add_alert(alerts_df, "Plano de Operação", "Circulações por hora", "GRAVE",
                  "Não foi possível extrair circulações únicas", "")
        return pd.DataFrame(), alerts_df

    # -------------------------------------------------------------------------------------------
    # 6️⃣ Merge com horário mais próximo (tolerância 30min)
    # -------------------------------------------------------------------------------------------
    df = pd.merge_asof(
        df_oferta,
        df_operacao,
        left_on="hora_oferta",
        right_on="hora_operacao",
        by=["date", "pattern_id"],
        direction="nearest",
        tolerance=pd.Timedelta(minutes=30)
    )

    # -------------------------------------------------------------------------------------------
    # 7️⃣ Calcula diferença em minutos
    # -------------------------------------------------------------------------------------------
    df["Diferença_min"] = (df["hora_operacao"] - df["hora_oferta"]).dt.total_seconds() / 60

    # -------------------------------------------------------------------------------------------
    # 8️⃣ Gera alertas
    # -------------------------------------------------------------------------------------------
    alerts = df[df["hora_operacao"].isna() | df["Diferença_min"].abs().gt(0)]
    for _, row in alerts.iterrows():
        contexto = f"{row['date'].strftime('%Y-%m-%d')} | {row['pattern_id']}"
        if pd.isna(row["hora_operacao"]):
            add_alert(alerts_df, "Plano de Operação", "Circulações por hora", "GRAVE",
                      "Circulação existente apenas no Plano de Oferta", contexto)
        else:
            diff = abs(int(row["Diferença_min"]))
            grav = "MUITO GRAVE" if diff > 5 else "GRAVE"
            add_alert(alerts_df, "Plano de Operação", "Circulações por hora", grav,
                      f"Diferença de {diff} minutos", contexto)

    # -------------------------------------------------------------------------------------------
    # 9️⃣ Formatação final
    # -------------------------------------------------------------------------------------------
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["Hora_Oferta"] = df["hora_oferta"].apply(format_timedelta)
    df["Hora_Operacao"] = df["hora_operacao"].apply(format_timedelta)
    df = df[["date", "pattern_id", "Hora_Oferta", "Hora_Operacao", "Diferença_min"]]

    # 🔹 Retorna DataFrame de comparação, alerts_df e totais de circulações
    return df.sort_values(["date", "pattern_id", "Hora_Oferta"], na_position="last"), alerts_df, total_circulacoes_oferta, total_circulacoes_operacao