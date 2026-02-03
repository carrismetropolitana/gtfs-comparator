"""
Este módulo gere a exportação dos resultados de análise e validação GTFS para ficheiros Excel.

Funcionalidades principais:
- Exporta a sequência de paragens por pattern_id, incluindo stop_id e stop_name.
- Gera ficheiros Excel auxiliares para outputs específicos, como total de circulações e VKM.
- Consolida todos os resultados de análise num único ficheiro Excel.
- Cria automaticamente sheets distintas para cada tipo de comparação e análise.
- Verifica a existência e o conteúdo de cada DataFrame antes de o exportar.
- Insere mensagens de aviso nos sheets quando não existem dados disponíveis.
- Organiza os resultados por áreas funcionais (alertas, resumos, comparações e análises).
- Guarda comparações entre planos de Oferta e Operação (calendários, paragens, extensões e rotas).
- Inclui análises de circulações por hora e por data.
- Exporta sequências de paragens separadamente para cada plano.
- Estrutura resumos finais independentes para o Plano de Oferta e para o Plano de Operação.

Outputs:
- 1 ficheiro Excel consolidado com múltiplos sheets de análise e validação.
- Sheets específicos para alertas, resumos globais, comparações entre planos e outputs detalhados.
- Ficheiros Excel auxiliares para outputs adicionais (sequência de paragens, circulações e VKM).
"""

import pandas as pd
import numpy as np

# ========================================================================================================================================================
# 1️⃣ Output extra - Sequência de Paragens
# ========================================================================================================================================================

def export_stop_sequence(df_seq, stops_df, output_path, sheet_name="Sequência Paragens"):
    """
    Exporta um ficheiro Excel com uma tabela com a sequencia de paragens (+ stop_id e stop_name) por pattern_id
    """
    df_export = df_seq.copy()
    df_export = df_export.merge(stops_df[['stop_id', 'stop_name']], on='stop_id', how='left')

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name=sheet_name, index=False)

# ========================================================================================================================================================
# 2️⃣ Output extra - Total de Circulações e Veículos KM
# ========================================================================================================================================================

def export_total_circulacoes_vkm(df, output_excel_path, sheet_name="Total circulações e VKM"):
    """
    Exporta um DataFrame para um ficheiro Excel novo, com o nome do sheet definido.
    """
    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# ========================================================================================================================================================
# 3️⃣ Output principal - Guarda um ficheiro Excel, com todas as comparações
# ========================================================================================================================================================

def save_to_excel(
    excel_file_path: str,
    alerts_df: pd.DataFrame,
    grand_total_df: pd.DataFrame,
    analysis_period_df: pd.DataFrame,
    merged_all: pd.DataFrame,
    compare_calendars: pd.DataFrame = None,
    stops_comparison_result: pd.DataFrame = None,
    extension_comparison_result: pd.DataFrame = None,
    merged_routes: pd.DataFrame = None,
    stop_sequence_oferta: pd.DataFrame = None,
    stop_sequence_operacao: pd.DataFrame = None,
    resumo_oferta_final: pd.DataFrame = None,
    resumo_operacao_final: pd.DataFrame = None,
    pivot_dates_oferta: pd.DataFrame = None,
    pivot_dates_operacao: pd.DataFrame = None,
    circulacoes_por_hora: pd.DataFrame = None
):
    """
    Guarda todos os resultados em diferentes sheets de um ficheiro Excel.
    Verifica se cada DataFrame existe e não está vazio antes de escrever.
    """
    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:

        def safe_to_excel(df, sheet_name):
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                pd.DataFrame(
                    {"Aviso": [f"Nenhum dado disponível para {sheet_name}"]}
                ).to_excel(writer, sheet_name=sheet_name, index=False)

        # -------------------------------------------------------------------------------------------
        # Alertas
        # -------------------------------------------------------------------------------------------
        
        safe_to_excel(alerts_df, 'ALERTAS')

        # -------------------------------------------------------------------------------------------
        # Resumo
        # -------------------------------------------------------------------------------------------

        if grand_total_df is not None and analysis_period_df is not None:
            grand_total_df.to_excel(writer, sheet_name='RESUMO', index=False, startrow=0)
            analysis_period_df.to_excel( writer, sheet_name='RESUMO', index=False, startrow=len(grand_total_df) + 2)
        else:
            safe_to_excel(grand_total_df, 'RESUMO')

        # -------------------------------------------------------------------------------------------
        # Comparação de circulações e VKM
        # -------------------------------------------------------------------------------------------
        
        safe_to_excel(merged_all, 'Comparação circulações e VKM')

        # -------------------------------------------------------------------------------------------
        # Comparações
        # -------------------------------------------------------------------------------------------
        
        safe_to_excel(compare_calendars, 'Comparação calendarios')
        safe_to_excel(stops_comparison_result, 'Comparação paragens')
        safe_to_excel(extension_comparison_result, 'Comparação extensões')
        safe_to_excel(merged_routes, 'Comparação rotas')

        # -------------------------------------------------------------------------------------------
        # Circulações por hora
        # -------------------------------------------------------------------------------------------

        safe_to_excel(circulacoes_por_hora, 'Circulações por hora')

        # -------------------------------------------------------------------------------------------
        # Sequências de paragens
        # -------------------------------------------------------------------------------------------

        safe_to_excel(stop_sequence_oferta, 'Sequencia paragens POferta')
        safe_to_excel(stop_sequence_operacao, 'Sequencia paragens POperação')

        # -------------------------------------------------------------------------------------------
        # Resumos planos
        # -------------------------------------------------------------------------------------------

        safe_to_excel(resumo_oferta_final, 'Resumo Plano Oferta')
        safe_to_excel(resumo_operacao_final, 'Resumo Plano Operação')

        # -------------------------------------------------------------------------------------------
        # Circulações por data
        # -------------------------------------------------------------------------------------------

        safe_to_excel(pivot_dates_oferta, 'Circulações por Data POferta')
        safe_to_excel(pivot_dates_operacao, 'Circulações por Data POperação')

    #print(f"Resultados guardados em {excel_file_path}")