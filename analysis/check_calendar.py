import pandas as pd
import numpy as np
from analysis.alerts import add_alert


# ========================================================================================================================================================
# 1️⃣ Verificação de exception_type = 2
# ========================================================================================================================================================

def check_exception_type(calendar_dates_df, START_DATE, END_DATE, plan_name, alerts_df):
    if calendar_dates_df is None or calendar_dates_df.empty:
        print(f"{plan_name}: calendar_dates vazio.")
        return alerts_df

    df = calendar_dates_df.copy()

    required_cols = {'exception_type', 'date'}
    if not required_cols.issubset(df.columns):
        print(f"{plan_name}: colunas obrigatórias ausentes em calendar_dates.")
        return alerts_df

    df['exception_type'] = df['exception_type'].fillna(0).astype(int)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    start_date = pd.to_datetime(START_DATE)
    end_date = pd.to_datetime(END_DATE)

    df_period = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    exception_dates = df_period.loc[df_period['exception_type'] == 2, 'date'].dropna()

    for date in sorted(exception_dates.unique()):
        alerts_df = add_alert(
            alerts_df,
            plan_name,
            "Calendário",
            "MUITO GRAVE",
            "Data com exception_type = 2",
            date.strftime('%Y-%m-%d')
        )

    return alerts_df


# ========================================================================================================================================================
# 2️⃣ Comparação de calendários
# ========================================================================================================================================================

def compare_calendar_dates_consolidated(calendar_dates_df, alerts_df):
    """
    Compara os calendários entre o Plano de Oferta e o Plano de Operação
    Classifica as diferenças de acordo com a severidade e identifica os dias que podem estar em falta.
    """
    df = calendar_dates_df.copy()

    required_cols = {'plan', 'date', 'period', 'day_type'}
    if not required_cols.issubset(df.columns):
        print("⚠️ Colunas obrigatórias ausentes:", required_cols - set(df.columns))
        return pd.DataFrame(), alerts_df

    # Normalizações
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['plan_norm'] = (
        df['plan'].astype(str)
        .str.lower()
        .str.normalize('NFKD')
        .str.encode('ascii', errors='ignore')
        .str.decode('utf-8')
    )

    df_oferta = df[df['plan_norm'].str.contains('oferta', na=False)]
    df_oper = df[df['plan_norm'].str.contains('oper', na=False)]

    if df_oferta.empty or df_oper.empty:
        print("⚠️ Calendários vazios após separação de planos.")
        return pd.DataFrame(), alerts_df

    df_oferta = df_oferta[['date', 'period', 'day_type']].drop_duplicates()
    df_oper = df_oper[['date', 'period', 'day_type']].drop_duplicates()

    
    compare_calendars = pd.merge(df_oferta, df_oper, on='date', how='outer', suffixes=('_POferta', '_POperacao'), indicator=True)

    # Diferenças
    compare_calendars['Diferenças_periodo'] = np.where(compare_calendars['period_POferta'] == compare_calendars['period_POperacao'], 'IGUAL', 'DIFERENTE'
    )
    compare_calendars['Diferenças_dia_tipo'] = np.where(
        compare_calendars['day_type_POferta'] == compare_calendars['day_type_POperacao'],
        'IGUAL',
        'DIFERENTE'
    )

    # Presença do dia
    compare_calendars['Presença'] = compare_calendars['_merge'].map({
        'both': 'Ambos',
        'left_only': 'Só Oferta',
        'right_only': 'Só Operação'
    })

    # Severidade
    def classify_severity(row):
        if row['_merge'] != 'both':
            return 'CRÍTICO'
        if row['Diferenças_periodo'] == 'DIFERENTE':
            return 'CRÍTICO'
        if row['Diferenças_dia_tipo'] == 'DIFERENTE':
            return 'AVISO'
        return 'OK'

    compare_calendars['Severidade'] = compare_calendars.apply(classify_severity, axis=1)

    # Alertas
    for _, row in compare_calendars.iterrows():
        if row['Severidade'] != 'OK':
            alerts_df = add_alert(
                alerts_df,
                "Plano de Operação",
                "Calendário",
                row['Severidade'],
                "Diferenças no calendário em relação ao Plano de Oferta",
                row['date'].strftime('%Y-%m-%d')
            )

    # Formatação final
    compare_calendars['Data'] = compare_calendars['date'].dt.strftime('%Y-%m-%d')
    compare_calendars = compare_calendars[
        [
            'Data',
            'period_POferta',
            'day_type_POferta',
            'period_POperacao',
            'day_type_POperacao',
            'Diferenças_periodo',
            'Diferenças_dia_tipo',
            'Presença',
            'Severidade'
        ]
    ].sort_values('Data')

    return compare_calendars, alerts_df
