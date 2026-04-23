"""
Este módulo valida e compara as sequências de paragens definidas nos planos GTFS.

Funcionalidades principais:
- Junta os ficheiros trips e stop_times para análise detalhada das sequências de paragens.
- Verifica, dentro de cada plano, se todas as viagens associadas ao mesmo pattern_id seguem a mesma ordem de paragens.
- Identifica inconsistências de stop_sequence entre viagens do mesmo percurso.
- Conta e organiza as paragens e respetivas sequências por pattern_id.
- Compara as sequências de paragens entre os planos de Oferta e de Operação.
- Deteta patterns em falta num dos planos e gera alertas específicos para o plano afetado.
- Valida se os patterns comuns entre planos têm sequências de paragens idênticas.
- Regista alertas com nível de gravidade “MUITO GRAVE” sempre que são detetadas inconsistências.

Outputs:
- 1 tabela com o número de paragens e respetivas sequências por pattern_id.
- 1 tabela detalhada com a associação entre pattern_id, stop_id e stop_sequence.
- Atualização da tabela de alertas com todas as inconsistências detetadas, por plano e pattern_id.

"""

import pandas as pd
from analysis.alerts import add_alert

# ==================================================================================================
# 0️⃣ Função auxiliar: extrai sequência única de paragens por pattern
# ==================================================================================================

def get_pattern_sequence(df):
    df = df.copy()

    # Normalizar tipos
    df['stop_sequence'] = pd.to_numeric(df['stop_sequence'], errors='coerce')
    df['stop_id'] = df['stop_id'].astype(str)

    # Remover linhas inválidas
    df = df.dropna(subset=['pattern_id', 'trip_id', 'stop_sequence', 'stop_id'])

    # Ordenar corretamente
    df = df.sort_values(['pattern_id', 'trip_id', 'stop_sequence'])

    # Extrair sequência base ignorando trips duplicadas
    seq = (
        df.groupby(['pattern_id', 'stop_sequence'])['stop_id']
          .first()
          .groupby('pattern_id')
          .apply(list)
          .to_dict()
    )

    return seq


# ==================================================================================================
# 1️⃣ Valida a sequência de paragens dentro de cada plano
# ==================================================================================================

def merge_and_check_stop_sequences(gtfs_trips, gtfs_stop_times, gtfs_name, alerts_df):

    merged_data = gtfs_trips[['trip_id', 'pattern_id']].merge(
        gtfs_stop_times, on='trip_id', how='left'
    )

    merged_data = merged_data.sort_values(by=['pattern_id', 'trip_id', 'stop_sequence'])

    stop_sequence_perpattern = merged_data[['pattern_id', 'stop_id', 'stop_sequence']].drop_duplicates()

    for pattern_id, group in merged_data.groupby('pattern_id'):

        unique_stop_sequences = group.groupby('trip_id')[['stop_sequence', 'stop_id']] \
            .apply(lambda x: tuple(map(tuple, x.values))).unique()

        if len(unique_stop_sequences) > 1:
            alerts_df = add_alert(
                alerts_df,
                gtfs_name,
                "Sequência de paragens",
                "MUITO GRAVE",
                "Múltiplas sequências de paragens para o percurso",
                str(pattern_id)
            )

    stops_count = stop_sequence_perpattern.groupby('pattern_id')[['stop_id','stop_sequence']] \
        .count().reset_index()

    return stops_count, stop_sequence_perpattern, alerts_df


# ==================================================================================================
# 2️⃣ Compara a sequência de paragens entre OFERTA e OPERAÇÃO
# ==================================================================================================

def merge_and_check_stop_sequences_between_plans(
    trips_offer, trips_oper,
    stop_times_offer, stop_times_oper,
    alerts_df
):

    merged_offer = trips_offer[['trip_id', 'pattern_id']].merge(
        stop_times_offer, on='trip_id', how='left'
    )
    merged_oper = trips_oper[['trip_id', 'pattern_id']].merge(
        stop_times_oper, on='trip_id', how='left'
    )

    seq_offer = get_pattern_sequence(merged_offer)
    seq_oper  = get_pattern_sequence(merged_oper)

    patterns_offer = set(seq_offer.keys())
    patterns_oper  = set(seq_oper.keys())

    # Patterns missing
    for pattern in patterns_offer - patterns_oper:
        alerts_df = add_alert(
            alerts_df, "PLANO DE OPERAÇÃO",
            "Sequência de paragens", "MUITO GRAVE",
            f"Pattern {pattern} existe na oferta mas não na operação",
            pattern
        )

    for pattern in patterns_oper - patterns_offer:
        alerts_df = add_alert(
            alerts_df, "PLANO DE OFERTA",
            "Sequência de paragens", "MUITO GRAVE",
            f"Pattern {pattern} existe na operação mas não na oferta",
            pattern
        )

    # Compare sequences
    for pattern in patterns_offer & patterns_oper:
        if seq_offer[pattern] != seq_oper[pattern]:
            alerts_df = add_alert(
                alerts_df, "PLANO DE OPERAÇÃO",
                "Sequência de paragens", "MUITO GRAVE",
                "Sequência de paragens diferente entre planos",
                pattern
            )

    return alerts_df