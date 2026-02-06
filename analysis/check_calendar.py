"""
Este módulo valida e compara os calendários GTFS entre o Plano de Oferta e o Plano de Operação.

Funcionalidades principais:
- Verifica a existência de datas com exception_type = 2 no ficheiro calendar_dates dentro de um período definido, gerando alertas.
- Normaliza e separa os calendários por plano (Oferta vs Operação).
- Compara os calendários dos dois planos por data, analisando:
    - Existência do dia em cada plano.
    - Diferenças no período (period).
    - Diferenças no tipo de dia (day_type).
    - Gera alertas automáticos sempre que são encontradas inconsistências face ao Plano de Oferta.

Outputs:
- 1 tabela consolidada com a comparação diária dos calendários entre os dois planos.
- 1 tabela de alertas com a identificação das datas problemáticas e tipo de inconsistência. 

"""

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
    Compara os calendários entre o Plano de Oferta e o Plano de Operação e devolve uma tabela consolidada com as diferenças encontradas.
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
    
    # -------------------------------------------------------------------------------------------
    # Diferenças
    # -------------------------------------------------------------------------------------------

    compare_calendars['Diferenças_periodo'] = np.where(compare_calendars['period_POferta'] == compare_calendars['period_POperacao'], 'IGUAL', 'DIFERENTE')
    compare_calendars['Diferenças_dia_tipo'] = np.where(compare_calendars['day_type_POferta'] == compare_calendars['day_type_POperacao'], 'IGUAL', 'DIFERENTE')

    # -------------------------------------------------------------------------------------------
    # Presença do dia
    # -------------------------------------------------------------------------------------------

    compare_calendars['Presença'] = compare_calendars['_merge'].map({'both': 'Ambos', 'left_only': 'Só Oferta', 'right_only': 'Só Operação'})

    # -------------------------------------------------------------------------------------------
    # Formatação final
    # -------------------------------------------------------------------------------------------

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
            'Presença'
        ]
    ].sort_values('Data')

    return compare_calendars, alerts_df
