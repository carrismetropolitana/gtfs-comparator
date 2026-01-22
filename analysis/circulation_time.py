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

# def parse_circulation_time(t):
#     try:
#         return pd.to_timedelta(t)
#     except Exception:
#         return pd.NaT


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
    Adiciona ao ficheiro, o dia (date) a partir do service_id.
    """

    calendar_dates_df["date"] = pd.to_datetime(calendar_dates_df["date"], format="%Y%m%d", errors="coerce")

    calendar_dates_df = calendar_dates_df[calendar_dates_df["exception_type"] == 1]

    return df.merge(calendar_dates_df[["service_id", "date"]], on="service_id", how="left")

# ========================================================================================================================================================
# 5️⃣ Processamento
# ========================================================================================================================================================

def compare_circulations_by_hour(gtfs_path_oferta, gtfs_path_operacao, alerts_df):

    # -------------------------------------------------------------------------------------------
    # 0️⃣ Normalização de GTFS
    # -------------------------------------------------------------------------------------------

    plan_oferta = normalize_plan_name("Oferta")
    plan_operacao = normalize_plan_name("Operacao")

    # -------------------------------------------------------------------------------------------
    # 1️⃣ Lê ficheiros GTFS
    # -------------------------------------------------------------------------------------------
    required_files = ["trips.txt", "stop_times.txt", "calendar_dates.txt"]
    dfs_oferta, dfs_operacao = {}, {}

    for path, dfs, plano in [
        (gtfs_path_oferta, dfs_oferta, "Plano de Oferta"),
        (gtfs_path_operacao, dfs_operacao, "Plano de Operação"),
    ]:
        for fname in required_files:
            try:
                dfs[fname] = read_gtfs_file(path, fname)
            except Exception:
                add_alert(
                    alerts_df,
                    plano,
                    "Circulações por hora",
                    "MUITO GRAVE",
                    f"Erro ao ler {fname}",
                    path
                )
                return pd.DataFrame(), alerts_df

    # -------------------------------------------------------------------------------------------
    # 2️⃣ Prepara dataframes base
    # -------------------------------------------------------------------------------------------

    df_oferta = prepare_df(dfs_oferta, plan_oferta)
    df_operacao = prepare_df(dfs_operacao, plan_operacao)

    # -------------------------------------------------------------------------------------------
    # 3️⃣ Adiciona a data
    # -------------------------------------------------------------------------------------------

    df_oferta = add_date_to_df(df_oferta, dfs_oferta["calendar_dates.txt"])
    df_operacao = add_date_to_df(df_operacao, dfs_operacao["calendar_dates.txt"])

    df_oferta = df_oferta.dropna(subset=["date"])
    df_operacao = df_operacao.dropna(subset=["date"])

    # -------------------------------------------------------------------------------------------
    # 4️⃣ Identifica as circulações únicas por dia e hora
    #  “Para cada dia, percurso (pattern_id) e hora, conta apenas uma circulação.”
    # “Se houver várias linhas com a mesma combinação de data + pattern + hora, mantém só uma.”
    #
    # #🔹 Por que não usar trip_id?
    #
    #         Porque:
    #         Oferta e Operação não têm os mesmos trip_id
    #
    #         O que interessa é:
    #         “Houve uma circulação às 08:00 neste percurso?”
    #         “A que horas foi feita?”
    # -------------------------------------------------------------------------------------------
    
    df_oferta = (df_oferta.drop_duplicates(subset=["date", "pattern_id", f"Hora_{plan_oferta}"]).rename(columns={f"Hora_{plan_oferta}": "hora_oferta"}).reset_index(drop=True))
    df_operacao = (df_operacao.drop_duplicates(subset=["date", "pattern_id", f"Hora_{plan_operacao}"]).rename(columns={f"Hora_{plan_operacao}": "hora_operacao"}).reset_index(drop=True))

    # -------------------------------------------------------------------------------------------
    # 5️⃣ Pré processamento (merge_asof)
    # -------------------------------------------------------------------------------------------

    df_oferta["date"] = pd.to_datetime(df_oferta["date"], errors="coerce")
    df_operacao["date"] = pd.to_datetime(df_operacao["date"], errors="coerce")

    df_oferta["hora_oferta"] = pd.to_timedelta(df_oferta["hora_oferta"], errors="coerce")
    df_operacao["hora_operacao"] = pd.to_timedelta(df_operacao["hora_operacao"], errors="coerce")

    df_oferta = df_oferta.dropna(subset=["hora_oferta"])
    df_operacao = df_operacao.dropna(subset=["hora_operacao"])

    df_oferta = df_oferta.sort_values(["hora_oferta", "date", "pattern_id"]).reset_index(drop=True)
    df_operacao = df_operacao.sort_values(["hora_operacao", "date", "pattern_id"]).reset_index(drop=True)

    print()
    print("Existem ", len(df_oferta), " de circulações únicas no plano de Oferta")
    print()
    print("Existem ", len(df_oferta), " de circulações únicas no plano de Operação")
    print()

    if df_oferta.empty or df_operacao.empty:
        add_alert(
            alerts_df,
            "Plano de Operação",
            "Circulações por hora",
            "GRAVE",
            "Não foi possível extrair circulações únicas",
            ""
        )
        return pd.DataFrame(), alerts_df

    # -------------------------------------------------------------------------------------------
    # 6️⃣ Identifica o horário mais proximo
    # Associa cada circulação do Plano de Oferta à circulação mais próxima no Plano de Operação,
    # no mesmo dia e no mesmo percurso, dentro de uma tolerância de 30 minutos.
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
    # 7️⃣ Indica a diferença (em minutos) entre planos
    # -------------------------------------------------------------------------------------------

    df["Diferença_min"] = (df["hora_operacao"] - df["hora_oferta"]).dt.total_seconds() / 60
    
    # -------------------------------------------------------------------------------------------
    # 8️⃣ Gera alertas
    # -------------------------------------------------------------------------------------------

    alerts = df[df["hora_operacao"].isna() | df["Diferença_min"].abs().gt(0)]

    for _, row in alerts.iterrows():
        contexto = f"{row['date'].strftime('%Y-%m-%d')} | {row['pattern_id']}"

        if pd.isna(row["hora_operacao"]):
            add_alert(
                alerts_df,
                "Plano de Operação",
                "Circulações por hora",
                "GRAVE",
                "Circulação existente apenas no Plano de Oferta",
                contexto
            )
        else:
            diff = abs(int(row["Diferença_min"]))
            grav = "MUITO GRAVE" if diff > 5 else "GRAVE"
            add_alert(
                alerts_df,
                "Plano de Operação",
                "Circulações por hora",
                grav,
                f"Diferença de {diff} minutos",
                contexto
            )

    # -------------------------------------------------------------------------------------------
    # 9️⃣ Formatação final
    # -------------------------------------------------------------------------------------------

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["Hora_Oferta"] = df["hora_oferta"].apply(format_timedelta)
    df["Hora_Operacao"] = df["hora_operacao"].apply(format_timedelta)

    df = df[["date", "pattern_id", "Hora_Oferta", "Hora_Operacao", "Diferença_min"]]

    return df.sort_values(["date", "pattern_id", "Hora_Oferta"], na_position="last"), alerts_df
