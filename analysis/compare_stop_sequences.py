
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

# ========================================================================================================================================================
# 1️⃣ Valida a sequencia de paragens de cada plano
# ========================================================================================================================================================

def merge_and_check_stop_sequences(gtfs_trips, gtfs_stop_times, gtfs_name, alerts_df):
    """
    Verifica inconsistências de sequência de paragens dentro de um único plano (Oferta ou Operação).
    """
    merged_data = pd.merge(gtfs_trips, gtfs_stop_times, on='trip_id')
    merged_data = merged_data.sort_values(by=['pattern_id', 'trip_id', 'stop_sequence'])

    stop_sequence_perpattern = merged_data[['pattern_id', 'stop_id', 'stop_sequence']].drop_duplicates(keep='first')
    inconsistent_stop_sequences = []

    for pattern_id, group in merged_data.groupby(['pattern_id']):
    
        unique_stop_sequences = group.groupby('trip_id')[['stop_sequence', 'stop_id']] \
            .apply(lambda x: tuple(map(tuple, x.values))).unique()
        if len(unique_stop_sequences) > 1:
            inconsistent_stop_sequences.append((pattern_id, unique_stop_sequences))
            alerts_df = add_alert(
                alerts_df,
                gtfs_name,  # ← usa o plano correto
                "Sequência de paragens",
                'MUITO GRAVE',
                f"Múltiplas sequências de paragens para o percurso",
                f'{pattern_id}'
            )

    stops_count = stop_sequence_perpattern.groupby('pattern_id')[['stop_id','stop_sequence']].count().reset_index()
    return stops_count, stop_sequence_perpattern, alerts_df


# ========================================================================================================================================================
# 2️⃣ Compara a sequênia de paragens entre planos
# ========================================================================================================================================================

def merge_and_check_stop_sequences_between_plans(
    trips_offer, trips_oper,
    stop_times_offer, stop_times_oper,
    alerts_df
):
    """
    Verifica inconsistências de sequência de paragens entre os planos de Oferta e Operação.
    Adiciona alertas indicando corretamente o plano afetado.
    """
    merged_offer = pd.merge(trips_offer, stop_times_offer, on='trip_id')
    merged_oper = pd.merge(trips_oper, stop_times_oper, on='trip_id')
    
    # Obtem os pattern_id de cada plano
    patterns_offer = set(merged_offer['pattern_id'].unique())
    patterns_oper = set(merged_oper['pattern_id'].unique())
    
    # -------------------------------------------------------------------------------------------
    # 📌 Identifica os patterns ausentes no plano de oferta e de operação
    # -------------------------------------------------------------------------------------------

    missing_in_oper = patterns_offer - patterns_oper
    for pattern in missing_in_oper:
        alerts_df = add_alert(
            alerts_df,
            "PLANO DE OPERAÇÃO", 
            'Sequência de paragens',
            'MUITO GRAVE',
            f'Pattern {pattern} presente no plano de oferta mas não no plano de operação',
            pattern
        )

    missing_in_offer = patterns_oper - patterns_offer
    for pattern in missing_in_offer:
        alerts_df = add_alert(
            alerts_df,
            "PLANO DE OFERTA",  
            'Sequência de paragens',
            'MUITO GRAVE',
            f'Pattern {pattern} presente no plano de operação mas não no plano de oferta',
            pattern
        )
    # -------------------------------------------------------------------------------------------
    # 📌 Verifica a sequências de paragens para os patterns em comum
    # -------------------------------------------------------------------------------------------
    
    common_patterns = patterns_offer & patterns_oper
    for pattern in common_patterns:
        seq_offer = merged_offer[merged_offer['pattern_id'] == pattern].sort_values('stop_sequence')['stop_id'].tolist()
        seq_oper = merged_oper[merged_oper['pattern_id'] == pattern].sort_values('stop_sequence')['stop_id'].tolist()
        if seq_offer != seq_oper:
                alerts_df = add_alert(
                alerts_df,
                "PLANO DE OPERAÇÃO",
                'Sequência de paragens',
                'MUITO GRAVE',
                'Sequência de paragens diferentes entre os planos',
                pattern
            )

    return alerts_df