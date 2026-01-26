import pandas as pd
from analysis.alerts import init_alerts_df, add_alert

# ========================================================================================================================================================
# 1️⃣ Analisa as viagens por dia
# ========================================================================================================================================================

def trips_per_date(trips_df, calendar_dates_df, start_date, end_date, alerts_df=None):
    """
    Cria uma tabela pivot:
    - linhas: pattern_id
    - colunas: datas
    - valores: número de trips
    """

    if alerts_df is None:
        alerts_df = init_alerts_df()

    if trips_df is None or trips_df.empty or calendar_dates_df is None or calendar_dates_df.empty:
        return pd.DataFrame(), alerts_df

    trips = trips_df.copy()
    calendar = calendar_dates_df.copy()

    # -------------------------------------------------------------------------------------------
    # 📌 Verifica se existem as colunas: service_id; trip_id; pattern_id; 
    # -------------------------------------------------------------------------------------------
    
    required_trips = {"trip_id", "service_id", "pattern_id"}
    required_calendar = {"service_id", "date", "exception_type"}

    if not required_trips.issubset(trips.columns) or not required_calendar.issubset(calendar.columns):
        print("⚠️ Colunas essenciais ausentes em trips ou calendar_dates.")
        return pd.DataFrame(), alerts_df

    # -------------------------------------------------------------------------------------------
    # 📌 Converte datas para o formato YYYYMMDD 
    # -------------------------------------------------------------------------------------------

    calendar["date"] = pd.to_datetime(calendar["date"], format="%Y%m%d", errors="coerce")

    # -------------------------------------------------------------------------------------------
    # 📌 Compara apenas dias "ativos" 
    # -------------------------------------------------------------------------------------------

    calendar = calendar[calendar["exception_type"] == 1]

    # -------------------------------------------------------------------------------------------
    # 📌 Filtra por período 
    # -------------------------------------------------------------------------------------------

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    calendar = calendar[(calendar["date"] >= start_date) & (calendar["date"] <= end_date)]

    # -------------------------------------------------------------------------------------------
    # 📌 Junta os calendários às viagens
    # -------------------------------------------------------------------------------------------
    
    merged = trips.merge(calendar[["service_id", "date"]], on="service_id", how="inner")

    # -------------------------------------------------------------------------------------------
    # 📌 Conta as viagens por percurso e dia
    # -------------------------------------------------------------------------------------------
    
    counts = (merged.groupby(["pattern_id", "date"])["trip_id"].count().reset_index(name="num_trips"))

    # -------------------------------------------------------------------------------------------
    # 📌 Gera a tabela com o número de viagens por percurso e dia
    # -------------------------------------------------------------------------------------------
    
    pivot = counts.pivot(index="pattern_id", columns="date", values="num_trips")
    pivot = pivot.fillna(0).astype(int)

    # -------------------------------------------------------------------------------------------
    # 📌 Garante que existem todas as datas para o intervalo de análise
    # -------------------------------------------------------------------------------------------

    all_dates = pd.date_range(start_date, end_date, freq="D")
    pivot = pivot.reindex(columns=all_dates, fill_value=0)

    # Formata cabeçalhos
    pivot.columns = pivot.columns.strftime("%d/%m/%Y")
    pivot = pivot.sort_index().reset_index()
    return pivot, alerts_df

# ========================================================================================================================================================
# 2️⃣ Compara paragens entre os planos de oferta e operação
# ========================================================================================================================================================

def compare_stops_between_plans(df_oferta, df_operacao, alerts_df=None):
    """
    Compara paragens entre Plano de Oferta e Plano de Operação.
    Compara stop_name, stop_lat, stop_lon.
    Retorna apenas as paragens com diferenças e atualiza alerts_df.
    """
    if alerts_df is None:
        alerts_df = init_alerts_df()

    # -------------------------------------------------------------------------------------------
    # 📌 Compara pelo stop_id
    # -------------------------------------------------------------------------------------------
    
    df_merged = pd.merge(df_oferta, df_operacao, on='stop_id', how='outer', suffixes=('_POferta', '_POperacao'))

    # -------------------------------------------------------------------------------------------
    # 📌 Compara o stop_name; stop_lat; stop_lon
    # -------------------------------------------------------------------------------------------

    columns_to_compare = ['stop_name', 'stop_lat', 'stop_lon']
    diffs = pd.DataFrame()

    for col in columns_to_compare:
        col_oferta = f"{col}_POferta"
        col_operacao = f"{col}_POperacao"

        if col_oferta not in df_merged.columns or col_operacao not in df_merged.columns:
            print(f"⚠️ Coluna {col} está ausente num dos planos. A comparação desta coluna será ignorada.")
            continue

        mask_diff = df_merged[col_oferta] != df_merged[col_operacao]
        if mask_diff.any():
            diffs = pd.concat([diffs, df_merged[mask_diff]])
    # -------------------------------------------------------------------------------------------
    # 📌 Adiciona alertas por stop_id
    # -------------------------------------------------------------------------------------------
            
            for _, row in df_merged[mask_diff].iterrows():
                alerts_df = add_alert(
                    alerts_df,
                    plan_name="Plano de Operação",
                    category="Paragens",
                    severity="MUITO GRAVE",
                    message=f"Paragens com diferenças: {col}",
                    identifier=row['stop_id']
                )

    # Remove duplicados
    diffs = diffs.drop_duplicates(subset=['stop_id'])

    return diffs, alerts_df